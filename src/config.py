import os
import logging
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

logger = logging.getLogger(__name__)


def get_connection_string():
    driver = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
    server = os.getenv("DB_SERVER", "localhost")
    port = os.getenv("DB_PORT", "").strip()
    database = os.getenv("DB_NAME", "")
    trusted = os.getenv("DB_TRUSTED_CONNECTION", "yes")
    trust_cert = os.getenv("DB_TRUST_SERVER_CERTIFICATE", "yes")

    if port and port != "1433":
        server_target = f"{server},{port}"
    else:
        server_target = server

    params = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server_target};"
        f"DATABASE={database};"
        f"Trusted_Connection={trusted};"
        f"TrustServerCertificate={trust_cert};"
    )
    return "mssql+pyodbc:///?odbc_connect=" + quote_plus(params)


def get_engine():
    conn_str = get_connection_string()
    engine = create_engine(conn_str, fast_executemany=True)
    return engine


def test_connection():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("[config] Kết nối SQL Server thành công.")
        return True
    except Exception:
        logger.exception("[config] Không thể kết nối SQL Server.")
        return False
