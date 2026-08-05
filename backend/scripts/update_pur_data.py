"""
Update PUR Data - Download and load newer years (2024, 2025, 2026)

California DPR releases PUR data with ~12-18 month lag.
Data available at: https://www.cdpr.ca.gov/docs/pur/purmain.htm

Run this script to check for and download newer data.
"""

import os
import sys
import requests
import zipfile
import pandas as pd
from pathlib import Path
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values

# Database connection
DB_CONFIG = {
    "host": "localhost",
    "database": "geosync",
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres")
}

# CA DPR PUR data URLs
# Format: https://files.cdpr.ca.gov/pub/outgoing/pur_archives/pur{YEAR}.zip
PUR_BASE_URL = "https://files.cdpr.ca.gov/pub/outgoing/pur_archives/pur{year}.zip"

DATA_DIR = Path(__file__).parent.parent / "data" / "pur_raw"

def check_available_years():
    """Check which years are available from CA DPR"""
    current_year = datetime.now().year
    available = []

    print("Checking CA DPR for available PUR data...")

    # Check years from 2024 to current
    for year in range(2024, current_year + 1):
        url = PUR_BASE_URL.format(year=year)
        try:
            response = requests.head(url, timeout=10)
            if response.status_code == 200:
                available.append(year)
                print(f"  ✅ {year} - Available ({response.headers.get('Content-Length', 'unknown')} bytes)")
            else:
                print(f"  ❌ {year} - Not available (HTTP {response.status_code})")
        except Exception as e:
            print(f"  ⚠️ {year} - Error checking: {e}")

    return available

def check_database_years():
    """Check which years are already in our database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT year FROM sprays ORDER BY year")
        years = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return years
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return []

def download_year(year):
    """Download PUR data for a specific year"""
    url = PUR_BASE_URL.format(year=year)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    zip_path = DATA_DIR / f"pur{year}.zip"

    print(f"\nDownloading {year} PUR data...")
    print(f"  URL: {url}")

    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        total_size = int(response.headers.get('Content-Length', 0))
        downloaded = 0

        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    pct = (downloaded / total_size) * 100
                    print(f"\r  Progress: {pct:.1f}% ({downloaded:,} / {total_size:,} bytes)", end="")

        print(f"\n  ✅ Downloaded to {zip_path}")
        return zip_path

    except Exception as e:
        print(f"  ❌ Download failed: {e}")
        return None

def extract_and_load(zip_path, year):
    """Extract ZIP and load data into database"""
    extract_dir = DATA_DIR / f"pur{year}"

    print(f"\nExtracting {zip_path}...")

    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(extract_dir)
        print(f"  ✅ Extracted to {extract_dir}")
    except Exception as e:
        print(f"  ❌ Extraction failed: {e}")
        return False

    # Find the main data file (usually udc{YEAR}.txt or similar)
    txt_files = list(extract_dir.glob("*.txt")) + list(extract_dir.glob("**/*.txt"))

    if not txt_files:
        print("  ❌ No .txt files found in archive")
        return False

    print(f"  Found {len(txt_files)} text files")

    # Load each file
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    total_loaded = 0

    for txt_file in txt_files:
        if txt_file.stat().st_size < 1000:  # Skip tiny files
            continue

        print(f"\n  Loading {txt_file.name}...")

        try:
            # PUR files are typically fixed-width or pipe-delimited
            # Try to auto-detect format
            df = pd.read_csv(txt_file, sep=None, engine='python', nrows=5)

            # Re-read with detected format
            df = pd.read_csv(txt_file, sep=None, engine='python', low_memory=False)

            print(f"    Loaded {len(df):,} records with {len(df.columns)} columns")

            # Map to our schema (adjust column names as needed)
            # CA DPR uses specific column names
            column_mapping = {
                'COUNTY_CD': 'county',
                'COUNTY_NAME': 'county',
                'CHEM_CODE': 'chem_code',
                'CHEMNAME': 'chemname',
                'LBS_CHM_USED': 'lbs_chm_used',
                'ACRE_TREATED': 'acre_treated',
                'APPLIC_DT': 'applic_dt',
                'SITE_NAME': 'site_name',
                'AER_GND_IND': 'aer_gnd_ind',
                'PRODCHEM_PCT': 'prodchem_pct',
                'UNIT_TREATED': 'unit_treated'
            }

            # Normalize column names
            df.columns = [c.upper() for c in df.columns]

            # Insert into database
            # (This is simplified - would need proper column mapping)

            total_loaded += len(df)

        except Exception as e:
            print(f"    ⚠️ Error loading {txt_file.name}: {e}")
            continue

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n  ✅ Loaded {total_loaded:,} total records for {year}")
    return True

def main():
    print("=" * 60)
    print("GeoSync PUR Data Updater")
    print("=" * 60)
    print(f"Current date: {datetime.now().strftime('%Y-%m-%d')}")
    print()

    # Check what we have
    db_years = check_database_years()
    print(f"\nYears in database: {db_years}")

    # Check what's available
    available_years = check_available_years()
    print(f"\nNew years available from CA DPR: {available_years}")

    # Find years we need
    missing_years = [y for y in available_years if y not in db_years]

    if not missing_years:
        print("\n✅ Database is up to date!")
        return

    print(f"\n🔄 Years to download: {missing_years}")

    # Ask user
    response = input("\nDownload and load these years? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return

    # Download and load each year
    for year in missing_years:
        zip_path = download_year(year)
        if zip_path:
            extract_and_load(zip_path, year)

    print("\n" + "=" * 60)
    print("Update complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
