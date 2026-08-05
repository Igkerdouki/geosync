import os
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'dbname': os.environ.get('DB_NAME', 'geosync'),
    'user': os.environ.get('DB_USER', os.environ.get('USER', 'ioannagkerdouki')),
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
