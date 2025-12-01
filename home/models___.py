from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
# from ckeditor.fields import RichTextField
from django_ckeditor_5.fields import CKEditor5Field
from storages.backends.s3boto3 import S3Boto3Storage

s3_storage = S3Boto3Storage()


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


class Users(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=191)
    email = models.EmailField(max_length=191, unique=True)
    course_completed_email = models.CharField(max_length=250, blank=True, null=True)
    email_verified_at = models.DateTimeField(blank=True, null=True)
    username = models.CharField(max_length=250, unique=True)
    image = models.CharField(max_length=250, blank=True, null=True)
    remember_token = models.CharField(max_length=100, blank=True, null=True)
    locked_exam = models.IntegerField(blank=True, null=True)
    banned_at = models.DateTimeField(blank=True, null=True)
    church_admin_id = models.IntegerField(null=True, blank=True, db_column='church_admin_id')
    last_login = models.DateTimeField(blank=True, null=True)
    expired_at = models.DateField(blank=True, null=True)
    completed = models.BooleanField(default=0)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name']

    class Meta:
        managed = True
        db_table = 'users'


class PasswordResets(models.Model):
    email = models.CharField(max_length=191)
    token = models.CharField(max_length=191)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'password_resets'


class Payments(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=250, blank=True, null=True)
    name = models.CharField(max_length=250)
    email = models.CharField(max_length=250)
    phone = models.CharField(max_length=15, blank=True, null=True)
    person_group = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    student_id = models.IntegerField(null=True, blank=True, db_column='student_id')
    church_admin_id = models.IntegerField(null=True, blank=True, db_column='church_admin_id')
    subjects_id = models.IntegerField(blank=True, null=True, db_column='subjects_id')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'payments'


class PaymentSubjects(models.Model):
    id = models.AutoField(primary_key=True)
    payment_id = models.IntegerField(db_column='payment_id')
    subject_id = models.IntegerField(db_column='subject_id')
    amount = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'payment_subjects'


class Permissions(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=191)
    group_name = models.CharField(max_length=191)
    guard_name = models.CharField(max_length=191)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'permissions'


class PhotoGallery(models.Model):
    id = models.AutoField(primary_key=True)
    gallery_name = models.CharField(max_length=250)
    code = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    category_id = models.IntegerField(db_column='category_id')
    media_id = models.IntegerField(db_column='media_id')
    status = models.BooleanField(default=False)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'photo_gallery'


class PhotoGalleryPhotos(models.Model):
    id = models.AutoField(primary_key=True)
    photo_gallery_id = models.IntegerField(db_column='photo_gallery_id')
    media_id = models.IntegerField(db_column='media_id')
    title = models.CharField(max_length=250, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    alt_text = models.CharField(max_length=250, blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'photo_gallery_photos'


class Photos(models.Model):
    id = models.AutoField(primary_key=True)
    media_id = models.IntegerField(db_column='media_id')
    title = models.CharField(max_length=250, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    alt_text = models.CharField(max_length=250, blank=True, null=True)
    categories_id = models.IntegerField(null=True, blank=True, db_column='categories_id')
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'photos'


class Posts(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=250)
    title = models.CharField(max_length=250)
    description = models.TextField()
    browser_title = models.CharField(max_length=250, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.TextField(blank=True, null=True)
    media_id = models.IntegerField(null=True, blank=True, db_column='media_id')
    status = models.BooleanField(default=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'posts'


class Qualifications(models.Model):
    id = models.AutoField(primary_key=True)
    qualification_name = models.CharField(max_length=250)
    display_order = models.IntegerField()
    status = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')

    class Meta:
        managed = True
        db_table = 'qualifications'


class ReferenceForm(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=250)
    middle_name = models.CharField(max_length=250, blank=True, null=True)
    last_name = models.CharField(max_length=250)
    email = models.CharField(max_length=250)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    nationality = models.CharField(max_length=50)
    applicant_name = models.CharField(max_length=250)
    relation_with_applicant = models.CharField(max_length=20, blank=True, null=True)
    since_know_applicant = models.CharField(max_length=10, blank=True, null=True)
    spiritual_commitment = models.CharField(max_length=20)
    dedication_for_loard = models.CharField(max_length=20, blank=True, null=True)
    learning_capacity = models.CharField(max_length=20, blank=True, null=True)
    church_involvement = models.CharField(max_length=20, blank=True, null=True)
    leadership_skills = models.CharField(max_length=20, blank=True, null=True)
    moral_standard = models.CharField(max_length=20, blank=True, null=True)
    biblical_knowledge = models.CharField(max_length=20)
    financial_condition = models.CharField(max_length=20, blank=True, null=True)
    how_do_you_recommend = models.CharField(max_length=20, blank=True, null=True)
    personal_comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'reference_form'


class RoleHasPermissions(models.Model):
    permission_id = models.PositiveIntegerField(primary_key=True)
    role_id = models.PositiveIntegerField()

    class Meta:
        managed = True
        db_table = 'role_has_permissions'
        unique_together = (('permission_id', 'role_id'),)


## working on it......

class Sliders(models.Model):
    id = models.AutoField(primary_key=True)
    slider_name = models.CharField(max_length=250)
    code = models.CharField(max_length=250)
    width = models.SmallIntegerField()
    height = models.SmallIntegerField()
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'sliders'

class SliderPhotos(models.Model):
    id = models.AutoField(primary_key=True)
    sliders_id = models.ForeignKey("Sliders",on_delete=models.CASCADE, db_column='sliders_id', related_name='sliders_photos')
    media_id = models.ForeignKey("MediaLibrary", on_delete=models.CASCADE, db_column='media_id', related_name='sliders_media')
    title = models.CharField(max_length=250, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    alt_text = models.CharField(max_length=250, blank=True, null=True)
    button_text = models.CharField(max_length=250, blank=True, null=True)
    button_link = models.CharField(max_length=250, blank=True, null=True)
    button_link_target = models.CharField(max_length=10, blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'slider_photos'

# end of work on 13-11..................

class Staffs(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(db_column='user_id')
    staff_id = models.CharField(max_length=250, blank=True, null=True)
    staff_name = models.CharField(max_length=250)
    title = models.CharField(max_length=250)
    degree = models.CharField(max_length=250)
    email = models.CharField(max_length=250)
    phone_code = models.IntegerField(blank=True, null=True)
    phone_number = models.CharField(max_length=15)
    date_of_joining = models.DateField()
    image = models.CharField(max_length=250, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=2)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    priority = models.IntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'staffs'


class StaffsSubjects(models.Model):
    id = models.AutoField(primary_key=True)
    staff_id = models.IntegerField(db_column='staff_id')
    subject_id = models.IntegerField(db_column='subject_id')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'staffs_subjects'


class Students(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.CharField(max_length=250, blank=True, null=True)
    user_id = models.IntegerField(null=True, blank=True, db_column='user_id')
    first_name = models.CharField(max_length=250)
    middle_name = models.CharField(max_length=250, blank=True, null=True)
    last_name = models.CharField(max_length=250, blank=True, null=True)
    email = models.CharField(max_length=250, blank=True, null=True)
    course_completed_email = models.CharField(max_length=250, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    citizenship = models.IntegerField(blank=True, null=True, db_column='citizenship')
    phone_code = models.IntegerField(blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    mrital_status = models.CharField(max_length=25, blank=True, null=True)
    spouse_name = models.CharField(max_length=250, blank=True, null=True)
    children = models.IntegerField(blank=True, null=True)
    mailing_address = models.CharField(max_length=500, blank=True, null=True)
    city = models.CharField(max_length=250, blank=True, null=True)
    state = models.CharField(max_length=250, blank=True, null=True)
    country = models.IntegerField(blank=True, null=True, db_column='country')
    photo = models.CharField(max_length=205, blank=True, null=True)
    zip_code = models.CharField(max_length=15, blank=True, null=True)
    timezone = models.CharField(max_length=250)
    highest_education = models.CharField(max_length=100, blank=True, null=True)
    course_applied = models.IntegerField(blank=True, null=True, db_column='course_applied')
    associate_degree = models.IntegerField(blank=True, null=True)
    language_id = models.IntegerField(db_column='language_id')
    starting_year = models.IntegerField(blank=True, null=True)
    ministerial_status = models.CharField(max_length=50, blank=True, null=True)
    church_affiliation = models.CharField(max_length=250, blank=True, null=True)
    scholarship_needed = models.CharField(max_length=4, blank=True, null=True)
    currently_employed = models.CharField(max_length=4, blank=True, null=True)
    income = models.CharField(max_length=50, blank=True, null=True)
    affordable_amount = models.CharField(max_length=4, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    reference_email2 = models.CharField(max_length=250, blank=True, null=True)
    reference_name1 = models.CharField(max_length=250, blank=True, null=True)
    reference_email1 = models.CharField(max_length=250, blank=True, null=True)
    reference_phone1 = models.CharField(max_length=50, blank=True, null=True)
    reference_name2 = models.CharField(max_length=250, blank=True, null=True)
    reference_phone2 = models.CharField(max_length=50, blank=True, null=True)
    reference_name3 = models.CharField(max_length=250, blank=True, null=True)
    reference_email3 = models.CharField(max_length=250, blank=True, null=True)
    reference_phone3 = models.CharField(max_length=50, blank=True, null=True)
    certificate1 = models.CharField(max_length=250, blank=True, null=True)
    certificate2 = models.CharField(max_length=250, blank=True, null=True)
    certificate3 = models.CharField(max_length=250, blank=True, null=True)
    certificate4 = models.CharField(max_length=250, blank=True, null=True)
    certificate5 = models.CharField(max_length=250, blank=True, null=True)
    approve_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=False)
    active = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'students'
        unique_together = (('course_applied', 'user_id'),)


class StudentsAssignment(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.IntegerField(db_column='student_id')
    assignment_id = models.IntegerField(db_column='assignment_id')
    submission_date = models.DateTimeField(blank=True, null=True)
    submitted_on = models.DateTimeField(blank=True, null=True)
    total_marks = models.FloatField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'students_assignment'


class StudentsBooks(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.IntegerField(db_column='student_id')
    book_id = models.IntegerField(db_column='book_id')
    updated_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'students_books'


class StudentsExams(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.IntegerField(db_column='student_id')
    exam_id = models.IntegerField(db_column='exam_id')
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    exam_duration = models.IntegerField()
    timezone = models.CharField(max_length=50)
    requested_by = models.IntegerField(blank=True, null=True, db_column='requested_by')
    is_approved = models.BooleanField(default=False)
    reject_reason = models.TextField(blank=True, null=True)
    is_exam_started = models.BooleanField(default=False)
    is_exam_ended = models.BooleanField(default=False)
    show_on_score = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'students_exams'


class StudentsInstructor(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.IntegerField(db_column='student_id')
    instructor_id = models.IntegerField(db_column='instructor_id')
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'students_instructor'


class StudentsSubjects(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.IntegerField(db_column='student_id')
    subject_id = models.IntegerField(db_column='subject_id')
    requested_by = models.IntegerField(blank=True, null=True, db_column='requested_by')
    is_approved = models.BooleanField(default=False)
    reject_reason = models.TextField(blank=True, null=True)
    is_optional = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'students_subjects'


class StudentsUploads(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.IntegerField(db_column='student_id')
    upload_id = models.IntegerField(db_column='upload_id')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'students_uploads'


class Subjects(models.Model):
    id = models.AutoField(primary_key=True)
    branches_id = models.IntegerField(db_column='branches_id')
    subject_name = models.CharField(max_length=250)
    subject_code = models.CharField(max_length=250)
    no_of_exams = models.IntegerField()
    class_hours = models.DecimalField(max_digits=10, decimal_places=2)
    fees = models.FloatField(blank=True, null=True)
    status = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')

    class Meta:
        managed = True
        db_table = 'subjects'


class Support(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.IntegerField(db_column='student_id')
    doubt_question = models.CharField(max_length=1000)
    doubt_answer = models.CharField(max_length=1000)
    category = models.CharField(max_length=50)
    subjects_id = models.IntegerField(null=True, blank=True, db_column='subjects_id')
    status = models.CharField(max_length=1)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'support'


class SupportReplies(models.Model):
    id = models.AutoField(primary_key=True)
    support_id = models.IntegerField(db_column='support_id')
    doubt_answer = models.CharField(max_length=1000)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'support_replies'


class Tags(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=250)
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    status = models.BooleanField(default=True, blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'tags'


class Uploads(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=250)
    upload_name = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    format = models.CharField(max_length=5)
    video_id = models.IntegerField(blank=True, null=True, db_column='video_id')
    youtube_id = models.IntegerField(null=True, blank=True, db_column='youtube_id')
    aws_url = models.CharField(max_length=250, blank=True, null=True)
    subject_id = models.IntegerField(db_column='subject_id')
    media_id = models.IntegerField(null=True, blank=True, db_column='media_id')
    status = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')

    class Meta:
        managed = True
        db_table = 'uploads'


class Videos(models.Model):
    id = models.AutoField(primary_key=True)
    media_id = models.IntegerField(null=True, blank=True, db_column='media_id')
    youtube_id = models.IntegerField(null=True, blank=True, db_column='youtube_id')
    title = models.CharField(max_length=250, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    categories_id = models.IntegerField(null=True, blank=True, db_column='categories_id')
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'videos'


class WpDb7Forms(models.Model):
    form_id = models.BigAutoField(primary_key=True)
    form_post_id = models.BigIntegerField()
    form_value = models.TextField()
    form_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'wp_db7_forms'


class WpPosts(models.Model):
    id = models.BigAutoField(db_column='ID', primary_key=True)
    post_author = models.PositiveBigIntegerField()
    post_date = models.DateTimeField()
    post_date_gmt = models.DateTimeField()
    post_content = models.TextField()
    post_title = models.TextField()
    post_excerpt = models.TextField()
    post_status = models.CharField(max_length=20)
    comment_status = models.CharField(max_length=20)
    ping_status = models.CharField(max_length=20)
    post_password = models.CharField(max_length=20)
    post_name = models.CharField(max_length=200)
    to_ping = models.TextField()
    pinged = models.TextField()
    post_modified = models.DateTimeField()
    post_modified_gmt = models.DateTimeField()
    post_content_filtered = models.TextField()
    post_parent = models.PositiveBigIntegerField()
    guid = models.CharField(max_length=255)
    menu_order = models.IntegerField()
    post_type = models.CharField(max_length=20)
    post_mime_type = models.CharField(max_length=100)
    comment_count = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'wp_posts'


class YoutubeVideos(models.Model):
    id = models.AutoField(primary_key=True)
    file_path = models.CharField(max_length=250)
    thumb_file_path = models.CharField(max_length=250)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'youtube_videos'


# ============================================================================
# USAGE NOTES:
# ============================================================================
# All ForeignKey fields have been converted to IntegerField for direct 
# database mapping without Django ORM relationship management.
#
# To query related objects manually:
# 
# Example 1: Get subject from assignment
#   assignment = Assignments.objects.get(id=1)
#   subject = Subjects.objects.get(id=assignment.subject_id)
#
# Example 2: Get user from student
#   student = Students.objects.get(id=1)
#   if student.user_id:
#       user = Users.objects.get(id=student.user_id)
#
# Example 3: Get all assignments for a subject
#   subject_id = 5
#   assignments = Assignments.objects.filter(subject_id=subject_id)
#
# Example 4: Get created_by user
#   assignment = Assignments.objects.get(id=1)
#   creator = Users.objects.get(id=assignment.created_by)
#
# This approach gives you full control over queries and works seamlessly
# with existing databases without requiring Django migrations.
# ============================================================================
    _table = 'users'

    def __str__(self):
        return f'{self.username} ({self.email})'


class RoleUsers(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(Users,on_delete=models.CASCADE,db_column='user_id', related_name='user_roles')
    role_id = models.ForeignKey("Roles",on_delete=models.CASCADE,db_column='role_id', related_name="role_user")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'role_users'
        unique_together = (('user_id', 'role_id'),)


class Roles(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=191)
    guard_name = models.CharField(max_length=191)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'roles'


class AdminPages(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=250)
    slug = models.CharField(max_length=250)
    permission = models.CharField(max_length=250)
    target = models.CharField(max_length=10, blank=True, null=True)
    icon = models.CharField(max_length=50)
    parent_id = models.IntegerField(null=True, blank=True, db_column='parent_id')
    menu_order = models.IntegerField(default=0)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'admin_pages'

    def __str__(self):
        return f'{self.title} - order {self.menu_order}'


class Assignments(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=250)
    subject_id = models.IntegerField(db_column='subject_id')
    assignment_name = models.CharField(max_length=250)
    assignment_type = models.CharField(max_length=250)
    total_score = models.SmallIntegerField()
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')

    class Meta:
        managed = True
        db_table = 'assignments'


class AssignmentAnswers(models.Model):
    id = models.AutoField(primary_key=True)
    assignment_id = models.IntegerField(db_column='assignment_id')
    student_id = models.IntegerField(db_column='student_id')
    answer_file = models.CharField(max_length=255, blank=True, null=True)
    answer_text = models.TextField(blank=True, null=True)
    marks_optained = models.FloatField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'assignment_answers'


class AssignmentQuestions(models.Model):
    id = models.AutoField(primary_key=True)
    assignment_id = models.IntegerField(db_column='assignment_id')
    question = models.TextField()
    mark = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')

    class Meta:
        managed = True
        db_table = 'assignment_questions'


class Bans(models.Model):
    id = models.AutoField(primary_key=True)
    bannable_type = models.CharField(max_length=191)
    bannable_id = models.PositiveBigIntegerField()
    created_by_type = models.CharField(max_length=191, blank=True, null=True)
    created_by_id = models.PositiveBigIntegerField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    expired_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bans'


class Books(models.Model):
    id = models.AutoField(primary_key=True)
    book_name = models.CharField(max_length=250)
    auther_name = models.CharField(max_length=250)
    course_id = models.IntegerField(db_column='course_id')
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'books'


class BookReferences(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=250)
    title = models.CharField(max_length=250)
    auther_name = models.CharField(max_length=250, blank=True, null=True)
    subject_id = models.IntegerField(db_column='subject_id')
    format = models.CharField(max_length=5)
    reference_file = models.CharField(max_length=250, blank=True, null=True)
    reference_note = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')

    class Meta:
        managed = True
        db_table = 'book_references'


class Branches(models.Model):
    id = models.AutoField(primary_key=True)
    branch_name = models.CharField(max_length=250)
    branch_code = models.CharField(max_length=250)
    is_associate_degree = models.IntegerField()
    status = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')

    class Meta:
        managed = True
        db_table = 'branches'


class Categories(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=250)
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    parent_id = models.IntegerField()
    type = models.CharField(max_length=50)
    media_id = models.IntegerField(null=True, blank=True, db_column='media_id')
    table_color = models.CharField(max_length=50, blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'categories'


class ChurchAdmins(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.IntegerField(null=True, blank=True, db_column='student_id')
    name_of_church = models.CharField(max_length=250, blank=True, null=True)
    name_of_paster = models.CharField(max_length=250, blank=True, null=True)
    church_address = models.TextField(blank=True, null=True)
    church_code_id = models.IntegerField()
    code = models.CharField(max_length=250)
    amount = models.FloatField()
    max_user_no = models.IntegerField()
    current_user_no = models.IntegerField()
    renewed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'church_admins'


class ChurchLoginCodeSettings(models.Model):
    id = models.AutoField(primary_key=True)
    branches_id = models.IntegerField(db_column='branches_id')
    name = models.CharField(max_length=250)
    max_user_no = models.IntegerField()
    amount = models.FloatField()
    expired_in_days = models.TextField()
    status = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'church_login_code_settings'


class Contacts(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=250, blank=True, null=True)
    email = models.CharField(max_length=250, blank=True, null=True)
    subject = models.CharField(max_length=250, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'contacts'


class Countries(models.Model):
    id = models.AutoField(primary_key=True)
    sortname = models.CharField(max_length=3)
    name = models.CharField(max_length=150)
    phonecode = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'countries'


class Courses(models.Model):
    id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=250)
    course_code = models.CharField(max_length=250)
    highest_qualification = models.IntegerField(db_column='highest_qualification')
    credit_hours = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    browser_title = models.CharField(max_length=250, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.TextField(blank=True, null=True)
    media_id = models.IntegerField(null=True, blank=True, db_column='media_id')
    status = models.IntegerField()
    apply_button_top = models.BooleanField(default=True)
    apply_button_bottom = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')

    class Meta:
        managed = True
        db_table = 'courses'


class DescriptiveAnswers(models.Model):
    id = models.AutoField(primary_key=True)
    assignment_id = models.IntegerField(db_column='assignment_id')
    question_id = models.IntegerField(db_column='question_id')
    answer = models.TextField(blank=True, null=True)
    mark = models.DecimalField(max_digits=10, decimal_places=0)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'descriptive_answers'


class DescriptiveQuestions(models.Model):
    id = models.AutoField(primary_key=True)
    exam_id = models.IntegerField(db_column='exam_id')
    question = models.TextField()
    mark = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')

    class Meta:
        managed = True
        db_table = 'descriptive_questions'


class Exams(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=250)
    subject_id = models.IntegerField(db_column='subject_id')
    exam_name = models.CharField(max_length=250)
    exam_type = models.CharField(max_length=20)
    status = models.BooleanField(default=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')

    class Meta:
        managed = True
        db_table = 'exams'


class HomeSettings(models.Model):
    id = models.AutoField(primary_key=True)
    section_group = models.CharField(max_length=250)
    code = models.CharField(max_length=250)
    content = models.TextField(blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'home_settings'


class Languages(models.Model):
    id = models.AutoField(primary_key=True)
    language_name = models.CharField(max_length=250)
    status = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')

    class Meta:
        managed = True
        db_table = 'languages'


class MediaLibrary(models.Model):
    id = models.AutoField(primary_key=True)
    file_name = models.TextField()
    file_path = models.FileField(
        storage=s3_storage,
        upload_to='uploads/',
        max_length=250,
        db_column='file_path',
    )
    thumb_file_path = models.CharField(max_length=250)
    slider_file_path = models.CharField(max_length=250, blank=True, null=True)
    file_type = models.CharField(max_length=100)
    file_size = models.CharField(max_length=100)
    dimensions = models.CharField(max_length=50, blank=True, null=True)
    media_type = models.CharField(max_length=120)
    title = models.CharField(max_length=250, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    alt_text = models.CharField(max_length=250, blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'media_library'


class Menus(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=250)
    code = models.CharField(max_length=250)
    menu_position = models.CharField(max_length=20, choices=(('header', 'header'), ('footer', "footer")))
    status = models.BooleanField(default=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'menus'


class MenuItems(models.Model):
    id = models.AutoField(primary_key=True)
    menus_id = models.IntegerField(db_column='menus_id')
    title = models.CharField(max_length=250)
    url = models.CharField(max_length=250, blank=True, null=True)
    pages_id = models.IntegerField(null=True, blank=True, db_column='pages_id')
    menu_type = models.CharField(max_length=50, blank=True, null=True)
    menu_order = models.IntegerField()
    parent_id = models.IntegerField(db_column='parent_id')
    target_blank = models.BooleanField(default=False)
    original_title = models.CharField(max_length=250, blank=True, null=True)
    menu_nextable_id = models.CharField(max_length=250, blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'menu_items'


class Migrations(models.Model):
    id = models.AutoField(primary_key=True)
    migration = models.CharField(max_length=191)
    batch = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'migrations'


class ModelHasPermissions(models.Model):
    permission_id = models.PositiveIntegerField(primary_key=True)
    model_type = models.CharField(max_length=191)
    model_id = models.PositiveBigIntegerField()

    class Meta:
        managed = False
        db_table = 'model_has_permissions'
        unique_together = (('permission_id', 'model_id', 'model_type'),)


class ModelHasRoles(models.Model):
    role_id = models.PositiveIntegerField(primary_key=True)
    model_type = models.CharField(max_length=191)
    model_id = models.PositiveBigIntegerField()

    class Meta:
        managed = False
        db_table = 'model_has_roles'
        unique_together = (('role_id', 'model_id', 'model_type'),)


class News(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=250)
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    browser_title = models.CharField(max_length=250, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.TextField(blank=True, null=True)
    media_id = models.IntegerField(null=True, blank=True, db_column='media_id')
    status = models.BooleanField(default=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'news'


class Notifications(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.IntegerField(db_column='student_id')
    notification_type = models.CharField(max_length=50)
    message = models.CharField(max_length=250)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'notifications'


class ObjectiveAnswers(models.Model):
    id = models.AutoField(primary_key=True)
    assignment_id = models.IntegerField(db_column='assignment_id')
    question_id = models.IntegerField(db_column='question_id')
    answer = models.CharField(max_length=250, blank=True, null=True)
    mark = models.DecimalField(max_digits=10, decimal_places=0)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'objective_answers'


class ObjectiveQuestions(models.Model):
    id = models.AutoField(primary_key=True)
    exam_id = models.IntegerField(db_column='exam_id')
    question = models.CharField(max_length=500)
    option1 = models.CharField(max_length=250, blank=True, null=True)
    option2 = models.CharField(max_length=250, blank=True, null=True)
    option3 = models.CharField(max_length=250, blank=True, null=True)
    option4 = models.CharField(max_length=250, blank=True, null=True)
    answer_option = models.CharField(max_length=10)
    answer = models.CharField(max_length=250, blank=True, null=True)
    marks = models.DecimalField(max_digits=10, decimal_places=2)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')

    class Meta:
        managed = True
        db_table = 'objective_questions'


class PageMediaLibrary(models.Model):
    id = models.AutoField(primary_key=True)
    pages_id = models.IntegerField(db_column='pages_id')
    media_id = models.IntegerField(db_column='media_id')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'page_media_library'


class PageSettings(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=250)
    browser_title = models.CharField(max_length=250, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.TextField(blank=True, null=True)
    status = models.BooleanField(default=True)
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'page_settings'


class Pages(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=250)
    title = models.CharField(max_length=250)
    description = CKEditor5Field(blank=True, null=True)
    browser_title = models.CharField(max_length=250, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.TextField(blank=True, null=True)
    media_id = models.IntegerField(null=True, blank=True, db_column='media_id')
    video_id = models.IntegerField(null=True, blank=True, db_column='video_id')
    youtube_id = models.IntegerField(null=True, blank=True, db_column='youtube_id')
    status = models.IntegerField(blank=True, null=True)
    apply_button_top = models.BooleanField(default=False)
    apply_button_bottom = models.BooleanField(default=False)
    parent_id = models.IntegerField(null=True, blank=True, db_column='parent_id')
    created_by = models.IntegerField(db_column='created_by')
    updated_by = models.IntegerField(db_column='updated_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'pages'