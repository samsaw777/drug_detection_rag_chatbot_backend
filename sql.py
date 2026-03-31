import psycopg2 # type: ignore
from dotenv import load_dotenv
import os
import collections

from config.settings import get_settings

Settings = get_settings()

try:
    conn = psycopg2.connect(Settings.MAIN_DATABASE_URL)
    cursor = conn.cursor()

    if cursor:
        print("Connected!")
    
    sql_querry = """
    select * from drug_info
    """

    cursor.execute(sql_querry)
    rows = cursor.fetchall()

    print(rows)
    print("Hello!")
except Exception as e:
    print("Ther is some issue with the settings!")