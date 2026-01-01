import os
import django
import sys

# Setup Django environment
sys.path.append(r'd:\USA_seminary\Updated\seminary')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seminary.settings')
django.setup()

from home.models import Students, StudentsUploads, Uploads, Videos

def check_uploads():

    print("--- Checking Uploads via Subjects ---")
    

    print("--- Checking Uploads via Subjects (Scanning all students) ---")
    
    from home.models import StudentsSubjects
    
    all_students = Students.objects.all()
    found_example = False
    
    for student in all_students:
        student_subjects = StudentsSubjects.objects.filter(student=student)
        subject_ids = student_subjects.values_list('subject_id', flat=True)
        
        if not subject_ids:
            continue
            
        # Check if there are ANY uploads for these subjects
        subject_uploads = Uploads.objects.filter(subject__id__in=subject_ids)
        if subject_uploads.count() > 0:
            print(f"\n[MATCH] Student: {student.email} ({student.first_name}) has {subject_uploads.count()} subject uploads.")
            print(f"Subjects: {list(subject_ids)}")
            
            for upload in subject_uploads:
                print(f"  [Subject Upload] ID: {upload.id}, Name: {upload.upload_name}, Subject: {upload.subject.subject_name if upload.subject else 'None'}")
                has_content = False
                if upload.youtube: 
                    print(f"    - Youtube: {upload.youtube.file_path}")
                    has_content = True
                if upload.media: 
                    print(f"    - Media: {upload.media.file_path}")
                    has_content = True
                if upload.video_id:
                     print(f"    - Video Relation: {upload.video_id}")
                     if upload.video_id.youtube: 
                        print(f"       -> Youtube: {upload.video_id.youtube.file_path}")
                        has_content = True
                     if upload.video_id.media: 
                        print(f"       -> Media: {upload.video_id.media.file_path}")
                        has_content = True
                
                if not has_content:
                    print("    [WARNING] Upload has no content linked!")
            
            found_example = True
            break
            
    if not found_example:
        print("No students found with subject-based uploads.")

if __name__ == "__main__":
    check_uploads()
