#!/usr/bin/env python3
"""
Load all PUR data (2014-2023) into PostgreSQL
Handles different file formats between years
"""

import os
import csv
import psycopg2
from datetime import datetime

DB_CONFIG = {
    'dbname': 'geosync',
    'user': os.environ.get('USER', 'ioannagkerdouki'),
    'host': 'localhost'
}

BASE_DIR = '/Users/ioannagkerdouki/Desktop/geosync_data'

def parse_date(date_str):
    if not date_str or date_str.strip() == '':
        return None
    date_str = date_str.strip()
    # Try different date formats
    formats = ['%d-%b-%Y', '%m/%d/%Y', '%Y-%m-%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None

def parse_decimal(value):
    if not value or value.strip() == '':
        return None
    try:
        return float(value.strip())
    except ValueError:
        return None

def parse_int(value):
    if not value or value.strip() == '':
        return None
    try:
        return int(float(value.strip()))
    except ValueError:
        return None

def find_pur_data_dir(year):
    """Find the pur_data directory for a given year"""
    base = os.path.join(BASE_DIR, f'pur{year}')
    possible_paths = [
        os.path.join(base, f'pur{year}', 'pur_data'),  # 2023 structure
        os.path.join(base, 'pur_data'),
        os.path.join(base, 'ftp_files'),  # 2020-2022 structure
        base,  # 2014-2019 structure (files directly in folder)
        os.path.join(base, f'PUR{year}', 'pur_data'),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            # Verify there are udc*.txt files
            if any(f.startswith('udc') and f.endswith('.txt') for f in os.listdir(path)):
                return path
    return None

def is_2023_format(filepath):
    """Check if file uses 2023 format (has 'year' and 'chemname' columns)"""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        header = f.readline().lower()
        return 'chemname' in header and 'year' in header

def load_file_2023_format(cursor, filepath):
    """Load file with 2023 format (includes year, chemname, county name)"""
    row_count = 0
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
            except Exception as e:
                pass
    return row_count

def load_file_old_format(cursor, filepath, year):
    """Load file with old format (2014-2022, uses codes, no year column)"""
    row_count = 0
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                cursor.execute("""
                    INSERT INTO sprays (
                        year, use_no, prodno, chem_code,
                        prodchem_pct, lbs_chm_used, lbs_prd_used, amt_prd_used,
                        unit_of_meas, acre_treated, applic_cnt, applic_dt,
                        applic_time, county_cd, township, range, section,
                        site_code, aer_gnd_ind, comtrs
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s
                    )
                """, (
                    year,  # year from filename
                    parse_int(row.get('use_no')),
                    parse_int(row.get('prodno')),
                    parse_int(row.get('chem_code')),
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
                    row.get('township', '')[:10],
                    row.get('range', '')[:10],
                    row.get('section', '')[:10],
                    parse_int(row.get('site_code')),
                    row.get('aer_gnd_ind', '')[:5],
                    row.get('comtrs', '')[:20]
                ))
                row_count += 1
            except Exception as e:
                pass
    return row_count

def load_year(conn, year):
    cursor = conn.cursor()

    # Check if year already loaded
    cursor.execute("SELECT COUNT(*) FROM sprays WHERE year = %s", (year,))
    existing = cursor.fetchone()[0]
    if existing > 0:
        print(f"Year {year} already has {existing} rows, skipping...")
        return 0

    pur_dir = find_pur_data_dir(year)
    if not pur_dir:
        print(f"Could not find PUR data directory for {year}")
        return 0

    print(f"\nLoading {year} from {pur_dir}...")

    # Only load udc*.txt files
    files = sorted([f for f in os.listdir(pur_dir) if f.startswith('udc') and f.endswith('.txt')])
    total_rows = 0

    for filename in files:
        filepath = os.path.join(pur_dir, filename)

        # Detect format and use appropriate loader
        if is_2023_format(filepath):
            rows = load_file_2023_format(cursor, filepath)
        else:
            rows = load_file_old_format(cursor, filepath, year)

        total_rows += rows
        if rows > 0:
            print(f"  {filename}: {rows} rows")

    conn.commit()
    print(f"Year {year}: {total_rows} total rows committed")
    return total_rows

def main():
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)

    grand_total = 0
    for year in range(2014, 2024):
        rows = load_year(conn, year)
        grand_total += rows

    # Final count
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sprays")
    total = cursor.fetchone()[0]

    conn.close()

    print(f"\n=== DONE ===")
    print(f"New rows loaded this run: {grand_total}")
    print(f"Total rows in database: {total}")

if __name__ == '__main__':
    main()
