import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def extract_data(file_path, staging_path=None):
    logger.info(f"Extracting data from {file_path}")

    try:
        df = pd.read_csv(
            file_path, dtype=str, encoding="utf-8-sig", keep_default_na=False
        )
    except FileNotFoundError:
        logger.error(f"File not found at {file_path}")
        return None
    except pd.errors.EmptyDataError:
        logger.error("File is empty")
        return None
    except pd.errors.ParserError as e:
        logger.error(f"Error parsing file: {e}")
        return None
    except UnicodeDecodeError as e:
        logger.error(f"Encoding error (thử encoding='cp1252' hoặc 'utf-16'?): {e}")
        return None
    except Exception:
        logger.exception("Unexpected error while extracting data")
        return None

    if df.empty:
        logger.error("File has a header but no rows")
        return None

    logger.info(f"Extracted {len(df)} rows, {len(df.columns)} columns")

    if staging_path is not None:
        staging_path = Path(staging_path)
        try:
            staging_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(staging_path, index=False) 
        except Exception:
            logger.exception(f"Không ghi được staging: {staging_path}")
            return None
        logger.info(f"Saved staging -> {staging_path}")

    return df