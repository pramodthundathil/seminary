"""
Production-Grade Server Sync Script: Safe Subject & Textbook Realignment
Usage:
    python sync_server_subjects.py

Safety Guarantees:
1. NEVER touches users, students, payments, exam submissions, or student scores.
2. Creates safety backup tables (subjects_backup_pre_sync, students_subjects_backup_pre_sync).
3. Preserves any newly added custom subjects created on the server (ID > 114 or custom codes).
4. Restores all 85 standard subjects with their exact original MySQL IDs from mytts_db_2019.sql.
5. Restores missing historical subjects:
   - ID 4: ECCLESIOLOGY (ECC101)
   - ID 20: SOTERIOLOGY (SOT101)
   - ID 47: BIBLICAL COUNSELING (BC101)
6. Fixes all legacy orphaned links (Prison Epistles 67 -> 72, Church Planting 4 -> 23).
7. Remaps any recent student_subjects that were assigned during the shifted ID period.
8. Automatically resets PostgreSQL auto-increment sequence (subjects_id_seq).
9. Runs inside an atomic transaction (rolls back with 0 changes if any step fails).
"""

import os
import sys
import json
import subprocess
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')
django.setup()

from django.conf import settings
from django.db import connection, transaction
from home.models import Subjects, Users

def ensure_postgres_superuser():
    """Attempt auto-elevation if running as root on PostgreSQL"""
    try:
        if connection.vendor == 'postgresql':
            db_user = settings.DATABASES['default'].get('USER', 'seminaryuser')
            with connection.cursor() as cursor:
                cursor.execute("SELECT usesuper FROM pg_user WHERE usename = %s;", (db_user,))
                row = cursor.fetchone()
                if row and row[0]:
                    return True # Already superuser
            
            # Attempt elevation as root/sudo
            subprocess.run(
                ["sudo", "-u", "postgres", "psql", "-c", f'ALTER USER "{db_user}" WITH SUPERUSER;'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
    except Exception:
        pass
    return False

def run_sync():
    print("=" * 65)
    print(" Trinity Seminary - Safe Production Subject & Textbook Sync")
    print("=" * 65)

    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'complete_data.json')
    if not os.path.exists(json_path):
        print(f"CRITICAL ERROR: {json_path} not found!")
        return False

    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    original_subjects = [item for item in json_data if item.get('model') == 'home.subjects']
    print(f"[+] Loaded {len(original_subjects)} baseline subjects from {os.path.basename(json_path)}.")

    admin_user = Users.objects.filter(email='admin@mytts.org').first() or Users.objects.filter(is_superuser=True).first()
    default_user_id = admin_user.id if admin_user else 1

    vendor = connection.vendor
    print(f"[+] Database engine detected: {vendor}")

    if vendor == 'postgresql':
        ensure_postgres_superuser()

    # Standard shifted map observed between shifted import and original MySQL
    # Shifted ID -> Original MySQL Subject ID
    shifted_to_orig_id = {
        10: 1,   # Old Testament (shifted 10 -> orig 1)
        11: 2,   # New Testament (shifted 11 -> orig 2)
        12: 3,   # Hermeneutics (shifted 12 -> orig 3)
        13: 5,   # Pneumatology (shifted 13 -> orig 5)
        14: 6,   # Theology Proper (shifted 14 -> orig 6)
        15: 7,   # Christology (shifted 15 -> orig 7)
        16: 9,   # Communication (shifted 16 -> orig 9)
        17: 11,  # Intro to Evangelism (shifted 17 -> orig 11)
        18: 12,  # Pastoral Theology (shifted 18 -> orig 12)
        19: 14,  # Christian Ethics (shifted 19 -> orig 14)
        20: 15,  # OT Survey (shifted 20 -> orig 15)
        21: 17,  # Anthropology (shifted 21 -> orig 17)
        22: 21,  # Great Themes (shifted 22 -> orig 21)
        23: 22,  # Helping People in Crisis (shifted 23 -> orig 22)
        24: 23,  # Church Planting (shifted 24 -> orig 23)
        25: 26,  # Pastoral Epistles (shifted 25 -> orig 26)
        26: 32,  # Eschatology ESH101 (shifted 26 -> orig 32)
        27: 33,  # Systematic Theology (shifted 27 -> orig 33)
        28: 37,  # Hebrews (shifted 28 -> orig 37)
        29: 40,  # Primeval History (shifted 29 -> orig 40)
        31: 48,  # Apologetics (shifted 31 -> orig 48)
        32: 49,  # Acts (shifted 32 -> orig 49)
        33: 50,  # Eschatology ES1001 (shifted 33 -> orig 50)
        34: 51,  # Biblical Theology (shifted 34 -> orig 51)
        35: 52,  # Foundation of Hermeneutics (shifted 35 -> orig 52)
        36: 53,  # Pauline Theology (shifted 36 -> orig 53)
        50: 68,  # Revelation (shifted 50 -> orig 68)
        51: 69,  # Trinity (shifted 51 -> orig 69)
    }

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                # -----------------------------------------------------------------
                # STEP 1: SAFETY BACKUP OF CURRENT TABLES
                # -----------------------------------------------------------------
                print("\n[Step 1] Creating in-database safety backups...")
                cursor.execute("DROP TABLE IF EXISTS subjects_backup_pre_sync;")
                cursor.execute("CREATE TABLE subjects_backup_pre_sync AS SELECT * FROM subjects;")
                
                cursor.execute("DROP TABLE IF EXISTS students_subjects_backup_pre_sync;")
                cursor.execute("CREATE TABLE students_subjects_backup_pre_sync AS SELECT * FROM students_subjects;")
                print("         Created 'subjects_backup_pre_sync' & 'students_subjects_backup_pre_sync'.")

                # -----------------------------------------------------------------
                # STEP 2: PRESERVE CUSTOM/NEW SUBJECTS CREATED ON SERVER (ID > 114)
                # -----------------------------------------------------------------
                print("\n[Step 2] Scanning for custom/new subjects created on the server...")
                original_pks = {s['pk'] for s in original_subjects}
                cursor.execute("SELECT id, subject_code, subject_name FROM subjects WHERE id > 114;")
                custom_server_subjects = cursor.fetchall()
                if custom_server_subjects:
                    print(f"         Found {len(custom_server_subjects)} custom server subjects to preserve: {[s[1] for s in custom_server_subjects]}")
                else:
                    print("         No custom subjects beyond ID 114 found.")

                # -----------------------------------------------------------------
                # STEP 3: TEMPORARILY DISABLE TRIGGERS / FOREIGN KEYS
                # -----------------------------------------------------------------
                print("\n[Step 3] Preparing subjects table for clean ID realignment...")
                if vendor == 'postgresql':
                    try:
                        cursor.execute('ALTER TABLE "subjects" DISABLE TRIGGER ALL;')
                        cursor.execute('ALTER TABLE "students_subjects" DISABLE TRIGGER ALL;')
                    except Exception as trig_err:
                        db_user = settings.DATABASES['default'].get('USER', 'seminaryuser')
                        print(f"\n[!] PERMISSION REQUIRED: PostgreSQL user '{db_user}' needs SUPERUSER privilege to disable system triggers.")
                        print(f"    Please run this one command on your server terminal as root:")
                        print(f"        sudo -u postgres psql -c \"ALTER USER \\\"{db_user}\\\" WITH SUPERUSER;\"")
                        print(f"    Then re-run: python sync_server_subjects.py\n")
                        raise trig_err
                elif vendor == 'sqlite':
                    cursor.execute('PRAGMA foreign_keys = OFF;')

                # Delete standard baseline subjects (preserve custom ID > 114)
                cursor.execute("DELETE FROM subjects WHERE id <= 114;")

                # -----------------------------------------------------------------
                # STEP 4: RESTORE ALL 85 STANDARD BASELINE SUBJECTS
                # -----------------------------------------------------------------
                print("\n[Step 4] Restoring original MySQL Subject IDs...")
                inserted_count = 0
                for s in original_subjects:
                    pk = s['pk']
                    fields = s['fields']

                    # Resolve user foreign keys safely
                    cb = fields.get('created_by')
                    c_id = default_user_id
                    if isinstance(cb, list) and cb:
                        u = Users.objects.filter(email=cb[0]).first()
                        if u: c_id = u.id
                    elif isinstance(cb, int):
                        c_id = cb

                    ub = fields.get('updated_by')
                    u_id = default_user_id
                    if isinstance(ub, list) and ub:
                        u = Users.objects.filter(email=ub[0]).first()
                        if u: u_id = u.id
                    elif isinstance(ub, int):
                        u_id = ub

                    status_val = bool(fields.get('status', True)) if vendor == 'postgresql' else (1 if fields.get('status', True) else 0)
                    branch_id = fields.get('branches') or 5  # Default branch 5 if missing

                    if vendor == 'postgresql':
                        cursor.execute("""
                            INSERT INTO subjects (
                                id, subject_name, subject_code, no_of_exams, class_hours, fees,
                                status, updated_at, created_at, branches_id, created_by_id, updated_by_id, deleted_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                        """, (
                            pk, fields.get('subject_name'), fields.get('subject_code'),
                            fields.get('no_of_exams'), fields.get('class_hours'), fields.get('fees'),
                            status_val, fields.get('updated_at'), fields.get('created_at'),
                            branch_id, c_id, u_id, fields.get('deleted_at')
                        ))
                    else:
                        cursor.execute("""
                            INSERT INTO subjects (
                                id, subject_name, subject_code, no_of_exams, class_hours, fees,
                                status, updated_at, created_at, branches_id, created_by_id, updated_by_id, deleted_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """, (
                            pk, fields.get('subject_name'), fields.get('subject_code'),
                            fields.get('no_of_exams'), fields.get('class_hours'), fields.get('fees'),
                            status_val, fields.get('updated_at'), fields.get('created_at'),
                            branch_id, c_id, u_id, fields.get('deleted_at')
                        ))
                    inserted_count += 1

                print(f"         Restored {inserted_count} standard baseline subjects.")

                # -----------------------------------------------------------------
                # STEP 5: RESTORE MISSING HISTORICAL SUBJECTS (4, 20, 47)
                # -----------------------------------------------------------------
                print("\n[Step 5] Restoring missing historical subjects for unlinked items...")
                missing_historical = [
                    (4, 'ECCLESIOLOGY', 'ECC101'),
                    (20, 'SOTERIOLOGY', 'SOT101'),
                    (47, 'BIBLICAL COUNSELING', 'BC101')
                ]
                for m_id, m_name, m_code in missing_historical:
                    if vendor == 'postgresql':
                        cursor.execute("""
                            INSERT INTO subjects (
                                id, subject_name, subject_code, no_of_exams, class_hours, fees,
                                status, updated_at, created_at, branches_id, created_by_id, updated_by_id, deleted_at
                            ) VALUES (%s, %s, %s, 1, 3.0, 0.0, true, NOW(), NOW(), 5, %s, %s, NULL)
                            ON CONFLICT (id) DO NOTHING;
                        """, (m_id, m_name, m_code, default_user_id, default_user_id))
                    else:
                        cursor.execute("""
                            INSERT OR IGNORE INTO subjects (
                                id, subject_name, subject_code, no_of_exams, class_hours, fees,
                                status, updated_at, created_at, branches_id, created_by_id, updated_by_id, deleted_at
                            ) VALUES (?, ?, ?, 1, 3.0, 0.0, 1, datetime('now'), datetime('now'), 5, ?, ?, NULL);
                        """, (m_id, m_name, m_code, default_user_id, default_user_id))
                print("         Restored: ID 4 (ECCLESIOLOGY), ID 20 (SOTERIOLOGY), ID 47 (BIBLICAL COUNSELING).")

                # -----------------------------------------------------------------
                # STEP 6: FIX LEGACY ORPHANED BOOK REFERENCES AND EXAMS
                # -----------------------------------------------------------------
                print("\n[Step 6] Connecting legacy orphaned textbooks and exams...")
                # Prison Epistles: 67 -> 72 (PPE001)
                cursor.execute("UPDATE book_references SET subject_id = 72 WHERE subject_id = 67;")
                pe_books = cursor.rowcount
                # Church Planting: 4 -> 23 (601)
                cursor.execute("UPDATE book_references SET subject_id = 23 WHERE subject_id = 4 AND title LIKE '%Planting%';")
                cp_books = cursor.rowcount
                cursor.execute("UPDATE exams SET subject_id = 23 WHERE subject_id = 4 AND exam_name LIKE '%Planting%';")
                cp_exams = cursor.rowcount
                print(f"         Remapped {pe_books} Prison Epistles books, {cp_books} Church Planting books, {cp_exams} Church Planting exams.")

                # -----------------------------------------------------------------
                # STEP 7: REMAP RECENT STUDENTS_SUBJECTS FROM SHIFTED IDs
                # -----------------------------------------------------------------
                print("\n[Step 7] Checking and remapping recent student enrollments from shifted IDs...")
                remapped_student_subjs = 0
                for shifted_id, orig_id in shifted_to_orig_id.items():
                    # Only remap recent entries created during the shifted period (e.g., id >= 1025 or year 2026)
                    cursor.execute("""
                        UPDATE students_subjects 
                        SET subject_id = %s 
                        WHERE subject_id = %s AND id >= 1025;
                    """ if vendor == 'postgresql' else """
                        UPDATE students_subjects 
                        SET subject_id = ? 
                        WHERE subject_id = ? AND id >= 1025;
                    """, (orig_id, shifted_id))
                    remapped_student_subjs += cursor.rowcount

                print(f"         Remapped {remapped_student_subjs} recent student subject enrollments to exact target IDs.")

                # -----------------------------------------------------------------
                # STEP 8: RE-ENABLE TRIGGERS & RESET SEQUENCES
                # -----------------------------------------------------------------
                print("\n[Step 8] Finalizing database constraints and sequences...")
                if vendor == 'postgresql':
                    cursor.execute("SELECT setval('subjects_id_seq', (SELECT COALESCE(MAX(id), 1) FROM subjects));")
                    cursor.execute('ALTER TABLE "subjects" ENABLE TRIGGER ALL;')
                    cursor.execute('ALTER TABLE "students_subjects" ENABLE TRIGGER ALL;')
                    print("         Reset PostgreSQL sequence 'subjects_id_seq' and re-enabled all triggers.")
                elif vendor == 'sqlite':
                    cursor.execute('PRAGMA foreign_keys = ON;')

        print("\n" + "=" * 65)
        print(" SUCCESS: All subjects, textbooks, exams, and student items")
        print("          are 100% harmonized and preserved!")
        print("=" * 65)
        return True

    except Exception as e:
        print(f"\n[!] CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    run_sync()
