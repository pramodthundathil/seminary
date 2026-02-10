
import os
import django
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')
django.setup()


print("--- Columns in 'subjects' table ---")
with connection.cursor() as cursor:
    cursor.execute("PRAGMA table_info(subjects)") # For SQLite
    # If MySQL: cursor.execute("DESCRIBE subjects")
    # I'll try generic valid SQL if possible or try/except
    try:
        cursor.execute("SHOW COLUMNS FROM subjects")
        columns = [col[0] for col in cursor.fetchall()]
        print(columns)
    except Exception:
        print("SHOW COLUMNS failed, trying PRAGMA (SQLite)...")
        try:
            cursor.execute("PRAGMA table_info(subjects)")
            columns = [col[1] for col in cursor.fetchall()]
            print(columns)
        except Exception as e:
            print(f"Failed to get columns: {e}")

