
import logging
import re
import unicodedata
from pathlib import Path

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype

logger = logging.getLogger(__name__)


STAGING_PATH = Path("data/staging/amazon_raw.parquet")

KEY_COL = "product_id"

INVALID_TOKENS = {"", "none", "null", "nan", "n/a", "na", "unknown", "undefined", "?"}

ID_SUFFIXES = ("_id", "_code", "_key")

DEFAULT_VALUES = {
    "product_name": "Unknown Product",
    "category": "Uncategorized",
    "user_name": "Anonymous",
}


_INVISIBLE = re.compile(r"[\u200b\u200c\u200d\ufeff]")
_NUM_NOISE = re.compile(r"[₹$€%,\s]")


def load_staging(path=STAGING_PATH):

    path = Path(path)
    try:
        df = pd.read_parquet(path)
    except FileNotFoundError:
        logger.error(f"Không thấy file staging: {path}")
        return None
    except (ImportError, OSError, ValueError):
        logger.exception(f"Không đọc được parquet: {path} (đã cài pyarrow chưa?)")
        return None
    logger.info(f"Đọc staging: {len(df)} dòng, {len(df.columns)} cột")
    return df


def is_invalid(val):
    if isinstance(val, str):
        return val.strip().lower() in INVALID_TOKENS
    return val is None or pd.isna(val)


def clean_text_data(data_text, default=None):

    if is_invalid(data_text):
        return default
    text = str(data_text)
    if not text.isascii():
        text = unicodedata.normalize("NFC", text)
        text = _INVISIBLE.sub("", text)
    return " ".join(text.split()) or default


def clean_id(data_id):
 
    if is_invalid(data_id):
        return None
    return str(data_id).strip().upper()


def clean_id_list(cell, sep=","):
    if is_invalid(cell):
        return []
    return [clean_id(x) for x in str(cell).split(sep)]


def join_ids(ids, sep=","):
    if not ids:
        return None
    return sep.join(i or "" for i in ids)


def detect_id_columns(df, suffixes=ID_SUFFIXES):
    return [c for c in df.columns if str(c).lower().endswith(suffixes)]


def is_list_column(series, sep=",", threshold=0.5):

    s = series.dropna().astype(str)
    return len(s) > 0 and s.str.contains(sep, regex=False).mean() > threshold


def is_numeric_like(series, threshold=0.9):

    s = series.dropna().astype(str).str.replace(_NUM_NOISE, "", regex=True)
    return len(s) > 0 and pd.to_numeric(s, errors="coerce").notna().mean() >= threshold


def clean_string_columns(df, exclude=()):

    df = df.copy()
    skip = set(detect_id_columns(df)) | set(exclude)
    for col in df.columns:
        if col in skip or is_numeric_dtype(df[col]) or is_datetime64_any_dtype(df[col]):
            continue
        df[col] = df[col].map(clean_text_data)
    return df


def clean_code_columns(df, sep=","):

    df = df.copy()
    for col in detect_id_columns(df):
        if is_list_column(df[col], sep):
            logger.info(f"[id] {col}: cột danh sách id")
            df[col] = df[col].map(lambda c: join_ids(clean_id_list(c, sep), sep))
        else:
            df[col] = df[col].map(clean_id)
    return df


def handle_missing(df, key_cols=None, max_missing_ratio=0.5):

    before = len(df)
    df = df.copy()
    id_cols = detect_id_columns(df)
    if key_cols is None:
        key_cols = [c for c in id_cols if not is_list_column(df[c])]

    if key_cols:
        m = df[key_cols].isna().any(axis=1)
        if m.any():
            logger.warning(f"[missing] bỏ {int(m.sum())} dòng thiếu khóa {key_cols}")
            df = df[~m]

    m = df.isna().mean(axis=1) > max_missing_ratio
    if m.any():
        logger.warning(f"[missing] bỏ {int(m.sum())} dòng thiếu > {max_missing_ratio:.0%} số cột")
        df = df[~m]

    left = df.isna().sum()
    left = left[left > 0]
    if len(left):
        logger.info(f"[missing] ô còn thiếu (giữ NULL): {left.to_dict()}")
    logger.info(f"[missing] {before} -> {len(df)} dòng")
    return df.reset_index(drop=True)


def fill_defaults(df, defaults=None, fallback=None):

    defaults = DEFAULT_VALUES if defaults is None else defaults
    df = df.copy()
    id_cols = set(detect_id_columns(df))
    for col in df.columns:
        if col in defaults:
            value = defaults[col]
        elif fallback is not None and not (
            col in id_cols or is_numeric_dtype(df[col]) or is_numeric_like(df[col])
        ):
            value = fallback
        else:
            continue
        n = int(df[col].isna().sum())
        if n:
            logger.info(f"[default] {col}: điền {n} ô thiếu = {value!r}")
            df[col] = df[col].fillna(value)
    return df


def impute_numeric_columns(df, strategy="median", exclude=()):

    if strategy not in ("mean", "median"):
        raise ValueError(f"strategy phải là 'mean' hoặc 'median', nhận được: {strategy!r}")
    df = df.copy()
    skip = set(exclude)
    for col in df.columns:
        if col in skip or not is_numeric_dtype(df[col]):
            continue
        n = int(df[col].isna().sum())
        if n == 0:
            continue
        fill_val = getattr(df[col], strategy)()
        logger.info(f"[impute] {col}: điền {n} ô NaN bằng {strategy} = {fill_val:.4g}")
        df[col] = df[col].fillna(fill_val)
    return df


def remove_duplicates(df, key=KEY_COL, prefer_col="rating_count"):

    before = len(df)

    df = df.drop_duplicates()

    if df[key].isna().any():
        logger.warning(f"[dup] bỏ {int(df[key].isna().sum())} dòng thiếu {key}")
        df = df[df[key].notna()]

    if prefer_col in df.columns:
        rank = pd.to_numeric(df[prefer_col].str.replace(_NUM_NOISE, "", regex=True), errors="coerce")
        df = df.assign(_rank=rank).sort_values("_rank", ascending=False, na_position="last", kind="stable")
        df = df.drop_duplicates(subset=key, keep="first").drop(columns="_rank")
    else:
        df = df.drop_duplicates(subset=key, keep="first")

    df = df.sort_index().reset_index(drop=True)
    logger.info(f"[dup] {before} -> {len(df)} dòng (bỏ {before - len(df)})")
    return df


def transform_data(df, staging_path=None):

    try:
        df = clean_string_columns(df)       # bước 1: chuẩn hóa văn bản (xóa ký tự đặc biệt, khoảng trắng thừa, chuẩn hóa Unicode...)
        df = clean_code_columns(df)         # bước 2: chuẩn hóa ID/mã (chuẩn hóa các cột ID: loại bỏ khoảng trắng, chuyển sang chữ hoa, xử lý danh sách ID...)
        df = remove_duplicates(df)          # bước 3: xóa trùng (trước khi xử lý NULL) (xóa các dòng có cùng ID chính, giữ lại dòng có rating_count cao hơn)
        df = handle_missing(df)             # bước 4: xóa dòng NULL quan trọng + hàng >50% (xóa dòng có ID chính bị thiếu, hoặc có trên 50% giá trị là NULL)
        df = fill_defaults(df)              # bước 5: điền mặc định cho cột văn bản (điền giá trị mặc định cho một số cột văn bản như product_name, category, user_name)
        df = impute_numeric_columns(df)     # bước 6: điền trung vị/trung bình cho cột số (điền giá trị trung vị/trung bình cho các cột số bị thiếu)
    except Exception:
        logger.exception("Lỗi ở bước transform")
        return None 

    if staging_path is not None:
        staging_path = Path(staging_path)
        staging_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(staging_path, index=False)
        logger.info(f"Đã lưu staging: {staging_path} ({len(df)} dòng)")

    return df