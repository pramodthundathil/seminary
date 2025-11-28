# import_subjects.py
# Run this script from your Django project root directory
# Usage: python import_subjects.py

import os
import sys
import csv
import django
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')
django.setup()

from home.models import Subjects, Branches, Users


def import_subjects_from_csv(csv_file_path, user_id=1):
    """
    Import subjects data from CSV file into the Subjects model.
    
    Args:
        csv_file_path: Path to the CSV file
        user_id: ID of the user for created_by and updated_by fields (default: 1)
    """
    
    try:
        user = Users.objects.get(id=user_id)
    except Users.DoesNotExist:
        print(f'Error: User with ID {user_id} does not exist')
        return
    
    success_count = 0
    error_count = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            # Strip whitespace from headers
            csv_reader.fieldnames = [name.strip() for name in csv_reader.fieldnames]
            
            print(f"CSV Headers: {csv_reader.fieldnames}")
            print("-" * 50)
            
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    # Strip whitespace from all values
                    row = {k: v.strip() if isinstance(v, str) else v for k, v in row.items()}
                    
                    # Get branch ID - can be 'branches_id' or 'branches'
                    branch_id = row.get('branches_id') or row.get('branches')
                    if not branch_id:
                        print(f"Error at row {row_num}: No branch ID found")
                        error_count += 1
                        continue
                    
                    # Get the branch object
                    try:
                        branch = Branches.objects.get(id=int(branch_id))
                    except Branches.DoesNotExist:
                        print(f"Error at row {row_num}: Branch with ID {branch_id} does not exist")
                        error_count += 1
                        continue
                    
                    # Convert status to boolean
                    status_value = row.get('status', 'True')
                    if isinstance(status_value, str):
                        status = status_value.lower() in ['true', '1', 'yes', 'active']
                    else:
                        status = bool(status_value)
                    
                    # Convert fees to float (handle empty/null values)
                    fees_value = row.get('fees', '')
                    if fees_value and fees_value.strip() and fees_value.upper() not in ['NULL', 'NONE', '']:
                        try:
                            fees = float(fees_value)
                        except ValueError:
                            fees = None
                    else:
                        fees = None
                    
                    # Check if subject exists
                    subject_code = row.get('subject_code', '')
                    existing_subject = Subjects.objects.filter(subject_code=subject_code).first()
                    
                    # Prepare defaults
                    defaults = {
                        'branches': branch,
                        'subject_name': row.get('subject_name', ''),
                        'no_of_exams': int(row.get('no_of_exams', 0)),
                        'class_hours': float(row.get('class_hours', 0)),
                        'fees': fees,
                        'status': status,
                        'updated_by': user,
                    }
                    
                    # Set created_at and created_by only for new records
                    if not existing_subject:
                        defaults['created_by'] = user
                    
                    # Create or update subject
                    subject, created = Subjects.objects.update_or_create(
                        subject_code=subject_code,
                        defaults=defaults
                    )
                    
                    action = "Created" if created else "Updated"
                    print(f"{action} subject: {subject.subject_name} (Code: {subject.subject_code})")
                    success_count += 1
                    
                except ValueError as e:
                    print(f"Error at row {row_num}: Invalid data format - {str(e)}")
                    print(f"Row data: {row}")
                    error_count += 1
                    continue
                except Exception as e:
                    print(f"Error at row {row_num}: {str(e)}")
                    print(f"Row data: {row}")
                    error_count += 1
                    continue
        
        print("-" * 50)
        print(f"Import completed!")
        print(f"Successfully imported: {success_count}")
        print(f"Errors: {error_count}")
        
    except FileNotFoundError:
        print(f"Error: File '{csv_file_path}' not found")
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    # Configuration
    CSV_FILE_PATH = 'subjects.csv'  # Change this to your CSV file path
    USER_ID = 1  # Change this to the appropriate user ID
    
    # Check if CSV file path is provided as command line argument
    if len(sys.argv) > 1:
        CSV_FILE_PATH = sys.argv[1]
    
    if len(sys.argv) > 2:
        USER_ID = int(sys.argv[2])
    
    print(f"Starting import from: {CSV_FILE_PATH}")
    print(f"Using User ID: {USER_ID}")
    print("-" * 50)
    
    import_subjects_from_csv(CSV_FILE_PATH, USER_ID)