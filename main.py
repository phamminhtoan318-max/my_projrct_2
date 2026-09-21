import sys
import logging
from pathlib import Path

from src.logger import setup_logging
from src.extract import extract_data

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

RAW_DATA_PATH = DATA_DIR / "raw" / "amazon.csv"
STAGING_PATH = DATA_DIR / "staging" / "amazon.parquet"
PROCESSED_PATH = DATA_DIR / "processed" / "amazon_clean.csv"
LOG_DIR = DATA_DIR / "logs"

def main():
    logger.info("START PIPELINE")
    
    df = extract_data(RAW_DATA_PATH, staging_path=STAGING_PATH)
    if df is None:
        logger.error("Pipeline thất bại ở bước trích xuất dữ liệu!")
        return 1

    
    logger.info("END PIPELINE")
    return 0

if __name__ == "__main__":
    setup_logging()        
    sys.exit(main())
