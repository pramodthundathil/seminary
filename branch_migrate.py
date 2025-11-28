# import_branches.py
# Run this script from your Django project root directory
# Usage: python import_branches.py

import os
import sys
import csv
import django
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')
django.setup()

from home.models import Branches, Users


def import_branches_from_csv(csv_file_path, user_id=1):
    """
    Import branches data from CSV file into the Branches model.
    
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
                    
                    # Convert status to boolean
                    status_value = row.get('status', 'True')
                    if isinstance(status_value, str):
                        status = status_value.lower() in ['true', '1', 'yes', 'active']
                    else:
                        status = bool(status_value)
                    
                    # Check if branch exists
                    branch_code = row.get('branch_code', '')
                    existing_branch = Branches.objects.filter(branch_code=branch_code).first()
                    
                    # Prepare defaults
                    defaults = {
                        'branch_name': row.get('branch_name', ''),
                        'is_associate_degree': int(row.get('is_associate_degree', 0)),
                        'status': status,
                        'updated_by': user,
                    }
                    
                    # Set created_at and created_by only for new records
                    if not existing_branch:
                        defaults['created_at'] = timezone.now()
                        defaults['created_by'] = user
                    
                    # Create or update branch
                    branch, created = Branches.objects.update_or_create(
                        branch_code=branch_code,
                        defaults=defaults
                    )
                    
                    action = "Created" if created else "Updated"
                    print(f"{action} branch: {branch.branch_name} (Code: {branch.branch_code})")
                    success_count += 1
                    
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
    CSV_FILE_PATH = 'branches.csv'  # Change this to your CSV file path
    USER_ID = 1  # Change this to the appropriate user ID
    
    # Check if CSV file path is provided as command line argument
    if len(sys.argv) > 1:
        CSV_FILE_PATH = sys.argv[1]
    
    if len(sys.argv) > 2:
        USER_ID = int(sys.argv[2])
    
    print(f"Starting import from: {CSV_FILE_PATH}")
    print(f"Using User ID: {USER_ID}")
    print("-" * 50)
    
    import_branches_from_csv(CSV_FILE_PATH, USER_ID)