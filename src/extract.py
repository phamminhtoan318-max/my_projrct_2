import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def extract_data(file_path):
    logger.info(f"Extracting data from {file_path}") 

    try:
        df = pd.read_csv(file_path, dtype=str, encoding="utf-8-sig")
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
        logger.error(f"Encoding error (thử encoding='latin-1'?): {e}")
        return None
    except Exception:
        logger.exception("Unexpected error while extracting data")
        return None

    if df.empty:
        logger.error("File has a header but no rows")
        return None

    logger.info(f"Extracted {len(df)} rows, {len(df.columns)} columns")
    return df