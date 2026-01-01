from django.core.management.base import BaseCommand
from home.models import Users, Students

class Command(BaseCommand):
    help = 'Delete users with ID >= 92 and their corresponding student records'

    def handle(self, *args, **options):
        # Confirm with the user
        self.stdout.write(self.style.WARNING("This will delete all users with ID >= 92 and their associated student records."))
        # confirmation = input("Are you sure you want to proceed? (yes/no): ")
        # if confirmation.lower() != 'yes':
        #     self.stdout.write(self.style.ERROR("Operation cancelled."))
        #     return

        users_to_delete = Users.objects.filter(id__gte=92)
        count = users_to_delete.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS("No users found with ID >= 92."))
            return

        self.stdout.write(f"Found {count} users to delete.")

        deleted_students = 0
        deleted_users = 0

        # Import related models to manually check constraints
        from home.models import StudentsAssignment, StudentsExams

        for user in users_to_delete:
            try:
                self.stdout.write(f"Processing User ID: {user.id} ({user.email})")
                
                # 1. Manually delete dependent records where this user might be 'created_by' or 'updated_by'
                # This is a brute-force approach to clear DO_NOTHING constraints if they exist on these tables
                # But careful, we don't want to delete random data. 
                # Only delete if it's related to the student we are about to delete anyway.
                # But if the user created records for *other* students (unlikely for a student user), we'd have a problem.
                # Assuming these are student users, they only create their own assignments/exams.
                
                # Check for students linked to this user
                students = user.student.all()
                for student in students:
                    self.stdout.write(f"  - Found linked Student ID: {student.id}")
                    
                    # Explicitly delete related assignments and exams for this student to ensure cascading happens
                    # and to clear the created_by/updated_by references if they point to this user.
                    
                    # Assignments
                    sas = StudentsAssignment.objects.filter(student=student)
                    sa_count = sas.count()
                    sas.delete()
                    if sa_count: self.stdout.write(f"    - Deleted {sa_count} StudentsAssignment records.")

                    # Exams
                    ses = StudentsExams.objects.filter(student=student)
                    se_count = ses.count()
                    ses.delete()
                    if se_count: self.stdout.write(f"    - Deleted {se_count} StudentsExams records.")

                    student_id_val = student.id
                    student.delete()
                    self.stdout.write(f"    - Deleted Student ID: {student_id_val}")
                    deleted_students += 1
                
                # 2. Check if User is referenced elsewhere as created_by/updated_by not covered above
                # (Optional: Add more checks if needed)

                user_id_val = user.id
                user.delete()
                self.stdout.write(self.style.SUCCESS(f"  - Deleted User ID: {user_id_val}"))
                deleted_users += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error deleting User ID {user.id}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully deleted {deleted_users} Users and {deleted_students} associated Students."))
