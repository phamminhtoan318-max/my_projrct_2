import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent 
DEFAULT_LOG_DIR = BASE_DIR / "data" / "logs"


def setup_logging(log_dir = DEFAULT_LOG_DIR, level = "INFO"):
    log_dir.mkdir(parents=True, exist_ok=True) 

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    #Thiết lập ghi vào file etl_process.log
    file_handler = RotatingFileHandler(
        log_dir / "etl_process.log",
        maxBytes=1_000_000,   
        backupCount=3,        
        encoding="utf-8",
    )
    console_handler = logging.StreamHandler(sys.stdout) #Giúp in đồng thời các dòng log trực tiếp lên màn hình console khi bạn chạy code.

    for handler in (file_handler, console_handler):
        handler.setFormatter(formatter)

    root = logging.getLogger() #trả về đối tượng logger chính
    root.setLevel(level) # Thiết lập ngưỡng mức log tối thiểu
    root.handlers.clear() # Xóa mọi handler đã được cấu hình trước đó trên root logger. Điều này ngăn chặn tình trạng log bị lặp lại nhiều lần nếu hàm setup_logging bị gọi nhiều lần
    root.addHandler(file_handler)  # Đính kèm file_handler vào root logger để ghi log ra file
    root.addHandler(console_handler) # Đính kèm console_handler vào root logger để in log ra console