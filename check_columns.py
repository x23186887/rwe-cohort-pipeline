# check_columns.py
import pandas as pd
from sqlalchemy import create_engine, text
import sys
sys.path.insert(0, r"D:\projects\healthcare\rwe")
from config import CONNECTION_STRING

engine = create_engine(CONNECTION_STRING)

with engine.connect() as conn:
    # Check actual column names in conditions table
    cols = pd.read_sql(
        """SELECT column_name FROM information_schema.columns
           WHERE table_schema = 'bronze'
           AND table_name = 'raw_conditions'
           ORDER BY ordinal_position""", conn
    )
    print("Columns in raw_conditions:")
    print(cols.to_string(index=False))

    # Also peek at first 3 rows
    sample = pd.read_sql(
        "SELECT * FROM bronze.raw_conditions LIMIT 3", conn
    )
    print("\nSample rows:")
    print(sample.to_string())