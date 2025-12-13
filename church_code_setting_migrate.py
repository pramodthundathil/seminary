#!/usr/bin/env python
"""
Standalone Django migration script for importing CSV data into ChurchLoginCodeSettings model.
Usage: python migrate_csv_to_django.py <csv_file_path>
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
    Read CSV file and migrate data to ChurchLoginCodeSettings model.
    
    Args:
        csv_file_path: Path to the CSV file to import
    """
    from home.models import ChurchLoginCodeSettings, Branches
    
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
                # Get the branch foreign key
                branch_id = row.get('branches_id', '').strip()
                if not branch_id:
                    print(f"Row {row_num}: Skipping - No branch_id provided")
                    error_count += 1
                    continue
                
                try:
                    branch = Branches.objects.get(id=int(branch_id))
                except Branches.DoesNotExist:
                    print(f"Row {row_num}: Error - Branch with id {branch_id} does not exist")
                    error_count += 1
                    continue
                
                # Parse datetime fields
                updated_at = parse_datetime(row.get('updated_at', ''))
                created_at = parse_datetime(row.get('created_at', ''))
                deleted_at = parse_datetime(row.get('deleted_at', ''))
                
                # Create or update the record
                obj, created = ChurchLoginCodeSettings.objects.update_or_create(
                    id=int(row['id']),
                    defaults={
                        'branches': branch,
                        'name': row.get('name', '').strip(),
                        'max_user_no': int(row.get('max_user_no', 0)),
                        'amount': float(row.get('amount', 0.0)),
                        'expired_in_days': row.get('expired_in_days', '').strip(),
                        'status': int(row.get('status', 0)),
                        'updated_at': updated_at,
                        'created_at': created_at,
                        'deleted_at': deleted_at,
                    }
                )
                
                action = "Created" if created else "Updated"
                print(f"Row {row_num}: {action} record with ID {obj.id} - {obj.name}")
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
        print("Usage: python migrate_csv_to_django.py <csv_file_path>")
        print("Example: python migrate_csv_to_django.py data/church_login_code_settings.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    # Setup Django
    setup_django()
    
    # Run migration
    migrate_csv_to_model(csv_file)