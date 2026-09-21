import sys
import logging
from pathlib import Path

from src.logger import setup_logging
from src.extract import extract_data
from src.transform import transform_data
from src.validate import validate
from src.quality import generate_quality_report
from src.load import load_to_sql

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
    
    df = transform_data(df, STAGING_PATH)
    if df is None:
        logger.error("Pipeline thất bại ở bước làm sạch dữ liệu!")
        return 1

    report = validate(df)
    if not report["passed"]:
        logger.error("Pipeline thất bại ở bước kiểm tra dữ liệu!")
        return 1

    generate_quality_report(df)

    ok = load_to_sql(df)
    if not ok:
        logger.error("Pipeline thất bại ở bước ghi vào SQL Server!")
        return 1

    logger.info("END PIPELINE")
    return 0

if __name__ == "__main__":
    setup_logging()        
    sys.exit(main())
