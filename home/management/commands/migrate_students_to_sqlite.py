"""
Django Management Command to Migrate Students Table from MySQL to SQLite3

Save this file as: your_app/management/commands/migrate_students_to_sqlite.py

Usage:
    python manage.py migrate_students_to_sqlite
"""

from django.core.management.base import BaseCommand
from django.db import connections
from django.apps import apps
import json
from datetime import datetime, date


class Command(BaseCommand):
    help = 'Migrate students table from MySQL to SQLite3'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to process in each batch'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Test migration without actually saving data'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']

        self.stdout.write(self.style.WARNING(
            f"{'DRY RUN: ' if dry_run else ''}Starting migration of students table..."
        ))

        # Get the Students model
        try:
            Students = apps.get_model('home', 'Students')  # Change 'home'
        except LookupError:
            self.stdout.write(self.style.ERROR(
                "Students model not found. Please update 'home' in the script."
            ))
            return

        # Get connections
        mysql_conn = connections['default']
        sqlite_conn = connections['sqlite']

        # Count total records in MySQL
        with mysql_conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM students")
            total_count = cursor.fetchone()[0]

        self.stdout.write(self.style.SUCCESS(
            f"Found {total_count} students in MySQL database"
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING(
                "Dry run mode - no data will be saved"
            ))
            return

        # Use Django ORM to fetch and migrate
        migrated_count = 0
        error_count = 0
        errors = []

        # Fetch students in batches from MySQL
        mysql_students = Students.objects.using('default').all()
        
        for i in range(0, total_count, batch_size):
            batch = list(mysql_students[i:i + batch_size])
            
            for student in batch:
                try:
                    # Create a new instance for SQLite
                    # We need to set the pk to None to create a new record
                    student_data = {
                        'id': student.id,
                        'student_id': student.student_id,
                        'user_id': student.user_id,
                        'first_name': student.first_name,
                        'middle_name': student.middle_name,
                        'last_name': student.last_name,
                        'email': student.email,
                        'course_completed_email': student.course_completed_email,
                        'gender': student.gender,
                        'citizenship_id': student.citizenship_id,
                        'phone_code': student.phone_code,
                        'phone_number': student.phone_number,
                        'date_of_birth': student.date_of_birth,
                        'mrital_status': student.mrital_status,
                        'spouse_name': student.spouse_name,
                        'children': student.children,
                        'mailing_address': student.mailing_address,
                        'city': student.city,
                        'state': student.state,
                        'country_id': student.country_id,
                        'photo': student.photo,
                        'zip_code': student.zip_code,
                        'timezone': student.timezone,
                        'highest_education': student.highest_education,
                        'course_applied_id': student.course_applied_id,
                        'associate_degree': student.associate_degree,
                        'language_id': student.language_id,
                        'starting_year': student.starting_year,
                        'ministerial_status': student.ministerial_status,
                        'church_affiliation': student.church_affiliation,
                        'scholarship_needed': student.scholarship_needed,
                        'currently_employed': student.currently_employed,
                        'income': student.income,
                        'affordable_amount': student.affordable_amount,
                        'message': student.message,
                        'reference_email2': student.reference_email2,
                        'reference_name1': student.reference_name1,
                        'reference_email1': student.reference_email1,
                        'reference_phone1': student.reference_phone1,
                        'reference_name2': student.reference_name2,
                        'reference_phone2': student.reference_phone2,
                        'reference_name3': student.reference_name3,
                        'reference_email3': student.reference_email3,
                        'reference_phone3': student.reference_phone3,
                        'certificate1': student.certificate1,
                        'certificate2': student.certificate2,
                        'certificate3': student.certificate3,
                        'certificate4': student.certificate4,
                        'certificate5': student.certificate5,
                        'approve_date': student.approve_date,
                        'created_at': student.created_at,
                        'updated_at': student.updated_at,
                        'status': student.status,
                        'active': student.active,
                    }

                    # Create or update in SQLite
                    Students.objects.using('sqlite').update_or_create(
                        id=student.id,
                        defaults=student_data
                    )
                    
                    migrated_count += 1
                    
                    if migrated_count % 10 == 0:
                        self.stdout.write(
                            f"Progress: {migrated_count}/{total_count} students migrated..."
                        )

                except Exception as e:
                    error_count += 1
                    error_msg = f"Error migrating student ID {student.id}: {str(e)}"
                    errors.append(error_msg)
                    self.stdout.write(self.style.ERROR(error_msg))

        # Summary
        self.stdout.write(self.style.SUCCESS(
            f"\n{'='*60}"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Migration completed!"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Total students in MySQL: {total_count}"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Successfully migrated: {migrated_count}"
        ))
        
        if error_count > 0:
            self.stdout.write(self.style.ERROR(
                f"Errors encountered: {error_count}"
            ))
            self.stdout.write(self.style.ERROR(
                f"See error details above"
            ))

        # Verify count in SQLite
        sqlite_count = Students.objects.using('sqlite').count()
        self.stdout.write(self.style.SUCCESS(
            f"Records in SQLite after migration: {sqlite_count}"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"{'='*60}\n"
        ))