import os
import django
import sys
import datetime

# Setup Django environment
sys.path.append('/Users/pramodgopinath/Desktop/Projects/Trinity_Seminary/seminary')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')
django.setup()

from django.db import transaction
from django.utils import timezone
from home.models import Users, Students, ChurchAdmins, RoleUsers, Payments

def run_deletion():
    min_date = timezone.make_aware(datetime.datetime(2026, 7, 15))
    
    try:
        with transaction.atomic():
            # Get matching user IDs
            users = Users.objects.filter(created_at__gte=min_date)
            user_ids = [u.id for u in users]
            emails = [u.email for u in users]
            
            # Get matching student IDs
            students = Students.objects.filter(created_at__gte=min_date)
            student_ids = [s.id for s in students]
            
            # Get matching church admin IDs
            admins = ChurchAdmins.objects.filter(created_at__gte=min_date)
            admin_ids = [a.id for a in admins]
            
            print('Emails to delete:', emails)
            print('User IDs:', user_ids)
            print('Student IDs:', student_ids)
            print('Church Admin IDs:', admin_ids)
            
            if not user_ids:
                print('No entries found to delete.')
                return
            
            # Delete Payments
            payments_deleted, _ = Payments.objects.filter(church_admin_id__in=admin_ids).delete()
            print('Payments deleted:', payments_deleted)
            
            # Delete RoleUsers
            roles_deleted, _ = RoleUsers.objects.filter(user_id__in=user_ids).delete()
            print('RoleUsers deleted:', roles_deleted)
            
            # Delete Students
            students_deleted, _ = Students.objects.filter(id__in=student_ids).delete()
            print('Students deleted:', students_deleted)
            
            # Delete ChurchAdmins
            admins_deleted, _ = ChurchAdmins.objects.filter(id__in=admin_ids).delete()
            print('ChurchAdmins deleted:', admins_deleted)
            
            # Delete Users
            users_deleted, _ = Users.objects.filter(id__in=user_ids).delete()
            print('Users deleted:', users_deleted)
            
            print('--- DELETE TRANSACTION COMPLETED SUCCESSFULLY ---')
    except Exception as e:
        print('Error during deletion:', e)

if __name__ == '__main__':
    run_deletion()
