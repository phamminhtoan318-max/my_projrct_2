import logging

import pandas as pd
from pandas.api.types import is_numeric_dtype

from src.transform import is_numeric_like

logger = logging.getLogger(__name__)


REQUIRED_COLUMNS = [
    "product_id",
    "product_name",
    "category",
    "discounted_price",
    "actual_price",
    "discount_percentage",
    "rating",
    "rating_count",
    "user_id",
    "review_id",
]

NUMERIC_COLUMNS = ["rating", "rating_count", "discounted_price", "actual_price", "discount_percentage"]

RATING_RANGE = (0.0, 5.0)


def _result(passed, rule, message):
    level = logging.INFO if passed else logging.WARNING
    status = "PASS" if passed else "FAIL"
    logger.log(level, f"[validate] {status} | {rule}: {message}")
    return {"passed": passed, "rule": rule, "message": message}


def check_required_columns(df, required=REQUIRED_COLUMNS):
    missing = [c for c in required if c not in df.columns]
    if missing:
        return _result(False, "required_columns", f"Thiếu {len(missing)} cột: {missing}")
    return _result(True, "required_columns", f"Đủ {len(required)} cột bắt buộc.")


def check_no_duplicate_ids(df, key="product_id"):
    if key not in df.columns:
        return _result(False, "no_duplicate_ids", f"Cột '{key}' không tồn tại.")
    dupes = int(df[key].dropna().duplicated().sum())
    if dupes:
        return _result(False, "no_duplicate_ids", f"Có {dupes} ID trùng trong cột '{key}'.")
    return _result(True, "no_duplicate_ids", f"Không có ID trùng trong '{key}'.")


def check_no_null_in_key(df, key="product_id"):
    if key not in df.columns:
        return _result(False, "no_null_in_key", f"Cột '{key}' không tồn tại.")
    n_null = int(df[key].isna().sum())
    if n_null:
        return _result(False, "no_null_in_key", f"Cột '{key}' có {n_null} ô NULL.")
    return _result(True, "no_null_in_key", f"Cột '{key}' không có NULL.")


def check_null_ratio(df, max_ratio=0.3):
    ratio = df.isna().mean()
    bad = ratio[ratio > max_ratio]
    if len(bad):
        detail = {col: f"{v:.1%}" for col, v in bad.items()}
        return _result(False, "null_ratio", f"Cột NULL > {max_ratio:.0%}: {detail}")
    return _result(True, "null_ratio", f"Tất cả cột NULL ≤ {max_ratio:.0%}.")


def check_rating_range(df, col="rating", range_=RATING_RANGE):
    if col not in df.columns:
        return _result(False, "rating_range", f"Cột '{col}' không tồn tại.")
    numeric = pd.to_numeric(df[col], errors="coerce").dropna()
    lo, hi = range_
    bad = int(((numeric < lo) | (numeric > hi)).sum())
    if bad:
        return _result(False, "rating_range", f"{bad} giá trị '{col}' ngoài [{lo}, {hi}].")
    return _result(True, "rating_range", f"Tất cả '{col}' hợp lệ trong [{lo}, {hi}].")


def check_min_rows(df, min_rows=100):
    if len(df) >= min_rows:
        return _result(True, "min_rows", f"{len(df)} dòng >= {min_rows} tối thiểu.")
    return _result(False, "min_rows", f"Chỉ có {len(df)} dòng, cần tối thiểu {min_rows}.")


def check_numeric_columns(df, cols=NUMERIC_COLUMNS):
    bad_cols = []
    for col in cols:
        if col not in df.columns:
            continue
        if is_numeric_dtype(df[col]) or is_numeric_like(df[col]):
            continue
        ratio = pd.to_numeric(df[col], errors="coerce").notna().mean()
        bad_cols.append(f"{col}({ratio:.0%})")
    if bad_cols:
        return _result(False, "numeric_columns", f"Cột số không hợp lệ: {bad_cols}")
    return _result(True, "numeric_columns", f"Tất cả {len(cols)} cột số hợp lệ.")


def validate(df, min_rows=100):
    if df is None:
        r = _result(False, "dataframe_not_none", "DataFrame là None — pipeline thất bại trước bước validate.")
        return {"passed": False, "results": [r]}

    results = [
        check_required_columns(df),
        check_min_rows(df, min_rows),
        check_no_null_in_key(df),
        check_no_duplicate_ids(df),
        check_null_ratio(df),
        check_rating_range(df),
        check_numeric_columns(df),
    ]

    passed = all(r["passed"] for r in results)
    total = len(results)
    failed = [r for r in results if not r["passed"]]

    if not failed:
        logger.info(f"[validate] Validate OK — {total}/{total} quy tắc passed.")
    else:
        lines = [f"Validate FAILED — {len(failed)}/{total} quy tắc thất bại:"]
        for r in failed:
            lines.append(f"  ✗ {r['rule']}: {r['message']}")
        logger.info(f"[validate] {chr(10).join(lines)}")

    return {"passed": passed, "results": results}
