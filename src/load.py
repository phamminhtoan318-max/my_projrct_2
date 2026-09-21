import logging

import pandas as pd

from src.config import get_engine

logger = logging.getLogger(__name__)

TABLE_NAME = "amazon_products"


def load_to_sql(df, table=TABLE_NAME, if_exists="replace", chunksize=500):
    if df is None or df.empty:
        logger.warning("[load] DataFrame rỗng hoặc None — bỏ qua bước load.")
        return False

    try:
        engine = get_engine()
        df.to_sql(
            name=table,
            con=engine,
            if_exists=if_exists,
            index=False,
            chunksize=chunksize,
        )
        logger.info(f"[load] Đã ghi {len(df)} dòng vào bảng '{table}' (if_exists='{if_exists}').")
        return True
    except Exception:
        logger.exception(f"[load] Lỗi khi ghi vào SQL Server bảng '{table}'.")
        return False
