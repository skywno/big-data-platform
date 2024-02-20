# !/usr/local/bin/python

import psycopg
import pandas as pd

def get_column_and_type(df):    
    
    dtypedict = {}
    for i,j in zip(df.columns, df.dtypes):
        if "object" in str(j):
            dtypedict.update({i: "TEXT"})
                                 
        if "datetime" in str(j):
            dtypedict.update({i: "TIMESTAMP"})

        if "float" in str(j):
            dtypedict.update({i: "FLOAT"})

        if "int" in str(j):
            dtypedict.update({i: "INTEGER"})
        
    return dtypedict


def create_table_statement(table_name, columns):
    sql = f"CREATE TABLE {table_name} ("

    for column_name, data_type in columns.items():
        sql += f"{column_name} {data_type}, "
    
    sql = sql.rstrip(', ')
    sql += ');'

    return sql

def create_table(table_name: str, df: pd.DataFrame, conn: psycopg.Connection):
    try:
        columns = get_column_and_type(df)
        with conn.cursor() as cur:
            cur.execute(create_table_statement(table_name, columns))
        conn.commit()
        return {"success": True}
        return True
    except Exception as e:
        print(str(e))
        return {"success": False, "error": e}
