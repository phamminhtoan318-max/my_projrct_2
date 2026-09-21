import logging
import re

import pandas as pd
from pandas.api.types import is_numeric_dtype

logger = logging.getLogger(__name__)

NUM_NOISE = re.compile(r"[₹$€%,\s]")


def compute_column_stats(series):
    total = len(series)
    null_count = int(series.isna().sum())
    null_ratio = round(null_count / total, 4) if total > 0 else 0.0
    unique_count = int(series.nunique(dropna=True))

    stats = {
        "dtype": str(series.dtype),
        "total": total,
        "null_count": null_count,
        "null_ratio": null_ratio,
        "unique_count": unique_count,
    }

    if is_numeric_dtype(series):
        valid_nums = series.dropna()
    else:
        cleaned = series.dropna().astype(str).str.replace(NUM_NOISE, "", regex=True)
        valid_nums = pd.to_numeric(cleaned, errors="coerce").dropna()

    if not valid_nums.empty and (is_numeric_dtype(series) or len(valid_nums) / total > 0.5):
        stats["is_numeric"] = True
        stats["min"] = round(float(valid_nums.min()), 2)
        stats["max"] = round(float(valid_nums.max()), 2)
        stats["mean"] = round(float(valid_nums.mean()), 2)
        stats["median"] = round(float(valid_nums.median()), 2)
    else:
        stats["is_numeric"] = False

    return stats


def compute_quality(df):
    if df is None or df.empty:
        return {"total_rows": 0, "total_columns": 0, "columns": {}}

    cols_stats = {}
    for col in df.columns:
        cols_stats[col] = compute_column_stats(df[col])

    return {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": cols_stats,
    }


def log_quality_report(report):
    total_rows = report.get("total_rows", 0)
    total_cols = report.get("total_columns", 0)
    columns = report.get("columns", {})

    logger.info("=" * 60)
    logger.info(f"[quality] BÁO CÁO CHẤT LƯỢNG DỮ LIỆU: {total_rows} dòng, {total_cols} cột")
    logger.info("=" * 60)

    for col, s in columns.items():
        null_pct = f"{s['null_ratio'] * 100:.1f}%"
        msg = f"- {col} [{s['dtype']}]: NULL={s['null_count']} ({null_pct}) | Unique={s['unique_count']}"
        if s.get("is_numeric"):
            msg += f" | min={s['min']}, max={s['max']}, mean={s['mean']}, median={s['median']}"
        logger.info(f"[quality] {msg}")

    logger.info("=" * 60)


def generate_quality_report(df):
    if df is None:
        logger.warning("[quality] DataFrame là None, không thể lập báo cáo chất lượng.")
        return {"total_rows": 0, "total_columns": 0, "columns": {}}

    report = compute_quality(df)
    log_quality_report(report)
    return report
