import os
import sys
import django
import csv
from datetime import datetime

# Setup Django environment
sys.path.append('/path/to/your/project')  # Update this path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')
django.setup()

from home.models import Uploads, Videos, YoutubeVideos, Subjects, MediaLibrary, Users

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
        return True
    return value.strip().lower() in ('true', '1', 'yes', 't')

def parse_int(value):
    """Parse integer value from CSV"""
    if not value or value.strip() == '':
        return None
    try:
        return int(value.strip())
    except ValueError:
        return None

def get_or_create_default_user():
    """Get or create a default user for migration purposes"""
    try:
        # Try to get the first existing user
        default_user = Users.objects.first()
        if default_user:
            print(f"Using existing user (ID: {default_user.id}) as default")
            return default_user
    except Exception as e:
        pass
    
    # If no users exist, create a minimal one
    # Adjust the fields based on your actual Users model
    try:
        default_user, created = Users.objects.get_or_create(
            id=9999,  # Using a high ID to avoid conflicts
            defaults={
                'username': 'migration_user',
                'email': 'migration@seminary.com',
                # Add other required fields from your Users model here
            }
        )
        if created:
            print(f"Created default migration user (ID: {default_user.id})")
        return default_user
    except Exception as e:
        print(f"Error creating default user: {e}")
        print("Please provide a valid user ID or create a user manually")
        return None

def get_or_create_default_subject():
    """Get or create a default subject for migration purposes"""
    try:
        # Try to get the first existing subject
        default_subject = Subjects.objects.first()
        if default_subject:
            print(f"Using existing subject (ID: {default_subject.id}) as default")
            return default_subject
    except Exception as e:
        pass
    
    # If no subjects exist, create one
    # Adjust the fields based on your actual Subjects model
    try:
        default_subject, created = Subjects.objects.get_or_create(
            id=9999,  # Using a high ID to avoid conflicts
            defaults={
                'name': 'Uncategorized',
                # Add other required fields from your Subjects model here
            }
        )
        if created:
            print(f"Created default subject (ID: {default_subject.id})")
        return default_subject
    except Exception as e:
        print(f"Error creating default subject: {e}")
        print("Please provide a valid subject ID or create a subject manually")
        return None

def migrate_uploads(csv_file_path, skip_missing_fk=False, create_defaults=True):
    """
    Migrate data from CSV to Uploads model
    
    Args:
        csv_file_path: Path to CSV file
        skip_missing_fk: If True, skip rows with missing foreign keys
        create_defaults: If True, create default records for required foreign keys
    """
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    errors = []
    
    # Create default records if needed
    default_user = None
    default_subject = None
    if create_defaults:
        default_user = get_or_create_default_user()
        default_subject = get_or_create_default_subject()
    
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row_num, row in enumerate(reader, start=2):
            try:
                # Parse foreign key IDs
                video_id = parse_int(row.get('video_id'))
                youtube_id = parse_int(row.get('youtube_id'))
                subject_id = parse_int(row.get('subject_id'))
                media_id = parse_int(row.get('media_id'))
                created_by_id = parse_int(row.get('created_by'))
                updated_by_id = parse_int(row.get('updated_by'))
                
                # Get optional foreign key instances (can be None)
                video_instance = None
                if video_id:
                    try:
                        video_instance = Videos.objects.get(id=video_id)
                    except Videos.DoesNotExist:
                        print(f"Row {row_num}: Warning - Video ID {video_id} not found, setting to None")
                
                youtube_instance = None
                if youtube_id:
                    try:
                        youtube_instance = YoutubeVideos.objects.get(id=youtube_id)
                    except YoutubeVideos.DoesNotExist:
                        print(f"Row {row_num}: Warning - YouTube Video ID {youtube_id} not found, setting to None")
                
                media_instance = None
                if media_id:
                    try:
                        media_instance = MediaLibrary.objects.get(id=media_id)
                    except MediaLibrary.DoesNotExist:
                        print(f"Row {row_num}: Warning - Media ID {media_id} not found, setting to None")
                
                # Get required foreign key instances (subject, created_by, updated_by)
                subject_instance = None
                if subject_id:
                    try:
                        subject_instance = Subjects.objects.get(id=subject_id)
                    except Subjects.DoesNotExist:
                        if create_defaults and default_subject:
                            subject_instance = default_subject
                            print(f"Row {row_num}: Warning - Subject ID {subject_id} not found, using default")
                        elif skip_missing_fk:
                            skipped_count += 1
                            print(f"Row {row_num}: Skipped - Subject ID {subject_id} not found")
                            continue
                        else:
                            raise
                else:
                    if create_defaults and default_subject:
                        subject_instance = default_subject
                
                created_by_instance = None
                if created_by_id:
                    try:
                        created_by_instance = Users.objects.get(id=created_by_id)
                    except Users.DoesNotExist:
                        if create_defaults and default_user:
                            created_by_instance = default_user
                            print(f"Row {row_num}: Warning - User ID {created_by_id} not found, using default")
                        elif skip_missing_fk:
                            skipped_count += 1
                            print(f"Row {row_num}: Skipped - Created by User ID {created_by_id} not found")
                            continue
                        else:
                            raise
                else:
                    if create_defaults and default_user:
                        created_by_instance = default_user
                
                updated_by_instance = None
                if updated_by_id:
                    try:
                        updated_by_instance = Users.objects.get(id=updated_by_id)
                    except Users.DoesNotExist:
                        if create_defaults and default_user:
                            updated_by_instance = default_user
                            print(f"Row {row_num}: Warning - Updated by User ID {updated_by_id} not found, using default")
                        elif skip_missing_fk:
                            skipped_count += 1
                            print(f"Row {row_num}: Skipped - Updated by User ID {updated_by_id} not found")
                            continue
                        else:
                            raise
                else:
                    if create_defaults and default_user:
                        updated_by_instance = default_user
                
                # Validate required fields
                if not subject_instance:
                    raise ValueError("Subject is required but not provided")
                if not created_by_instance:
                    raise ValueError("Created by user is required but not provided")
                if not updated_by_instance:
                    raise ValueError("Updated by user is required but not provided")
                
                # Create or update Upload instance
                upload, created = Uploads.objects.update_or_create(
                    id=parse_int(row.get('id')),
                    defaults={
                        'code': row.get('code', '').strip(),
                        'upload_name': row.get('upload_name', '').strip(),
                        'description': row.get('description', '').strip(),
                        'format': row.get('format', '').strip(),
                        'video_id': video_instance,
                        'youtube': youtube_instance,
                        'aws_url': row.get('aws_url', '').strip() or None,
                        'subject': subject_instance,
                        'media': media_instance,
                        'status': parse_boolean(row.get('status')),
                        'updated_at': parse_datetime(row.get('updated_at')),
                        'created_at': parse_datetime(row.get('created_at')),
                        'created_by': created_by_instance,
                        'updated_by': updated_by_instance,
                    }
                )
                
                success_count += 1
                action = "Created" if created else "Updated"
                print(f"Row {row_num}: {action} Upload ID {upload.id} - {upload.upload_name}")
                
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
    
    if errors:
        print("\nError Details:")
        for error in errors:
            print(error)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python migrate_uploads.py <path_to_csv_file> [--skip-missing] [--no-defaults]")
        print("\nOptions:")
        print("  --skip-missing    Skip rows with missing foreign keys instead of using defaults")
        print("  --no-defaults     Don't create default user/subject records")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    skip_missing = '--skip-missing' in sys.argv
    create_defaults = '--no-defaults' not in sys.argv
    
    if not os.path.exists(csv_file_path):
        print(f"Error: File '{csv_file_path}' not found!")
        sys.exit(1)
    
    print(f"Starting migration from {csv_file_path}...")
    print(f"Skip missing FK: {skip_missing}")
    print(f"Create defaults: {create_defaults}")
    print()
    
    migrate_uploads(csv_file_path, skip_missing, create_defaults)
    print("Migration completed!")