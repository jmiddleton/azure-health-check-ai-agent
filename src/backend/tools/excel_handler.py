import os
import pandas as pd
import logging

from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

base_dir = Path.cwd() / "config"

# ---------------- Excel Handler ----------------
class ExcelReaderWriter:
    def __init__(self, excel_file: str):
        self.excel_file = base_dir / Path(excel_file).name
        self.current_month = datetime.now().strftime("%b %Y")
        self.today_str = datetime.now().strftime("%Y-%m-%d 00:00:00")

    def read_sheet(self):
        if self.excel_file.suffix in ('.xlsx', '.xls'):
            logger.info(f"Reading Excel file: {self.excel_file}")
            df = pd.read_excel(self.excel_file, sheet_name="main")
        elif self.excel_file.suffix == '.csv':
            logger.info(f"Reading CSV file: {self.excel_file}")
            df = pd.read_csv(self.excel_file)

        return df

