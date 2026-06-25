#!/usr/bin/env python3
"""
Load PUR (Pesticide Use Reports) data into PostgreSQL
"""

import os
import csv
import psycopg2
from datetime import datetime

# Database connection
DB_CONFIG = {
    'dbname': 'geosync',
    'user': os.environ.get('USER', 'ioannagkerdouki'),
    'host': 'localhost'
}

# PUR data directory
PUR_DATA_DIR = '/Users/ioannagkerdouki/Desktop/geosync_data/pur2023/pur2023/pur_data'

def parse_date(date_str):
    """Parse PUR date format (e.g., '01-FEB-2023')"""
    if not date_str or date_str.strip() == '':
        return None
    try:
        return datetime.strptime(date_str.strip(), '%d-%b-%Y').date()
    except ValueError:
        return None

def parse_decimal(value):
    """Parse decimal value, return None if empty"""
    if not value or value.strip() == '':
        return None
    try:
        return float(value.strip())
    except ValueError:
        return None

def parse_int(value):
    """Parse integer value, return None if empty"""
    if not value or value.strip() == '':
        return None
    try:
        return int(float(value.strip()))
    except ValueError:
        return None

def load_file(cursor, filepath):
    """Load a single PUR data file"""
    filename = os.path.basename(filepath)
    print(f"Loading {filename}...")

    row_count = 0
    error_count = 0

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                cursor.execute("""
                    INSERT INTO sprays (
                        year, use_no, prodno, product_name, chem_code, chemname,
                        prodchem_pct, lbs_chm_used, lbs_prd_used, amt_prd_used,
                        unit_of_meas, acre_treated, applic_cnt, applic_dt,
                        applic_time, county_cd, county, township, range, section,
                        site_code, site_name, aer_gnd_ind, comtrs
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s
                    )
                """, (
                    parse_int(row.get('year')),
                    parse_int(row.get('use_no')),
                    parse_int(row.get('prodno')),
                    row.get('product_name', '')[:255],
                    parse_int(row.get('chem_code')),
                    row.get('chemname', '')[:255],
                    parse_decimal(row.get('prodchem_pct')),
                    parse_decimal(row.get('lbs_chm_used')),
                    parse_decimal(row.get('lbs_prd_used')),
                    parse_decimal(row.get('amt_prd_used')),
                    row.get('unit_of_meas', '')[:10],
                    parse_decimal(row.get('acre_treated')),
                    parse_int(row.get('applic_cnt')),
                    parse_date(row.get('applic_dt')),
                    row.get('applic_time', '')[:10],
                    row.get('county_cd', '')[:5],
                    row.get('county', '')[:50],
                    row.get('township', '')[:10],
                    row.get('range', '')[:10],
                    row.get('section', '')[:10],
                    parse_int(row.get('site_code')),
                    row.get('site_name', '')[:100],
                    row.get('aer_gnd_ind', '')[:5],
                    row.get('comtrs', '')[:20]
                ))
                row_count += 1

                if row_count % 10000 == 0:
                    print(f"  Loaded {row_count} rows...")

            except Exception as e:
                error_count += 1
                if error_count <= 5:
                    print(f"  Error on row: {e}")

    return row_count, error_count

def main():
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    total_rows = 0
    total_errors = 0

    # Find all .txt files in PUR data directory
    files = sorted([f for f in os.listdir(PUR_DATA_DIR) if f.endswith('.txt')])
    print(f"Found {len(files)} data files")

    for filename in files:
        filepath = os.path.join(PUR_DATA_DIR, filename)
        rows, errors = load_file(cursor, filepath)
        total_rows += rows
        total_errors += errors
        conn.commit()
        print(f"  Committed {rows} rows from {filename}")

    cursor.close()
    conn.close()

    print(f"\nDone! Loaded {total_rows} total rows with {total_errors} errors")

if __name__ == '__main__':
    main()
