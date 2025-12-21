import os
import sys
import django
import csv
from datetime import datetime

# Setup Django environment
sys.path.append('/path/to/your/project')  # UPDATE THIS PATH
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')
django.setup()

from home.models import StudentsAssignment, Students, Assignments, Users

def parse_datetime(date_string):
    """Parse datetime string from CSV"""
    if not date_string or date_string.strip() == '':
        return None
    
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d',
        '%d/%m/%Y %H:%M:%S',
        '%m/%d/%Y %H:%M:%S',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string.strip(), fmt)
        except ValueError:
            continue
    
    return None

def parse_float(value):
    """Parse float values from CSV"""
    if not value or value.strip() == '':
        return None
    try:
        return float(value.strip())
    except ValueError:
        return None

def get_default_user():
    """Get or create default user with ID 1"""
    try:
        return Users.objects.get(id=1)
    except Users.DoesNotExist:
        print("⚠️  Warning: Default user with ID 1 not found!")
        print("Please ensure user with ID 1 exists in the database.")
        sys.exit(1)

def migrate_students_assignment(csv_file_path, skip_missing=False):
    """Migrate StudentsAssignment from CSV"""
    success_count = 0
    error_count = 0
    skipped_count = 0
    errors = []
    
    # Get default user
    default_user = get_default_user()
    print(f"Using default user ID: {default_user.id}\n")
    
    # Pre-load valid IDs
    valid_student_ids = set(Students.objects.values_list('id', flat=True))
    valid_assignment_ids = set(Assignments.objects.values_list('id', flat=True))
    
    print(f"Valid student IDs in database: {len(valid_student_ids)}")
    print(f"Valid assignment IDs in database: {len(valid_assignment_ids)}")
    
    if len(valid_student_ids) == 0:
        print("\n❌ ERROR: No Students found in database!")
        print("Please run the Students migration first.")
        return
    
    if len(valid_assignment_ids) == 0:
        print("\n❌ ERROR: No Assignments found in database!")
        print("Please run the Assignments migration first.")
        return
    
    print()

    with open(csv_file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                student_id = int(row['student_id'])
                assignment_id = int(row['assignment_id'])
                
                # Check if foreign keys exist
                if student_id not in valid_student_ids or assignment_id not in valid_assignment_ids:
                    if skip_missing:
                        skipped_count += 1
                        if skipped_count <= 10:
                            missing = []
                            if student_id not in valid_student_ids:
                                missing.append(f"Student {student_id}")
                            if assignment_id not in valid_assignment_ids:
                                missing.append(f"Assignment {assignment_id}")
                            print(f"⊘ Row {row_num}: Skipped - Missing: {', '.join(missing)}")
                        elif skipped_count == 11:
                            print(f"... (suppressing further skip messages)")
                        continue
                    else:
                        missing = []
                        if student_id not in valid_student_ids:
                            missing.append(f"Student with ID {student_id}")
                        if assignment_id not in valid_assignment_ids:
                            missing.append(f"Assignment with ID {assignment_id}")
                        raise Exception(f"Missing foreign keys: {', '.join(missing)}")
                
                # Get foreign key instances
                student = Students.objects.get(id=student_id)
                assignment = Assignments.objects.get(id=assignment_id)
                
                # Get Users for foreign keys with default fallback
                created_by = default_user
                if row['created_by'] and row['created_by'].strip():
                    try:
                        created_by = Users.objects.get(id=int(row['created_by']))
                    except Users.DoesNotExist:
                        created_by = default_user
                
                updated_by = default_user
                if row['updated_by'] and row['updated_by'].strip():
                    try:
                        updated_by = Users.objects.get(id=int(row['updated_by']))
                    except Users.DoesNotExist:
                        updated_by = default_user
                
                # Create StudentsAssignment instance
                student_assignment = StudentsAssignment(
                    id=int(row['id']),
                    student=student,
                    assignment=assignment,
                    submission_date=parse_datetime(row['submission_date']),
                    submitted_on=parse_datetime(row['submitted_on']),
                    total_marks=parse_float(row['total_marks']),
                    deleted_at=parse_datetime(row['deleted_at']),
                    created_by=created_by,
                    updated_by=updated_by,
                )
                
                # Handle auto_now and auto_now_add fields
                if row['created_at'] and row['created_at'].strip():
                    student_assignment.created_at = parse_datetime(row['created_at'])
                if row['updated_at'] and row['updated_at'].strip():
                    student_assignment.updated_at = parse_datetime(row['updated_at'])
                
                student_assignment.save()
                success_count += 1
                
                if success_count <= 10 or success_count % 100 == 0:
                    print(f"✓ Row {row_num}: Successfully migrated ID {row['id']} (Total: {success_count})")
                
            except Exception as e:
                error_msg = f"Row {row_num}: {str(e)}"
                errors.append(error_msg)
                if error_count < 10:
                    print(f"✗ {error_msg}")
                error_count += 1
    
    print("\n" + "="*50)
    print("MIGRATION SUMMARY")
    print("="*50)
    print(f"Total successful migrations: {success_count}")
    print(f"Total skipped (missing FK): {skipped_count}")
    print(f"Total errors: {error_count}")
    
    if skipped_count > 0:
        print(f"\nℹ️  Note: {skipped_count} rows were skipped due to missing foreign keys.")
        print("This is expected if some Students or Assignments records couldn't be migrated.")
    
    if errors and not skip_missing:
        print("\nFirst 10 errors:")
        for error in errors[:10]:
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")

if __name__ == '__main__':
    CSV_FILE_PATH = 'students_assignment.csv'  # UPDATE THIS
    
    print("Starting StudentsAssignment migration...")
    print(f"Reading from: {CSV_FILE_PATH}\n")
    
    if not os.path.exists(CSV_FILE_PATH):
        print(f"Error: CSV file not found at {CSV_FILE_PATH}")
        sys.exit(1)
    
    # Ask user what to do about missing foreign keys
    print("="*50)
    print("OPTIONS:")
    print("1. Skip rows with missing foreign keys (recommended)")
    print("2. Stop on missing foreign keys (fail fast)")
    print("="*50)
    
    choice = input("\nEnter your choice (1/2): ").strip()
    
    if choice == '1':
        print("\nProceeding with SKIP mode...\n")
        migrate_students_assignment(CSV_FILE_PATH, skip_missing=True)
    elif choice == '2':
        print("\nProceeding with FAIL FAST mode...\n")
        migrate_students_assignment(CSV_FILE_PATH, skip_missing=False)
    else:
        print("Invalid choice. Exiting.")
        sys.exit(1)
    
    print("\nMigration completed!")