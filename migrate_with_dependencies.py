"""
Migrate Students and All Dependencies from MySQL to SQLite

This script migrates tables in the correct order to satisfy foreign key constraints.

Save as: migrate_with_dependencies.py
Run: python migrate_with_dependencies.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')  # Change this
django.setup()

from django.db import transaction, connections
from django.apps import apps


def get_model(app_name, model_name):
    """Safely get a model"""
    try:
        return apps.get_model(app_name, model_name)
    except LookupError:
        return None


def migrate_table(model_class, table_name, using_default='default', using_target='sqlite'):
    """
    Generic function to migrate any table from MySQL to SQLite
    """
    if model_class is None:
        print(f"⚠️  Skipping {table_name} - model not found")
        return 0
    
    print(f"\n📦 Migrating {table_name}...")
    
    try:
        # Count records
        source_count = model_class.objects.using(using_default).count()
        print(f"   Found {source_count} records in MySQL")
        
        if source_count == 0:
            print(f"   ⏭️  No records to migrate")
            return 0
        
        # Fetch all records
        records = model_class.objects.using(using_default).all()
        
        migrated = 0
        errors = 0
        
        # Migrate in batches
        batch_size = 100
        with transaction.atomic(using=using_target):
            for i in range(0, source_count, batch_size):
                batch = list(records[i:i + batch_size])
                
                for record in batch:
                    try:
                        # Get all field values as dict
                        record_dict = {}
                        for field in record._meta.fields:
                            field_name = field.name
                            
                            # Handle foreign keys
                            if field.is_relation and field.many_to_one:
                                # Get the foreign key ID value
                                fk_value = getattr(record, f"{field_name}_id", None)
                                record_dict[f"{field_name}_id"] = fk_value
                            else:
                                # Regular field
                                record_dict[field_name] = getattr(record, field_name)
                        
                        # Create or update in target database
                        model_class.objects.using(using_target).update_or_create(
                            id=record.id,
                            defaults=record_dict
                        )
                        
                        migrated += 1
                        
                    except Exception as e:
                        errors += 1
                        if errors <= 3:  # Only show first 3 errors
                            print(f"   ✗ Error with ID {record.id}: {str(e)}")
        
        # Verify
        target_count = model_class.objects.using(using_target).count()
        print(f"   ✅ Migrated {migrated} records (Target now has {target_count})")
        
        if errors > 0:
            print(f"   ⚠️  {errors} errors encountered")
        
        return migrated
        
    except Exception as e:
        print(f"   ❌ Failed to migrate {table_name}: {str(e)}")
        return 0


def migrate_with_raw_sql(table_name, using_default='default', using_target='sqlite'):
    """
    Migrate table using raw SQL - useful when foreign key constraints are an issue
    """
    print(f"\n📦 Migrating {table_name} (Raw SQL)...")
    
    source_conn = connections[using_default]
    target_conn = connections[using_target]
    
    try:
        # Get data from source
        with source_conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
        
        count = len(rows)
        print(f"   Found {count} records in MySQL")
        
        if count == 0:
            return 0
        
        # Disable foreign key checks temporarily in SQLite
        with target_conn.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            migrated = 0
            for row in rows:
                try:
                    # Prepare INSERT OR REPLACE
                    placeholders = ', '.join(['?' for _ in row])
                    columns = ', '.join(column_names)
                    sql = f"INSERT OR REPLACE INTO {table_name} ({columns}) VALUES ({placeholders})"
                    
                    cursor.execute(sql, row)
                    migrated += 1
                    
                except Exception as e:
                    if migrated == 0:  # Show first error
                        print(f"   ✗ Error: {str(e)}")
            
            # Re-enable foreign key checks
            cursor.execute("PRAGMA foreign_keys = ON")
        
        print(f"   ✅ Migrated {migrated} records")
        return migrated
        
    except Exception as e:
        print(f"   ❌ Failed: {str(e)}")
        return 0


def main():
    """
    Main migration function - migrates tables in dependency order
    """
    
    print("="*70)
    print("🚀 MIGRATING STUDENTS AND DEPENDENCIES: MySQL → SQLite")
    print("="*70)
    
    app_name = 'home'  # ← CHANGE THIS to your Django app name
    
    # Define migration order based on dependencies
    # Format: (model_name, table_name)
    migration_order = [
        # Level 0: No dependencies
        ('Countries', 'countries'),
        ('Qualifications', 'qualifications'),
        ('Permissions', 'permissions'),
        ('Roles', 'roles'),
        
        # Level 1: Depends on Level 0
        ('ChurchAdmins', 'church_admins'),
        ('Users', 'users'),
        ('Languages', 'languages'),
        
        # Level 2: Depends on Users
        ('MediaLibrary', 'media_library'),
        ('YoutubeVideos', 'youtube_videos'),
        ('Branches', 'branches'),
        ('Courses', 'courses'),
        
        # Level 3: Depends on Branches/Courses
        ('Subjects', 'subjects'),
        ('Books', 'books'),
        
        # Level 4: Students (depends on Users, Countries, Languages, Courses)
        ('Students', 'students'),
    ]
    
    total_migrated = 0
    
    for model_name, table_name in migration_order:
        model_class = get_model(app_name, model_name)
        migrated = migrate_table(model_class, table_name)
        total_migrated += migrated
    
    # Summary
    print("\n" + "="*70)
    print("📊 MIGRATION SUMMARY")
    print("="*70)
    print(f"Total records migrated: {total_migrated}")
    
    # Verify Students
    Students = get_model(app_name, 'Students')
    if Students:
        mysql_count = Students.objects.using('default').count()
        sqlite_count = Students.objects.using('sqlite').count()
        print(f"\nStudents in MySQL:  {mysql_count}")
        print(f"Students in SQLite: {sqlite_count}")
        
        if mysql_count == sqlite_count:
            print("✅ All students migrated successfully!")
        else:
            print(f"⚠️  Missing {mysql_count - sqlite_count} students")
    
    print("="*70)


def quick_migrate_students_only():
    """
    Quick migration of students only - disables FK checks
    Use only if parent tables are already migrated
    """
    
    print("="*70)
    print("🚀 QUICK STUDENT MIGRATION (FK Checks Disabled)")
    print("="*70)
    
    target_conn = connections['sqlite']
    
    # Temporarily disable foreign key constraints
    with target_conn.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys = OFF")
    
    print("\n⚠️  Foreign key checks disabled temporarily")
    
    # Migrate
    migrated = migrate_with_raw_sql('students')
    
    # Re-enable foreign key constraints
    with target_conn.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys = ON")
    
    print("\n✅ Foreign key checks re-enabled")
    print("="*70)
    
    return migrated


def check_missing_foreign_keys():
    """
    Check which foreign key records are missing
    """
    from home.models import Students  # Change 'home'
    
    print("\n🔍 Checking for missing foreign key records...")
    print("-"*70)
    
    # Get all students from MySQL
    students = Students.objects.using('default').all()
    
    missing_users = set()
    missing_countries = set()
    missing_languages = set()
    missing_courses = set()
    
    for student in students[:100]:  # Check first 100
        if student.user_id:
            try:
                Users = get_model('home', 'Users')
                Users.objects.using('sqlite').get(id=student.user_id)
            except:
                missing_users.add(student.user_id)
        
        if student.citizenship_id:
            try:
                Countries = get_model('home', 'Countries')
                Countries.objects.using('sqlite').get(id=student.citizenship_id)
            except:
                missing_countries.add(student.citizenship_id)
        
        if student.country_id:
            try:
                Countries = get_model('home', 'Countries')
                Countries.objects.using('sqlite').get(id=student.country_id)
            except:
                missing_countries.add(student.country_id)
        
        if student.language_id:
            try:
                Languages = get_model('home', 'Languages')
                Languages.objects.using('sqlite').get(id=student.language_id)
            except:
                missing_languages.add(student.language_id)
        
        if student.course_applied_id:
            try:
                Courses = get_model('home', 'Courses')
                Courses.objects.using('sqlite').get(id=student.course_applied_id)
            except:
                missing_courses.add(student.course_applied_id)
    
    print(f"Missing Users:     {len(missing_users)} IDs: {list(missing_users)[:5]}")
    print(f"Missing Countries: {len(missing_countries)} IDs: {list(missing_countries)[:5]}")
    print(f"Missing Languages: {len(missing_languages)} IDs: {list(missing_languages)[:5]}")
    print(f"Missing Courses:   {len(missing_courses)} IDs: {list(missing_courses)[:5]}")
    print("-"*70)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--check':
        check_missing_foreign_keys()
    elif len(sys.argv) > 1 and sys.argv[1] == '--quick':
        # Quick migration with FK checks disabled
        quick_migrate_students_only()
    elif len(sys.argv) > 1 and sys.argv[1] == '--students-only':
        # Migrate only students (assumes dependencies exist)
        app_name = 'home'  # Change this
        Students = get_model(app_name, 'Students')
        migrate_table(Students, 'students')
    else:
        # Full migration with all dependencies
        response = input("⚠️  This will migrate students and dependencies. Continue? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            main()
        else:
            print("Migration cancelled.")