import os
import sys
import django
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation

# Setup Django environment
sys.path.append('/path/to/your/project')  # Update this path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')
django.setup()

from home.models import Payments, Students, ChurchAdmins, Subjects

def parse_datetime(date_string):
    """Parse datetime string from CSV"""
    if not date_string or date_string.strip() == '':
        return None
    try:
        return datetime.strptime(date_string.strip(), '%Y-%m-%d %H:%M:%S')
    except ValueError:
        try:
            return datetime.strptime(date_string.strip(), '%Y-%m-%d')
        except ValueError:
            return None

def parse_boolean(value):
    """Parse boolean value from CSV"""
    if not value or value.strip() == '':
        return False
    return value.strip().lower() in ('true', '1', 'yes', 't')

def parse_int(value):
    """Parse integer value from CSV"""
    if not value or value.strip() == '':
        return None
    try:
        return int(value.strip())
    except ValueError:
        return None

def parse_decimal(value):
    """Parse decimal value from CSV"""
    if not value or value.strip() == '':
        return None
    try:
        return Decimal(value.strip())
    except (InvalidOperation, ValueError):
        return None

def migrate_payments(csv_file_path, skip_missing_fk=False):
    """
    Migrate data from CSV to Payments model
    
    Args:
        csv_file_path: Path to CSV file
        skip_missing_fk: If True, skip rows with missing foreign keys
    """
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    errors = []
    
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row_num, row in enumerate(reader, start=2):
            try:
                # Parse foreign key IDs
                student_id = parse_int(row.get('student_id'))
                church_admin_id = parse_int(row.get('church_admin_id'))
                subjects_id = parse_int(row.get('subjects_id'))
                
                # Get optional foreign key instances
                student_instance = None
                if student_id:
                    try:
                        student_instance = Students.objects.get(id=student_id)
                    except Students.DoesNotExist:
                        if skip_missing_fk:
                            skipped_count += 1
                            print(f"Row {row_num}: Skipped - Student ID {student_id} not found")
                            continue
                        else:
                            print(f"Row {row_num}: Warning - Student ID {student_id} not found, setting to None")
                
                church_admin_instance = None
                if church_admin_id:
                    try:
                        church_admin_instance = ChurchAdmins.objects.get(id=church_admin_id)
                    except ChurchAdmins.DoesNotExist:
                        if skip_missing_fk:
                            skipped_count += 1
                            print(f"Row {row_num}: Skipped - ChurchAdmin ID {church_admin_id} not found")
                            continue
                        else:
                            print(f"Row {row_num}: Warning - ChurchAdmin ID {church_admin_id} not found, setting to None")
                
                subjects_instance = None
                if subjects_id:
                    try:
                        subjects_instance = Subjects.objects.get(id=subjects_id)
                    except Subjects.DoesNotExist:
                        if skip_missing_fk:
                            skipped_count += 1
                            print(f"Row {row_num}: Skipped - Subject ID {subjects_id} not found")
                            continue
                        else:
                            print(f"Row {row_num}: Warning - Subject ID {subjects_id} not found, setting to None")
                
                # Parse and validate required fields
                name = row.get('name', '').strip()
                email = row.get('email', '').strip()
                person_group = row.get('person_group', '').strip()
                
                if not name:
                    raise ValueError("Name is required but empty")
                if not email:
                    raise ValueError("Email is required but empty")
                if not person_group:
                    raise ValueError("Person group is required but empty")
                
                # Create or update Payment instance
                payment, created = Payments.objects.update_or_create(
                    id=parse_int(row.get('id')),
                    defaults={
                        'code': row.get('code', '').strip() or None,
                        'name': name,
                        'email': email,
                        'phone': row.get('phone', '').strip() or None,
                        'person_group': person_group,
                        'amount': parse_decimal(row.get('amount')),
                        'message': row.get('message', '').strip() or None,
                        'is_paid': parse_boolean(row.get('is_paid')),
                        'student': student_instance,
                        'church_admin': church_admin_instance,
                        'subjects_id': subjects_instance,
                        'updated_at': parse_datetime(row.get('updated_at')),
                        'created_at': parse_datetime(row.get('created_at')),
                        'deleted_at': parse_datetime(row.get('deleted_at')),
                    }
                )
                
                success_count += 1
                action = "Created" if created else "Updated"
                status = "Paid" if payment.is_paid else "Unpaid"
                print(f"Row {row_num}: {action} Payment ID {payment.id} - {payment.name} ({status}) - Amount: ${payment.amount or 0}")
                
            except Exception as e:
                error_count += 1
                error_msg = f"Row {row_num}: Error - {str(e)}"
                errors.append(error_msg)
                print(error_msg)
    
    # Print summary
    print("\n" + "="*50)
    print("Migration Summary")
    print("="*50)
    print(f"Successfully processed: {success_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Errors: {error_count}")
    
    # Calculate totals
    total_amount = Payments.objects.aggregate(
        total=sum('amount')
    )
    paid_amount = Payments.objects.filter(is_paid=True).aggregate(
        total=sum('amount')
    )
    
    print(f"\nPayment Statistics:")
    print(f"Total payments: {Payments.objects.count()}")
    print(f"Paid payments: {Payments.objects.filter(is_paid=True).count()}")
    print(f"Unpaid payments: {Payments.objects.filter(is_paid=False).count()}")
    
    if errors:
        print("\n" + "="*50)
        print("Error Details:")
        print("="*50)
        for error in errors:
            print(error)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python migrate_payments.py <path_to_csv_file> [--skip-missing]")
        print("\nOptions:")
        print("  --skip-missing    Skip rows with missing foreign keys")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    skip_missing = '--skip-missing' in sys.argv
    
    if not os.path.exists(csv_file_path):
        print(f"Error: File '{csv_file_path}' not found!")
        sys.exit(1)
    
    print(f"Starting migration from {csv_file_path}...")
    print(f"Skip missing FK: {skip_missing}")
    print()
    
    migrate_payments(csv_file_path, skip_missing)
    print("\nMigration completed!")