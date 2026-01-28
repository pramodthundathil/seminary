import os
import django
import sys

# Setup Django environment
sys.path.append('/Users/pramodgopinath/Desktop/Trinity_Seminary/seminary')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')
django.setup()

from home.models import StudentsBooks, Students, BookReferences

def check_data():
    print("--- Debugging StudentsBooks Data ---")
    
    # 1. Total Count
    total = StudentsBooks.objects.count()
    print(f"Total StudentsBooks records: {total}")
    
    # 2. Active Count (deleted_at is null)
    active = StudentsBooks.objects.filter(deleted_at__isnull=True).count()
    print(f"Active StudentsBooks records (deleted_at__isnull=True): {active}")
    
    # 3. Check Relationships
    if active > 0:
        first = StudentsBooks.objects.filter(deleted_at__isnull=True).first()
        print(f"\nSample Record ID: {first.id}")
        print(f"Student: {first.student_id} - {first.student}")
        print(f"Book: {first.book_id} - {first.book}")
        print(f"Is Approved: {first.is_approved}")
        print(f"Updated By: {first.updated_by_id}")
    else:
        print("\nNo active records found!")
        
    print("\n--- Related Counts ---")
    print(f"Total Students: {Students.objects.count()}")
    print(f"Total Books: {BookReferences.objects.count()}")

if __name__ == "__main__":
    check_data()
