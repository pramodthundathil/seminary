"""
Force Migration - Migrates ALL data without FK validation
Then validates after all data is loaded

Usage: python force_migrate_all.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')
django.setup()

from django.apps import apps
from django.db import connections, transaction

def execute_sql(database, sql):
    """Execute raw SQL"""
    with connections[database].cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchall()

def get_all_models(app_label):
    """Get all models from app"""
    return apps.get_app_config(app_label).get_models()

def migrate_model_raw(model):
    """
    Migrate using raw SQL - bypasses Django ORM FK checks
    This is the nuclear option that works when everything else fails
    """
    model_name = model.__name__
    table_name = model._meta.db_table
    
    try:
        # Check MySQL count
        mysql_cursor = connections['default'].cursor()
        mysql_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        mysql_count = mysql_cursor.fetchone()[0]
        
        if mysql_count == 0:
            return 0, 0
        
        print(f"  MySQL has {mysql_count:,} records")
        
        # Get all data from MySQL
        mysql_cursor.execute(f"SELECT * FROM {table_name}")
        rows = mysql_cursor.fetchall()
        
        # Get column names
        columns = [desc[0] for desc in mysql_cursor.description]
        
        if not rows:
            return 0, 0
        
        # Prepare SQLite insert
        placeholders = ','.join(['?' for _ in columns])
        column_names = ','.join(columns)
        insert_sql = f"INSERT OR IGNORE INTO {table_name} ({column_names}) VALUES ({placeholders})"
        
        # Insert into SQLite in batches
        sqlite_cursor = connections['sqlite'].cursor()
        batch_size = 500
        inserted = 0
        errors = 0
        
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            try:
                sqlite_cursor.executemany(insert_sql, batch)
                connections['sqlite'].connection.commit()
                inserted += len(batch)
                print(f"  Inserted {inserted:,}/{mysql_count:,}", end='\r')
            except Exception as e:
                errors += len(batch)
                # Try one by one for this batch
                for row in batch:
                    try:
                        sqlite_cursor.execute(insert_sql, row)
                        connections['sqlite'].connection.commit()
                        inserted += 1
                    except:
                        errors += 1
        
        # Verify
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        sqlite_count = sqlite_cursor.fetchone()[0]
        
        print(f"  ✓ SQLite now has {sqlite_count:,} records (inserted {inserted:,})")
        
        return inserted, errors
        
    except Exception as e:
        print(f"  ✗ Error: {str(e)[:100]}")
        return 0, 1

def main():
    """Main migration"""
    print("="*70)
    print("FORCE MIGRATION - Raw SQL Method")
    print("="*70)
    
    app_label = 'home'  # <<<< CHANGE THIS
    
    print(f"\nApp: {app_label}")
    print("Method: Raw SQL (bypasses all ORM checks)")
    
    # Define explicit order based on your models
    model_order = [
        # No FK dependencies
        'Countries', 'Languages', 'Qualifications', 'Roles', 'Permissions',
        
        # Depends on above
        'Users', 'Branches', 'YoutubeVideos', 'RoleUsers', 'RoleHasPermissions',
        
        # Depends on Users, Countries, Languages
        'ChurchLoginCodeSettings', 'MediaLibrary', 'Categories',
        
        # Depends on Branches, Qualifications
        'Courses',
        
        # Depends on Branches
        'Subjects',
        
        # Depends on Courses
        'Books',
        
        # Depends on Users, Countries, Languages, Courses
        'Students', 'ChurchAdmins',
        
        # Depends on Users, Students
        'Staffs',
        
        # Relationship tables
        'StaffsSubjects', 'StudentsSubjects', 'StudentsBooks', 'StudentsInstructor',
        
        # Depends on Subjects
        'Exams', 'Assignments',
        
        # Depends on Exams, Assignments
        'ObjectiveQuestions', 'DescriptiveQuestions', 'AssignmentQuestions',
        'StudentsExams', 'StudentsAssignment',
        
        # Answers
        'AssignmentAnswers', 'ObjectiveAnswers', 'DescriptiveAnswers',
        
        # Media and content
        'Uploads', 'StudentsUploads', 'BookReferences', 'Photos', 'Videos',
        
        # Pages
        'Pages', 'PageMediaLibrary', 'PageSettings',
        
        # Menus
        'Menus', 'MenuItems', 'AdminPages',
        
        # Gallery
        'PhotoGallery', 'PhotoGalleryPhotos', 'Sliders', 'SliderPhotos',
        
        # Other
        'News', 'Posts', 'Tags', 'HomeSettings', 'Contacts', 
        'ReferenceForm', 'Payments', 'PaymentSubjects',
        'Notifications', 'Support', 'SupportReplies', 'PasswordResets',
    ]
    
    # Disable FK constraints
    print("\n" + "="*70)
    print("Disabling FK constraints...")
    execute_sql('sqlite', 'PRAGMA foreign_keys = OFF;')
    print("✓ FK constraints disabled")
    
    # Get models
    all_models = {m.__name__: m for m in get_all_models(app_label)}
    
    total_inserted = 0
    total_errors = 0
    
    # Migrate each model
    print("\n" + "="*70)
    print("Migrating Models")
    print("="*70)
    
    for i, model_name in enumerate(model_order, 1):
        if model_name not in all_models:
            continue
        
        model = all_models[model_name]
        
        print(f"\n[{i}/{len(model_order)}] {model_name}")
        print("-" * 70)
        
        inserted, errors = migrate_model_raw(model)
        total_inserted += inserted
        total_errors += errors
    
    # Re-enable FK constraints
    print("\n" + "="*70)
    print("Re-enabling FK constraints...")
    execute_sql('sqlite', 'PRAGMA foreign_keys = ON;')
    print("✓ FK constraints enabled")
    
    # Check FK integrity
    print("\nChecking FK integrity...")
    fk_check = execute_sql('sqlite', 'PRAGMA foreign_key_check;')
    
    if fk_check:
        print(f"  ⚠ Found {len(fk_check)} FK violations (showing first 10):")
        for row in fk_check[:10]:
            print(f"    Table: {row[0]}, RowID: {row[1]}, Parent: {row[2]}, FK Index: {row[3]}")
        print("\n  Note: These records reference deleted/non-existent parent records")
        print("  They will work but the FK fields will point to missing data")
    else:
        print("  ✓ All foreign keys are valid!")
    
    # Summary
    print("\n" + "="*70)
    print("MIGRATION COMPLETE")
    print("="*70)
    print(f"  Total records inserted: {total_inserted:,}")
    print(f"  Total errors:           {total_errors:,}")
    print("="*70)
    
    # Show final counts
    print("\n" + "="*70)
    print("Final Record Counts (SQLite)")
    print("="*70)
    
    for model_name in model_order:
        if model_name in all_models:
            model = all_models[model_name]
            try:
                count = model.objects.using('sqlite').count()
                if count > 0:
                    print(f"  {model_name:30} {count:>8,}")
            except:
                pass
    
    print("\n✓ Done! Now test your application with SQLite")

if __name__ == '__main__':
    print("\n⚠️  This script uses RAW SQL to bypass all FK checks")
    print("  It will migrate ALL data regardless of FK issues")
    print()
    print("  Before running:")
    print("  1. Change 'home' to your actual app name")
    print("  2. Backup your SQLite db if it has data: cp db.sqlite3 db.sqlite3.backup")
    print()
    
    confirm = input("Continue? (yes/no): ")
    
    if confirm.lower() == 'yes':
        main()
    else:
        print("Cancelled.")