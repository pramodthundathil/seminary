#!/usr/bin/env python3
"""
migrate_media_to_s3.py

Transfers media files uploaded after a specific cutoff date (default: September 15, 2026)
from the server's local media/ folder directly to Amazon S3 (mytts-media-s3).

Run this script directly on your production server.

Usage:
    # 1. Preview what files will be uploaded (safe dry-run):
    python migrate_media_to_s3.py --since 2026-09-15 --dry-run

    # 2. Perform the actual upload to S3:
    python migrate_media_to_s3.py --since 2026-09-15

    # 3. Check and upload ALL local student/media files currently missing on S3:
    python migrate_media_to_s3.py --all-missing
"""

import os
import sys
import argparse
import mimetypes
from datetime import datetime, timezone

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Initialize Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')
try:
    import django
    django.setup()
except Exception as e:
    print(f"Error initializing Django: {e}")
    sys.exit(1)

from django.conf import settings
from home.models import Students, MediaLibrary, AssignmentAnswers
import boto3
from botocore.exceptions import ClientError


def get_s3_client():
    key = getattr(settings, 'AWS_ACCESS_KEY_ID', os.environ.get('AWS_ACCESS_KEY_ID'))
    secret = getattr(settings, 'AWS_SECRET_ACCESS_KEY', os.environ.get('AWS_SECRET_ACCESS_KEY'))
    region = getattr(settings, 'AWS_S3_REGION_NAME', os.environ.get('AWS_S3_REGION_NAME', 'us-east-2'))
    bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', os.environ.get('AWS_STORAGE_BUCKET_NAME', 'mytts-media-s3'))

    if not key or not secret:
        print("[ERROR] AWS credentials not found in settings or .env file.")
        sys.exit(1)

    s3 = boto3.client(
        's3',
        aws_access_key_id=key,
        aws_secret_access_key=secret,
        region_name=region
    )
    return s3, bucket, region


def s3_object_exists(s3, bucket, key):
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response.get('Error', {}).get('Code') in ('404', 'NoSuchKey', '403'):
            return False
        return False
    except Exception:
        return False


def resolve_local_path(val_str, media_root):
    if not val_str:
        return None, None
    clean = str(val_str).strip().lstrip('/')
    if clean.startswith('media/'):
        clean = clean[6:]

    # Possible relative locations
    prefixes = [
        '',
        'uploads/students/',
        'uploads/certificates/1/',
        'uploads/certificates/2/',
        'uploads/certificates/3/',
        'uploads/certificates/4/',
        'uploads/certificates/5/',
        'uploads/',
        'student_photos/',
        'student_certificates/'
    ]

    for p in prefixes:
        candidate = (p + clean).replace('//', '/')
        full_candidate = os.path.join(media_root, candidate)
        if os.path.isfile(full_candidate):
            return full_candidate, candidate

    # Direct check on media_root
    direct_full = os.path.join(media_root, clean)
    if os.path.isfile(direct_full):
        return direct_full, clean

    return None, clean


def collect_database_files(cutoff_dt):
    print(f"\n[1] Querying database records created/updated on or after {cutoff_dt.strftime('%Y-%m-%d')}...")
    files_to_check = set()

    # 1. Students
    students = Students.objects.filter(created_at__gte=cutoff_dt)
    print(f"    Found {students.count()} student record(s) created since cutoff.")
    for s in students:
        for fld in ['photo', 'certificate1', 'certificate2', 'certificate3', 'certificate4', 'certificate5']:
            val = getattr(s, fld, None)
            if val:
                files_to_check.add(str(val))

    # Also check recently updated students (e.g. edited by admin)
    updated_students = Students.objects.filter(updated_at__gte=cutoff_dt).exclude(created_at__gte=cutoff_dt)
    if updated_students.exists():
        print(f"    Found {updated_students.count()} student record(s) updated since cutoff.")
        for s in updated_students:
            for fld in ['photo', 'certificate1', 'certificate2', 'certificate3', 'certificate4', 'certificate5']:
                val = getattr(s, fld, None)
                if val:
                    files_to_check.add(str(val))

    # 2. MediaLibrary
    try:
        medias = MediaLibrary.objects.filter(created_at__gte=cutoff_dt)
        print(f"    Found {medias.count()} MediaLibrary record(s) created since cutoff.")
        for m in medias:
            if m.file_path:
                files_to_check.add(str(m.file_path))
    except Exception as e:
        print(f"    [WARN] MediaLibrary query error: {e}")

    # 3. AssignmentAnswers
    try:
        answers = AssignmentAnswers.objects.filter(created_at__gte=cutoff_dt)
        print(f"    Found {answers.count()} AssignmentAnswer record(s) created since cutoff.")
        for a in answers:
            if a.answer_file:
                files_to_check.add(str(a.answer_file))
    except Exception as e:
        print(f"    [WARN] AssignmentAnswers query error: {e}")

    print(f"    Total distinct file paths found in database: {len(files_to_check)}")
    return files_to_check


def collect_disk_files(media_root, cutoff_dt, all_missing=False):
    print(f"\n[2] Scanning local server disk at: {media_root}...")
    disk_files = []
    cutoff_ts = cutoff_dt.timestamp()

    for root, dirs, files in os.walk(media_root):
        for f in files:
            if f.startswith('.') or f.endswith('.tmp'):
                continue
            full_path = os.path.join(root, f)
            try:
                mtime = os.path.getmtime(full_path)
            except OSError:
                continue

            rel_path = os.path.relpath(full_path, media_root).replace('\\', '/')

            # Include if modified after cutoff OR inside uploads/students/ OR if all_missing requested
            if all_missing or mtime >= cutoff_ts or rel_path.startswith('uploads/students/'):
                disk_files.append((full_path, rel_path, mtime))

    print(f"    Found {len(disk_files)} file(s) matching scan criteria on local disk.")
    return disk_files


def main():
    parser = argparse.ArgumentParser(description="Migrate local media files to AWS S3.")
    parser.add_argument('--since', default='2026-09-15', help="Cutoff date in YYYY-MM-DD format (default: 2026-09-15)")
    parser.add_argument('--dry-run', action='store_true', help="Preview files to upload without making changes")
    parser.add_argument('--all-missing', action='store_true', help="Scan all local media files and upload any missing from S3")
    parser.add_argument('--force', action='store_true', help="Re-upload even if object already exists in S3")
    args = parser.parse_args()

    try:
        cutoff_dt = datetime.strptime(args.since, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    except ValueError:
        print(f"[ERROR] Invalid date format for --since: {args.since}. Use YYYY-MM-DD.")
        sys.exit(1)

    s3, bucket, region = get_s3_client()
    media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(BASE_DIR, 'media'))

    print("=" * 70)
    print(" Trinity Seminary - Media to S3 Migration Utility")
    print(f" S3 Bucket:  {bucket} (region: {region})")
    print(f" Media Root: {media_root}")
    print(f" Cutoff:     {cutoff_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f" Mode:       {'DRY RUN (no uploads)' if args.dry_run else 'LIVE UPLOAD'}")
    print("=" * 70)

    # Gather files to process:
    # A. From Database records
    db_file_strings = collect_database_files(cutoff_dt)

    # B. From Server Disk
    disk_files = collect_disk_files(media_root, cutoff_dt, all_missing=args.all_missing)

    # Build queue of (full_local_path, s3_key)
    queue = {}

    # 1. Process files referenced in Database
    for db_val in db_file_strings:
        full_path, s3_key = resolve_local_path(db_val, media_root)
        if full_path and os.path.isfile(full_path):
            queue[s3_key] = full_path

    # 2. Add files found on local disk
    for full_path, rel_path, mtime in disk_files:
        if rel_path not in queue:
            queue[rel_path] = full_path

    print(f"\n[3] Total unique candidate files to evaluate: {len(queue)}")
    if not queue:
        print("    No candidate files found to migrate.")
        return

    # Check S3 status and perform upload
    to_upload = []
    already_on_s3 = 0

    print("\n[4] Checking existing objects on AWS S3...")
    for s3_key, full_path in queue.items():
        if not args.force and s3_object_exists(s3, bucket, s3_key):
            already_on_s3 += 1
        else:
            to_upload.append((s3_key, full_path))

    print(f"    Already in S3: {already_on_s3}")
    print(f"    To be uploaded to S3: {len(to_upload)}")

    if not to_upload:
        print("\n[SUCCESS] All files are already present in AWS S3! Nothing to upload.")
        return

    # Perform Upload
    print(f"\n[5] {'Planning upload (Dry Run)' if args.dry_run else 'Uploading files to AWS S3'}...")
    uploaded_count = 0
    failed_count = 0
    total_bytes = 0

    for idx, (s3_key, full_path) in enumerate(to_upload, 1):
        file_size = os.path.getsize(full_path)
        content_type, _ = mimetypes.guess_type(full_path)
        if not content_type:
            content_type = 'application/octet-stream'

        print(f"  [{idx}/{len(to_upload)}] {s3_key} ({file_size / 1024:.1f} KB, {content_type})")

        if args.dry_run:
            uploaded_count += 1
            total_bytes += file_size
            continue

        try:
            extra_args = {
                'ContentType': content_type
            }
            s3.upload_file(full_path, bucket, s3_key, ExtraArgs=extra_args)
            uploaded_count += 1
            total_bytes += file_size
            public_url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
            print(f"      -> OK: {public_url}")
        except Exception as err:
            failed_count += 1
            print(f"      -> FAILED: {err}")

    print("\n" + "=" * 70)
    print(" Summary:")
    print(f" Files successfully {'identified' if args.dry_run else 'uploaded'}: {uploaded_count}")
    print(f" Total size: {total_bytes / (1024 * 1024):.2f} MB")
    if failed_count:
        print(f" Failed: {failed_count}")
    print("=" * 70)

    if args.dry_run:
        print("\n[TIP] To actually upload these files, run without --dry-run:")
        print(f"      python migrate_media_to_s3.py --since {args.since}")


if __name__ == '__main__':
    main()
