#!/usr/bin/env python
"""
Standalone Django migration script for importing CSV data into ChurchAdmins model.
Usage: python migrate_church_admins_csv.py <csv_file_path>
"""

import os
import sys
import django
import csv
from datetime import datetime

# Setup Django environment
def setup_django():
    """Configure Django settings before importing models."""
    # Add the project root to the path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')
    
    # Setup Django
    django.setup()

def parse_datetime(date_string):
    """Parse datetime string from CSV, handling various formats and empty values."""
    if not date_string or date_string.strip() == '':
        return None
    
    # Common datetime formats to try
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d',
        '%d/%m/%Y %H:%M:%S',
        '%d/%m/%Y',
        '%m/%d/%Y %H:%M:%S',
        '%m/%d/%Y',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string.strip(), fmt)
        except ValueError:
            continue
    
    print(f"Warning: Could not parse datetime: {date_string}")
    return None

def migrate_csv_to_model(csv_file_path):
    """
    Read CSV file and migrate data to ChurchAdmins model.
    
    Args:
        csv_file_path: Path to the CSV file to import
    """
    from home.models import ChurchAdmins, Students, ChurchLoginCodeSettings
    
    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file not found at {csv_file_path}")
        sys.exit(1)
    
    success_count = 0
    error_count = 0
    
    print(f"Starting migration from {csv_file_path}...")
    print("-" * 60)
    
    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
        # Use DictReader to map column names automatically
        reader = csv.DictReader(csvfile)
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
            try:
                # Handle student foreign key (nullable)
                student = None
                student_id = row.get('student_id', '').strip()
                if student_id:
                    try:
                        student = Students.objects.get(id=int(student_id))
                    except Students.DoesNotExist:
                        print(f"Row {row_num}: Warning - Student with id {student_id} does not exist, setting to NULL")
                    except ValueError:
                        print(f"Row {row_num}: Warning - Invalid student_id '{student_id}', setting to NULL")
                
                # Handle church_code foreign key (required)
                church_code_id = row.get('church_code_id', '').strip()
                if not church_code_id:
                    print(f"Row {row_num}: Skipping - No church_code_id provided")
                    error_count += 1
                    continue
                
                try:
                    church_code = ChurchLoginCodeSettings.objects.get(id=int(church_code_id))
                except ChurchLoginCodeSettings.DoesNotExist:
                    print(f"Row {row_num}: Error - ChurchLoginCodeSettings with id {church_code_id} does not exist")
                    error_count += 1
                    continue
                except ValueError:
                    print(f"Row {row_num}: Error - Invalid church_code_id '{church_code_id}'")
                    error_count += 1
                    continue
                
                # Parse datetime fields
                renewed_at = parse_datetime(row.get('renewed_at', ''))
                updated_at = parse_datetime(row.get('updated_at', ''))
                created_at = parse_datetime(row.get('created_at', ''))
                deleted_at = parse_datetime(row.get('deleted_at', ''))
                
                # Parse numeric fields
                try:
                    amount = float(row.get('amount', 0.0)) if row.get('amount', '').strip() else 0.0
                    max_user_no = int(row.get('max_user_no', 0)) if row.get('max_user_no', '').strip() else 0
                    current_user_no = int(row.get('current_user_no', 0)) if row.get('current_user_no', '').strip() else 0
                except ValueError as e:
                    print(f"Row {row_num}: Error - Invalid numeric value: {str(e)}")
                    error_count += 1
                    continue
                
                # Create or update the record
                obj, created = ChurchAdmins.objects.update_or_create(
                    id=int(row['id']),
                    defaults={
                        'student': student,
                        'name_of_church': row.get('name_of_church', '').strip() or None,
                        'name_of_paster': row.get('name_of_paster', '').strip() or None,
                        'church_address': row.get('church_address', '').strip() or None,
                        'church_code': church_code,
                        'code': row.get('code', '').strip(),
                        'amount': amount,
                        'max_user_no': max_user_no,
                        'current_user_no': current_user_no,
                        'renewed_at': renewed_at,
                        'updated_at': updated_at,
                        'created_at': created_at,
                        'deleted_at': deleted_at,
                    }
                )
                
                action = "Created" if created else "Updated"
                church_name = obj.name_of_church or "Unnamed Church"
                print(f"Row {row_num}: {action} record with ID {obj.id} - {church_name} (Code: {obj.code})")
                success_count += 1
                
            except Exception as e:
                print(f"Row {row_num}: Error - {str(e)}")
                error_count += 1
                continue
    
    print("-" * 60)
    print(f"Migration completed!")
    print(f"Successfully processed: {success_count} records")
    print(f"Errors: {error_count} records")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python migrate_church_admins_csv.py <csv_file_path>")
        print("Example: python migrate_church_admins_csv.py data/church_admins.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    # Setup Django
    setup_django()
    
    # Run migration
    migrate_csv_to_model(csv_file)