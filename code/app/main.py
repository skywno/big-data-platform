from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from typing import Annotated
from .roach import create_table

import psycopg
import pandas as pd
import geopandas as gpd
import os
import gzip
import io
import json
import time

try: 
    conn = psycopg.connect("postgresql://root@roach1:26257/defaultdb", application_name="$ docs_simplecrud_psycopg3")
except:
    time.sleep(60)
    conn = psycopg.connect("postgresql://root@roach1:26257/defaultdb", application_name="$ docs_simplecrud_psycopg3")

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(f'{UPLOAD_DIR}/csv', exist_ok=True)
os.makedirs(f'{UPLOAD_DIR}/geojson', exist_ok=True)

@app.post("/uploadfile/{tenant_id}/{table_name}")
async def create_file(tenant_id, table_name, file: UploadFile = File(...)):
    # table name is defined using tenant_id and table_name
    table_name=f'{table_name}_{tenant_id}'
    # Validate file type
    valid_extensions = ['.csv', '.csv.gz', '.geojson']
    if not any(file.filename.endswith(ext) for ext in valid_extensions):
        raise HTTPException(status_code=400, detail="Supported file formats are CSV, CSV compressed in gzip format (csv.gz), and GeoJSON")
    
    # Save the file with its table name to the 'uploads' directory
    if file.filename.endswith('.csv.gz'):
        # Decompress the file if it is in gzip format
        contents = await file.read()
        # Decompress the gzip file contents
        with gzip.open(io.BytesIO(contents), 'rt') as f:
            # Read the CSV data using pandas
            df = pd.read_csv(f)        
            # Create a table. If table already exists, then raise an exception.
            result = create_table(table_name, df, conn)
            if not result['success']:
               raise HTTPException(status_code=400, detail=f"{result['error']}")
            
            df['tenant_id'] = [tenant_id] * len(df)
            file_path = os.path.join(UPLOAD_DIR, 'csv', table_name + '.csv')
            df.to_csv(file_path, sep=',', index=False, encoding='utf-8')
    elif file.filename.endswith('.csv'):
        # Read CSV file directly
        contents = await file.read()
        # convert bytes to string
        contents = contents.decode(encoding='utf-8')
        # Create a table. If table already exists, then raise an exception.
        df = pd.read_csv(contents)
        success = create_table(table_name, df, conn)
        if not success:
            raise HTTPException(status_code=400, detail="Table already exists with the given name")
        df['tenant_id'] = [tenant_id] * len(df)
        file_path = os.path.join(UPLOAD_DIR, 'csv', table_name + '.csv')
        df.to_csv(file_path, sep=',', index=False, encoding='utf-8')

    elif file.filename.endswith('.geojson'):
        # Read GeoJSON file using GeoPandas
        contents = await file.read()
        # Convert bytes to string
        contents_str = contents.decode("utf-8")
        # Parse the GeoJSON data
        geojson_data = json.loads(contents_str)        
        geojson_data['tenant_id'] = tenant_id
        geojson_string = json.dumps(geojson_data, indent=2)
        file_path = os.path.join(UPLOAD_DIR, 'geojson', table_name + '.geojson')
        with open(file_path, "w") as f:
            f.write(geojson_string)

