import psycopg2
from dotenv import load_dotenv
import os
import collections
"""
Create the frequent query table and verify it exists
"""

# Load environment variables from .env
load_dotenv()
 
# Fetch variables
DATABASE_URL = os.getenv("DATABASE_URL")
 
try:
    conn = psycopg2.connect(DATABASE_URL)
    print("Connected!")
    cursor= conn.cursor()

    # add new table for frequent_retrieval
    table_query ="""
           CREATE TABLE IF NOT EXISTS frequent_queries (
            id                      uuid primary key default gen_random_uuid(),
            canonical_query         text unique not null,  -- e.g. "ibuprofen: drug interactions"
            llm_response            text not null,         -- cached markdown response
            hit_count               int default 1,
            last_asked_at           timestamptz default now(),
            response_invalidated_at timestamptz,           -- set when source drug data changes
            drug_names              text[],                -- e.g. ["ibuprofen", "warfarin"]
            intent_category         text,                  -- e.g. "drug interactions"
            created_at              timestamptz default now()
            );
    """
    cursor.execute(table_query)  
    print("table created!")
 
    # sql_query = """
    # SELECT table_name, column_name, data_type 
    # FROM information_schema.columns 
    # WHERE table_schema NOT IN ('information_schema', 'performance_schema', 'sys')
    # ORDER BY table_name, ordinal_position;
    # """
    # cursor.execute(sql_query)
    # rows = cursor.fetchall()

    # # Group columns by table using a dictionary
    # schema_dict = collections.defaultdict(list)
    # for table, column,data_type in rows:
    #     schema_dict[table].append(f"{column} ({data_type})")

     
    # for table, columns in schema_dict.items():
    #     if "herb" in table or "food" in table or "drug" in table or "interact" in table or "frequent" in table:
    #         print(f"Table: {table}")
    #         print(f"  Columns: {'\n '.join(columns)}\n")
    cursor.execute("SELECT * FROM frequent_queries;")
    print(cursor.fetchone())
    conn.commit()
    print("table committed!")
    conn.close()
    

except Exception as e:
    print(f"Connection failed: {e}")
 