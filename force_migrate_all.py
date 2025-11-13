"""
Check what data exists in MySQL database
This helps diagnose why tables aren't migrating

Usage: python check_mysql_data.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')
django.setup()

from django.apps import apps
from django.db import connections

def check_table_counts():
    """Check record counts in all tables in MySQL"""
    
    print("="*70)
    print("MySQL Database Analysis")
    print("="*70)
    
    app_label = 'home'  # <<<< CHANGE THIS
    
    models = list(apps.get_app_config(app_label).get_models())
    
    print(f"\nChecking {len(models)} tables in MySQL...\n")
    
    mysql_cursor = connections['default'].cursor()
    
    tables_with_data = []
    tables_empty = []
    
    for model in models:
        model_name = model.__name__
        table_name = model._meta.db_table
        
        try:
            # Check MySQL count
            mysql_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            mysql_count = mysql_cursor.fetchone()[0]
            
            # Check SQLite count
            sqlite_cursor = connections['sqlite'].cursor()
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            sqlite_count = sqlite_cursor.fetchone()[0]
            
            if mysql_count > 0:
                tables_with_data.append((model_name, table_name, mysql_count, sqlite_count))
            else:
                tables_empty.append(model_name)
                
        except Exception as e:
            print(f"  ✗ {model_name}: {str(e)[:50]}")
    
    # Sort by count
    tables_with_data.sort(key=lambda x: x[2], reverse=True)
    
    # Show tables with data
    print("="*70)
    print("Tables WITH Data in MySQL")
    print("="*70)
    print(f"{'Model':<30} {'Table':<30} {'MySQL':>8} {'SQLite':>8}")
    print("-"*70)
    
    for model_name, table_name, mysql_count, sqlite_count in tables_with_data:
        status = "✓" if sqlite_count > 0 else "✗"
        print(f"{model_name:<30} {table_name:<30} {mysql_count:>8,} {sqlite_count:>8,} {status}")
    
    print("\n" + "="*70)
    print(f"Summary: {len(tables_with_data)} tables have data in MySQL")
    print(f"         {sum(1 for _, _, _, s in tables_with_data if s > 0)} have been migrated to SQLite")
    print(f"         {sum(1 for _, _, _, s in tables_with_data if s == 0)} NOT yet migrated ✗")
    print("="*70)
    
    # Show empty tables
    if tables_empty:
        print("\nTables EMPTY in MySQL:")
        for name in sorted(tables_empty):
            print(f"  - {name}")
    
    # Show specific key tables
    print("\n" + "="*70)
    print("Key Tables Status")
    print("="*70)
    
    key_tables = [
        'Users', 'Students', 'Courses', 'Subjects', 'Books',
        'Exams', 'Assignments', 'StudentsSubjects', 'StudentsBooks',
        'StudentsExams', 'StudentsAssignment'
    ]
    
    for model_name in key_tables:
        found = False
        for name, table, mysql_c, sqlite_c in tables_with_data:
            if name == model_name:
                percent = (sqlite_c / mysql_c * 100) if mysql_c > 0 else 0
                print(f"  {model_name:<25} MySQL: {mysql_c:>6,} → SQLite: {sqlite_c:>6,} ({percent:.1f}%)")
                found = True
                break
        if not found:
            print(f"  {model_name:<25} No data in MySQL")
    
    # Sample some Students data to check FK issues
    print("\n" + "="*70)
    print("Sample Students Records (First 5)")
    print("="*70)
    
    try:
        # First, check what columns actually exist in students table
        mysql_cursor.execute("DESCRIBE students")
        columns = mysql_cursor.fetchall()
        column_names = [col[0] for col in columns]
        
        print(f"Actual columns in students table: {', '.join(column_names[:10])}...")
        
        # Use actual column names
        mysql_cursor.execute("""
            SELECT id, first_name, last_name, user_id, 
                   language_id, citizenship, country
            FROM students 
            LIMIT 5
        """)
        
        rows = mysql_cursor.fetchall()
        
        if rows:
            print(f"\n{'ID':<6} {'Name':<25} {'User':<6} {'Lang':<5} {'Citizen':<7} {'Country':<7}")
            print("-"*70)
            
            for row in rows:
                id_, first, last, user_id, lang_id, citizen_id, country_id = row
                name = f"{first} {last or ''}"[:25]
                print(f"{id_:<6} {name:<25} {user_id or 'NULL':<6} {lang_id or 'NULL':<5} {citizen_id or 'NULL':<7} {country_id or 'NULL':<7}")
            
            # Check if those FKs exist
            print("\nChecking if those FK records exist in SQLite...")
            
            sqlite_cursor = connections['sqlite'].cursor()
            
            for row in rows:
                id_, first, last, user_id, lang_id, citizen_id, country_id = row
                
                print(f"\nStudent ID {id_} ({first} {last or ''}):")
                
                # Check User
                if user_id:
                    sqlite_cursor.execute(f"SELECT COUNT(*) FROM users WHERE id = {user_id}")
                    exists = sqlite_cursor.fetchone()[0] > 0
                    print(f"  User {user_id}: {'✓ EXISTS' if exists else '✗ MISSING'}")
                
                # Check Language
                if lang_id:
                    sqlite_cursor.execute(f"SELECT COUNT(*) FROM languages WHERE id = {lang_id}")
                    exists = sqlite_cursor.fetchone()[0] > 0
                    print(f"  Language {lang_id}: {'✓ EXISTS' if exists else '✗ MISSING'}")
        else:
            print("  No students found in MySQL!")
            
    except Exception as e:
        print(f"  Error checking students: {e}")
    
    print("\n" + "="*70)

if __name__ == '__main__':
    check_table_counts()