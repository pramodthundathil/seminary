# """
# Robust MySQL to SQLite Migration Script with FK Error Handling
# Works with dual database configuration

# Usage: python migrate_data.py
# """

# import os
# import django

# # Setup Django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')
# django.setup()

# from django.apps import apps
# from django.db import transaction, connections
# from django.core.exceptions import ObjectDoesNotExist

# def disable_foreign_keys(database='sqlite'):
#     """Temporarily disable foreign key checks"""
#     with connections[database].cursor() as cursor:
#         cursor.execute('PRAGMA foreign_keys = OFF;')
#     print("  ✓ Foreign key constraints disabled")

# def enable_foreign_keys(database='sqlite'):
#     """Re-enable foreign key checks"""
#     with connections[database].cursor() as cursor:
#         cursor.execute('PRAGMA foreign_keys = ON;')
#     print("  ✓ Foreign key constraints enabled")

# def check_record_exists_in_sqlite(model, pk):
#     """Check if a record already exists in SQLite"""
#     try:
#         return model.objects.using('sqlite').filter(pk=pk).exists()
#     except:
#         return False

# def get_fk_fields(model):
#     """Get all foreign key fields for a model"""
#     return [
#         field for field in model._meta.get_fields()
#         if field.many_to_one and field.concrete
#     ]

# def validate_foreign_keys(record, model):
#     """
#     Check if all foreign key relationships exist in SQLite
#     Returns True if all FKs are valid or can be set to None
#     """
#     fk_fields = get_fk_fields(model)
    
#     for fk_field in fk_fields:
#         fk_value = getattr(record, fk_field.name)
        
#         if fk_value is None:
#             continue  # NULL FK is okay
        
#         # Check if the related record exists in SQLite
#         related_model = fk_field.related_model
        
#         if hasattr(fk_value, 'pk'):
#             fk_pk = fk_value.pk
#         else:
#             fk_pk = fk_value
        
#         if not check_record_exists_in_sqlite(related_model, fk_pk):
#             # If FK doesn't exist and field allows null, set to None
#             if fk_field.null:
#                 setattr(record, fk_field.name, None)
#                 setattr(record, f"{fk_field.name}_id", None)
#             else:
#                 # Required FK is missing - skip this record
#                 return False, f"Missing required FK: {fk_field.name} (ID: {fk_pk})"
    
#     return True, None

# def get_migration_order(app_label):
#     """Define the correct order for migrating models"""
#     ordered_models = [
#         # Level 1: No dependencies
#         'Countries',
#         'Languages',
#         'Qualifications',
#         'Roles',
#         'Permissions',
        
#         # Level 2: Depends on Level 1
#         'Users',
#         'Branches',
#         'YoutubeVideos',
        
#         # Level 3: Depends on Level 1-2
#         'RoleUsers',
#         'RoleHasPermissions',
#         'Courses',
#         'ChurchLoginCodeSettings',
#         'MediaLibrary',
#         'Categories',
        
#         # Level 4: Depends on Level 1-3
#         'Subjects',
#         'Books',
#         'Students',
#         'ChurchAdmins',
#         'Staffs',
#         'Exams',
#         'Assignments',
        
#         # Level 5: Relationships and dependent tables
#         'StaffsSubjects',
#         'StudentsSubjects',
#         'StudentsBooks',
#         'StudentsInstructor',
#         'ObjectiveQuestions',
#         'DescriptiveQuestions',
#         'AssignmentQuestions',
#         'StudentsExams',
#         'StudentsAssignment',
        
#         # Level 6: Answers and responses
#         'AssignmentAnswers',
#         'ObjectiveAnswers',
#         'DescriptiveAnswers',
        
#         # Level 7: Media and content
#         'Uploads',
#         'StudentsUploads',
#         'BookReferences',
#         'Photos',
#         'Videos',
#         'Pages',
#         'PageMediaLibrary',
#         'PageSettings',
#         'Menus',
#         'MenuItems',
#         'AdminPages',
#         'PhotoGallery',
#         'PhotoGalleryPhotos',
#         'Sliders',
#         'SliderPhotos',
#         'News',
#         'Posts',
#         'Tags',
#         'HomeSettings',
#         'Contacts',
#         'ReferenceForm',
#         'Payments',
#         'PaymentSubjects',
#         'Notifications',
#         'Support',
#         'SupportReplies',
#         'PasswordResets',
#     ]
    
#     models_in_order = []
#     for model_name in ordered_models:
#         try:
#             model = apps.get_model(app_label, model_name)
#             models_in_order.append(model)
#         except LookupError:
#             pass  # Model doesn't exist, skip it
    
#     return models_in_order

# def migrate_model_record_by_record(model):
#     """
#     Migrate records one by one, validating FKs for each
#     Slower but more reliable for models with FK issues
#     """
#     model_name = model.__name__
    
#     try:
#         # Get all records from MySQL
#         mysql_records = model.objects.using('default').all()
#         total_count = mysql_records.count()
        
#         if total_count == 0:
#             return 0, 0, 0
        
#         print(f"  Found {total_count} records (migrating individually)")
        
#         migrated = 0
#         skipped = 0
#         errors = 0
        
#         for i, record in enumerate(mysql_records, 1):
#             try:
#                 # Check if already exists
#                 if check_record_exists_in_sqlite(model, record.pk):
#                     skipped += 1
#                     continue
                
#                 # Validate foreign keys
#                 is_valid, error_msg = validate_foreign_keys(record, model)
                
#                 if not is_valid:
#                     skipped += 1
#                     if skipped <= 3:  # Show first 3 FK errors
#                         print(f"  ⚠ Skipping record {record.pk}: {error_msg}")
#                     continue
                
#                 # Save to SQLite
#                 record.pk = record.pk  # Keep original PK
#                 with transaction.atomic(using='sqlite'):
#                     record.save(using='sqlite', force_insert=True)
                
#                 migrated += 1
                
#                 # Progress update
#                 if i % 100 == 0:
#                     print(f"  Progress: {i}/{total_count} (✓{migrated} ⊗{skipped})", end='\r')
                
#             except Exception as e:
#                 errors += 1
#                 if errors <= 3:  # Show first 3 errors
#                     print(f"\n  ✗ Error on record {record.pk}: {str(e)[:100]}")
        
#         print(f"\n  ✓ Migrated: {migrated} | ⊗ Skipped: {skipped} | ✗ Errors: {errors}")
        
#         return migrated, skipped, errors
        
#     except Exception as e:
#         print(f"\n  ✗ Fatal error: {str(e)[:150]}")
#         return 0, 0, 1

# def migrate_model_bulk(model, batch_size=500):
#     """
#     Migrate in bulk (faster but less error handling)
#     Use this for models without FK issues
#     """
#     model_name = model.__name__
    
#     try:
#         mysql_count = model.objects.using('default').count()
        
#         if mysql_count == 0:
#             return 0, 0, 0
        
#         print(f"  Found {mysql_count} records (bulk migration)")
        
#         migrated = 0
#         skipped = 0
#         errors = 0
        
#         for offset in range(0, mysql_count, batch_size):
#             try:
#                 batch = list(
#                     model.objects.using('default')
#                     .all()[offset:offset + batch_size]
#                 )
                
#                 with transaction.atomic(using='sqlite'):
#                     created = model.objects.using('sqlite').bulk_create(
#                         batch,
#                         ignore_conflicts=True,
#                         batch_size=batch_size
#                     )
#                     migrated += len(batch)
                
#                 print(f"  Progress: {migrated}/{mysql_count}", end='\r')
                
#             except Exception as e:
#                 errors += len(batch)
#                 print(f"\n  ⚠ Batch error at offset {offset}: {str(e)[:100]}")
        
#         sqlite_count = model.objects.using('sqlite').count()
#         print(f"\n  ✓ Migrated {migrated} records (SQLite has {sqlite_count})")
        
#         return migrated, skipped, errors
        
#     except Exception as e:
#         print(f"\n  ✗ Error: {str(e)[:150]}")
#         return 0, 0, 1

# def migrate_all_data():
#     """Migrate all data from MySQL to SQLite"""
    
#     print("="*70)
#     print("MySQL to SQLite Data Migration - Robust Version")
#     print("="*70)
    
#     app_label = 'home'  # CHANGE THIS to your actual app name
    
#     # Models that typically have no FK issues (can use bulk migration)
#     safe_models = [
#         'Countries', 'Languages', 'Qualifications', 'Roles', 
#         'Permissions', 'Users', 'Branches', 'Categories', 'YoutubeVideos'
#     ]
    
#     # Disable foreign key checks
#     print("\nDisabling foreign key constraints...")
#     disable_foreign_keys('sqlite')
    
#     # Get models in correct order
#     models = get_migration_order(app_label)
    
#     total_migrated = 0
#     total_skipped = 0
#     total_errors = 0
    
#     print(f"\nMigrating {len(models)} models...\n")
    
#     for model in models:
#         model_name = model.__name__
        
#         print(f"{'='*70}")
#         print(f"Migrating: {model_name}")
#         print(f"{'='*70}")
        
#         # Use bulk migration for safe models, record-by-record for others
#         if model_name in safe_models:
#             migrated, skipped, errors = migrate_model_bulk(model)
#         else:
#             migrated, skipped, errors = migrate_model_record_by_record(model)
        
#         total_migrated += migrated
#         total_skipped += skipped
#         total_errors += errors
    
#     # Re-enable foreign key checks
#     print(f"\n{'='*70}")
#     print("Re-enabling foreign key constraints...")
#     enable_foreign_keys('sqlite')
    
#     # Verify foreign key integrity
#     print("\nVerifying foreign key integrity...")
#     with connections['sqlite'].cursor() as cursor:
#         cursor.execute('PRAGMA foreign_key_check;')
#         fk_errors = cursor.fetchall()
#         if fk_errors:
#             print(f"  ⚠ Found {len(fk_errors)} foreign key violations")
#             for error in fk_errors[:10]:
#                 print(f"    Table: {error[0]}, Row: {error[1]}, Parent: {error[2]}")
#         else:
#             print("  ✓ All foreign keys are valid!")
    
#     # Final summary
#     print(f"\n{'='*70}")
#     print(f"Migration Complete!")
#     print(f"{'='*70}")
#     print(f"✓ Successfully migrated: {total_migrated}")
#     print(f"⊗ Skipped (FK issues):   {total_skipped}")
#     print(f"✗ Errors:                {total_errors}")
#     print(f"{'='*70}")
    
#     # Show record counts for verification
#     print("\nRecord counts in SQLite:")
#     for model in models[:10]:  # Show first 10
#         count = model.objects.using('sqlite').count()
#         print(f"  {model.__name__}: {count}")

# if __name__ == '__main__':
#     print("\n⚠️  IMPORTANT:")
#     print("  1. MySQL dump should be loaded in 'mytts_temp' database")
#     print("  2. Run: python manage.py migrate --database=sqlite")
#     print()
    
#     confirm = input("Continue with migration? (yes/no): ")
    
#     if confirm.lower() == 'yes':
#         # Verify SQLite schema
#         print("\nVerifying SQLite schema...")
#         from django.core.management import call_command
#         try:
#             call_command('migrate', database='sqlite', verbosity=0)
#             print("✓ SQLite schema ready\n")
#         except Exception as e:
#             print(f"✗ Migration error: {e}")
#             exit(1)
        
#         # Migrate data
#         migrate_all_data()
        
#         print("\n✓ Migration complete!")
#         print("\nVerify your data:")
#         print("  python manage.py shell")
#         print("  >>> from home.models import Students")
#         print("  >>> Students.objects.using('sqlite').count()")
#     else:
#         print("Migration cancelled.")


from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import connections

class Command(BaseCommand):
    help = 'Migrate data from MySQL to SQLite'

    def handle(self, *args, **options):
        # Get all models from your app
        app_models = apps.get_app_config('home').get_models()
        
        # Models to skip (Django's built-in tables will be created automatically)
        skip_models = ['ContentType', 'Permission', 'Group', 'Session', 'LogEntry']
        
        for model in app_models:
            model_name = model.__name__
            
            if model_name in skip_models:
                self.stdout.write(f'Skipping {model_name}')
                continue
                
            self.stdout.write(f'Migrating {model_name}...')
            
            try:
                # Get all records from MySQL
                records = model.objects.using('default').all()
                count = records.count()
                
                if count == 0:
                    self.stdout.write(f'  No records to migrate for {model_name}')
                    continue
                
                # Bulk create in SQLite
                batch_size = 1000
                for i in range(0, count, batch_size):
                    batch = list(records[i:i + batch_size])
                    model.objects.using('sqlite').bulk_create(
                        batch, 
                        ignore_conflicts=True
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Migrated {count} records for {model_name}')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error migrating {model_name}: {str(e)}')
                )

        self.stdout.write(self.style.SUCCESS('\nMigration completed!'))