# This is a refined Django models module based on the provided SQL dump.
# I've compared the SQL schema with the auto-generated models and made the following fixes:
# - Added missing 'id' fields where they were omitted (e.g., primary keys as AutoField or specified explicitly).
# - Converted integer-based foreign key references to proper Django ForeignKey fields with on_delete (using CASCADE where specified in SQL constraints, or SET_NULL/DO_NOTHING where appropriate based on SQL).
# - Ensured primary_key=True where applicable.
# - Handled unique keys and auto-increment appropriately (using AutoField for ids).
# - Fixed field types (e.g., mediumint -> IntegerField, tinyint -> SmallIntegerField where it makes sense, but kept IntegerField for simplicity unless specified).
# - Added db_column where field names differ (rare here).
# - Kept managed=False for all models since this is for an existing database.
# - Added unique_together where SQL has composite unique keys.
# - For fields like 'updated_at' with DEFAULT current_timestamp(), you can add auto_now=True if you want Django to handle it, but since managed=False, it's optional.
# - Removed redundant 'unique=True' on AutoField ids (implied by primary_key).
# - Ensured all fields match SQL types (e.g., varchar(250) -> CharField(max_length=250), text -> TextField).
# - For composite primary keys (e.g., ModelHasPermissions), used primary_key=True on the first field and unique_together.
# - Ignored engine-specific details like MyISAM, COLLATE (not relevant in Django models).
# - Later, to migrate data: Use Django's dumpdata to export from one DB and loaddata to import, or use SQL dumps directly since managed=False.

from django.db import models

from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
# from ckeditor.fields import RichTextField
from django_ckeditor_5.fields import CKEditor5Field


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
    church_admin = models.ForeignKey('ChurchAdmins', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    last_login = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    expired_at = models.DateField(blank=True, null=True)
    completed = models.BooleanField(default=0)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    # Django auth-related fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Custom manager
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name']

    class Meta:
        managed = True  # ✅ because the table already exists
        db_table = 'users'
        ordering = ['name']

    def __str__(self):
        return f'{self.username or ""} ({self.email or ""})'

    def check_password(self, raw_password):
        import bcrypt
        if self.password and (self.password.startswith('$2y$') or self.password.startswith('$2a$') or self.password.startswith('$2b$')):
            try:
                hashed = self.password
                if hashed.startswith('$2y$'):
                    hashed = hashed.replace('$2y$', '$2b$', 1)
                if bcrypt.checkpw(raw_password.encode('utf-8'), hashed.encode('utf-8')):
                    return True
            except Exception:
                pass
        return super().check_password(raw_password)




class RoleUsers(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey('Roles', on_delete=models.DO_NOTHING, related_name="role_user")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'role_users'
        unique_together = (('user', 'role'),)

    def __str__(self):
        return f"{self.user or ''} - {self.role or ''}"

class Roles(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=191)
    guard_name = models.CharField(max_length=191)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)


    class Meta:
        managed = True
        db_table = 'roles'
        ordering = ['name']

    def __str__(self):
        return str(self.name or "")

# class Users(models.Model):
#     id = models.AutoField(primary_key=True)
#     name = models.CharField(max_length=191)
#     email = models.CharField(max_length=191)
#     course_completed_email = models.CharField(max_length=250, blank=True, null=True)
#     email_verified_at = models.DateTimeField(blank=True, null=True)
#     password = models.CharField(max_length=191)
#     username = models.CharField(max_length=250)
#     image = models.CharField(max_length=250, blank=True, null=True)
#     remember_token = models.CharField(max_length=100, blank=True, null=True)
#     locked_exam = models.IntegerField(blank=True, null=True)
#     banned_at = models.DateTimeField(blank=True, null=True)
#     church_admin = models.ForeignKey('ChurchAdmins', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
#     expired_at = models.DateField(blank=True, null=True)
#     completed = models.IntegerField()
#     created_at = models.DateTimeField(blank=True, null=True)
#     updated_at = models.DateTimeField(blank=True, null=True)
#     deleted_at = models.DateTimeField(blank=True, null=True)

#     class Meta:
#         managed = False
#         db_table = 'users'

#     def __str__(self):
#         return f'{self.username} -name: {self.password}' 


class AdminPages(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=250)
    slug = models.CharField(max_length=250)
    permission = models.CharField(max_length=250)
    target = models.CharField(max_length=10, blank=True, null=True)
    icon = models.CharField(max_length=50)
    parent = models.ForeignKey('AdminPages', on_delete=models.SET_NULL, null=True, blank=True)
    menu_order = models.IntegerField(default=0)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name='admin_page')
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name='admin_page_update')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'admin_pages'
        ordering = ['title']
    def __str__(self):
        return f'{self.title or ""} - order {self.menu_order or 0}'  

class Assignments(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=250)
    subject = models.ForeignKey("Subjects", on_delete=models.CASCADE)
    assignment_name = models.CharField(max_length=250)
    assignment_type = models.CharField(
        max_length=250,
        choices=(
            ('paper_upload', 'Paper Upload type'),
            ('paper_submit', 'Paper Submit type'),
        )
    )
    total_score = models.SmallIntegerField()
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="assignment_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="assignment_updated")
    deleted_at = models.DateTimeField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'assignments'
        ordering = ['assignment_name']

    def __str__(self):
        return str(self.assignment_name or "")

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Auto-populate assignment code to ID
        if not self.code or self.code == "":
            self.code = str(self.id)
            super().save(update_fields=['code'])
            
        if is_new:
            # Auto-assign to already approved students of the same subject
            from home.models import StudentsSubjects, StudentsAssignment
            from datetime import timedelta
            from django.utils import timezone
            
            approved_students = StudentsSubjects.objects.filter(
                subject=self.subject,
                is_approved=True,
                deleted_at__isnull=True
            ).select_related('student')
            
            one_year_span = timezone.now() + timedelta(days=365)
            
            for ss in approved_students:
                if not StudentsAssignment.objects.filter(student=ss.student, assignment=self, deleted_at__isnull=True).exists():
                    assigned_by = self.updated_by or self.created_by
                    if not assigned_by:
                        assigned_by = ss.student.user
                    
                    StudentsAssignment.objects.create(
                        student=ss.student,
                        assignment=self,
                        submission_date=one_year_span,
                        created_by=assigned_by,
                        updated_by=assigned_by
                    )

class AssignmentAnswers(models.Model):
    id = models.AutoField(primary_key=True)
    assignment = models.ForeignKey('Assignments', on_delete=models.DO_NOTHING, related_name='answers')
    student = models.ForeignKey('Students', on_delete=models.DO_NOTHING, related_name='assignment_answers')
    question = models.ForeignKey('AssignmentQuestions', on_delete=models.SET_NULL, blank=True, null=True, related_name='answers')
    answer_file = models.FileField(upload_to="uploads/assignments/", blank=True, null=True)
    answer_text = models.TextField(blank=True, null=True)
    marks_optained = models.FloatField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'assignment_answers'

    def __str__(self):
        return f"Answer for {self.assignment or ''}"

class AssignmentQuestions(models.Model):
    id = models.AutoField(primary_key=True)
    assignment = models.ForeignKey('Assignments', on_delete=models.DO_NOTHING, related_name='questions')
    question = models.TextField()
    mark = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="assignment_questions_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="assignment_questions_updated")

    class Meta:
        managed = True
        db_table = 'assignment_questions'

    def __str__(self):
        return str(self.question[:50] or "")

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
        managed = True
        db_table = 'bans'

    def __str__(self):
        return f"{self.bannable_type or ''} - {self.id}"

class Books(models.Model):
    id = models.AutoField(primary_key=True)
    book_name = models.CharField(max_length=250)
    auther_name = models.CharField(max_length=250)
    course = models.ForeignKey('Courses', on_delete=models.DO_NOTHING, related_name='books')
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'books'
        ordering = ['book_name']

    def __str__(self):
        return str(self.book_name or "")

class BookReferences(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=250)
    title = models.CharField(max_length=250)
    auther_name = models.CharField(max_length=250, blank=True, null=True)
    subject = models.ForeignKey('Subjects', on_delete=models.DO_NOTHING, related_name='references')
    format = models.CharField(
        max_length=5,
        choices=(
            ('PDF', 'PDF'),
            ('note', 'Note'),
        )
    )
    reference_file = models.ForeignKey("MediaLibrary", on_delete=models.DO_NOTHING, blank=True, null=True)
    reference_note = CKEditor5Field(blank=True, null=True)
    description = CKEditor5Field(blank=True, null=True)
    status = models.BooleanField(default=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="book_reference_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="book_reference_updated")
    deleted_at = models.DateTimeField(blank=True, null=True)


    class Meta:
        managed = True
        db_table = 'book_references'
        ordering = ['title']

    def __str__(self):
        return str(self.title or "")

class Branches(models.Model):
    id = models.AutoField(primary_key=True)
    branch_name = models.CharField(max_length=250)
    branch_code = models.CharField(max_length=250)
    is_associate_degree = models.BooleanField(default=False)
    status = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="branches_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="branches_updated")

    deleted_at = models.DateTimeField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'branches'
        ordering = ['branch_name']

    def __str__(self):
        return f"{str(self.branch_name or '')} - {str(self.branch_code or '')}"

class Categories(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=250)
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    parent_id = models.IntegerField()
    type = models.CharField(max_length=50)
    media = models.ForeignKey('MediaLibrary', on_delete=models.SET_NULL, null=True, blank=True, related_name='categories')
    table_color = models.CharField(max_length=50, blank=True, null=True)
    status = models.BooleanField(default=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="categories_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="categories_updated")

    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'categories'
        ordering = ['name']

    def __str__(self):
        return str(self.name or "")

class ChurchAdmins(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey('Students', on_delete=models.SET_NULL, null=True, blank=True, related_name='church_admins')
    name_of_church = models.CharField(max_length=250, blank=True, null=True)
    name_of_paster = models.CharField(max_length=250, blank=True, null=True)
    church_address = models.TextField(blank=True, null=True)
    church_code = models.ForeignKey('ChurchLoginCodeSettings', on_delete=models.DO_NOTHING, db_column='church_code_id', related_name='church_admins')
    code = models.CharField(max_length=250)
    amount = models.FloatField()
    max_user_no = models.IntegerField()
    current_user_no = models.IntegerField()
    is_paid = models.BooleanField(default=False)
    renewed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'church_admins'
        ordering = ['name_of_church']

    def __str__(self):
        return str(self.name_of_church or "")

class ChurchAdminApplication(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey('Students', on_delete=models.CASCADE, related_name='church_admin_applications')
    name_of_church = models.CharField(max_length=250)
    name_of_pastor = models.CharField(max_length=250, null=True, blank=True)
    church_address = models.TextField(null=True, blank=True)
    church_code_settings = models.ForeignKey('ChurchLoginCodeSettings', on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        default='pending'
    )
    rejection_reason = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'church_admin_applications'

    def __str__(self):
        return f"Application by {self.student.first_name} {self.student.last_name} for {self.name_of_church}"

class ChurchLoginCodeSettings(models.Model):
    id = models.AutoField(primary_key=True)
    branches = models.ForeignKey('Branches', on_delete=models.DO_NOTHING, related_name='code_settings')
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
        ordering = ['name']

    def __str__(self):
        return str(self.name or "")

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

    def __str__(self):
        return str(self.name or self.email or "Contact")

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
        ordering = ['name']
    
    def __str__(self):
        return str(self.name or "")

class Courses(models.Model):
    id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=250)
    course_code = models.CharField(max_length=250)
    highest_qualification = models.ForeignKey('Qualifications', on_delete=models.DO_NOTHING)
    credit_hours = models.DecimalField(max_digits=10, decimal_places=2)
    fees = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    description = CKEditor5Field(blank=True, null=True)
    browser_title = models.CharField(max_length=250, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.TextField(blank=True, null=True)
    media = models.ForeignKey('MediaLibrary', on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    status = models.IntegerField()
    apply_button_top = models.BooleanField(default=True)
    apply_button_bottom = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="course_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="course_updated")
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'courses'
        ordering = ['course_name']
    def __str__(self):
        return str(self.course_name or "")

class DescriptiveAnswers(models.Model):
    id = models.AutoField(primary_key=True)
    assignment = models.ForeignKey('StudentsExams', on_delete=models.DO_NOTHING, related_name='descriptive_answers')
    question = models.ForeignKey('DescriptiveQuestions', on_delete=models.DO_NOTHING, related_name='answers')
    answer = models.TextField(blank=True, null=True)
    mark = models.DecimalField(max_digits=10, decimal_places=0)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'descriptive_answers'

    def __str__(self):
        return f"Answer for {self.question or ''}"

class DescriptiveQuestions(models.Model):
    id = models.AutoField(primary_key=True)
    exam = models.ForeignKey('Exams', on_delete=models.DO_NOTHING, related_name='descriptive_questions')
    question = models.TextField()
    mark = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="descriptive_questions_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="descriptive_questions_updated")


    class Meta:
        managed = True
        db_table = 'descriptive_questions'

    def __str__(self):
        return str(self.question[:50] or "")

class Exams(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=250)
    subject = models.ForeignKey('Subjects', on_delete=models.DO_NOTHING, related_name='exams')
    exam_name = models.CharField(max_length=250)
    exam_type = models.CharField(
        max_length=20,
        choices=(
            ('descriptive', 'Descriptive'),
            ('objective', 'Objective'),
        )
    )
    status = models.BooleanField(default=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="exams_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="exams_updated")
    deleted_at = models.DateTimeField(blank=True, null=True)


    class Meta:
        managed = True
        db_table = 'exams'
        ordering = ['exam_name']

    def __str__(self):
        return str(self.exam_name or "")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.code or self.code == "":
            self.code = str(self.id)
            super().save(update_fields=['code'])

class HomeSettings(models.Model):
    id = models.AutoField(primary_key=True)
    section_group = models.CharField(max_length=250)
    code = models.CharField(max_length=250)
    content = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="home_settings_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="home_settings_updated")

    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'home_settings'

    def __str__(self):
        return str(self.section_group or "")

class Languages(models.Model):
    id = models.AutoField(primary_key=True)
    language_name = models.CharField(max_length=250)
    status = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="language_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="language_updated")
    deleted_at = models.DateTimeField(blank=True, null=True)


    class Meta:
        managed = True
        db_table = 'languages'
        ordering = ['language_name']

    def __str__(self):
        return str(self.language_name or "")

# from storages.backends.s3boto3 import S3Boto3Storage

# s3_storage = S3Boto3Storage()   

class MediaLibrary(models.Model):
    id = models.AutoField(primary_key=True)
    file_name = models.TextField()
     
    file_path = models.FileField(
        
        upload_to='uploads/',     # base path (can be empty if Laravel already used 'uploads/')
        
        db_column='file_path',    # critical! keep mapping to same DB column
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
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="media_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="media_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'media_library'

    def __str__(self):
        return f"{str(self.file_name or '')} - file {self.file_type or ''}"

class Menus(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=250)
    code = models.CharField(max_length=250)
    menu_position = models.CharField(max_length=20, choices=(('header','header'),('footer',"footer")))
    status = models.BooleanField(default=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="menu_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="menu_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'menus'
        ordering = ['name']

    def __str__(self):
        return str(self.name or "")

class MenuItems(models.Model):
    id = models.AutoField(primary_key=True)
    menus = models.ForeignKey(Menus, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=250)
    url = models.CharField(max_length=250, blank=True, null=True)
    pages = models.ForeignKey('Pages', on_delete=models.CASCADE, null=True, blank=True, related_name='menu_items')
    menu_type = models.CharField(max_length=50, blank=True, null=True)
    menu_order = models.IntegerField()
    parent_id = models.ForeignKey("MenuItems", on_delete=models.CASCADE,null=True, blank=True, related_name="sub_menu")
    target_blank = models.BooleanField(default=False)
    original_title = models.CharField(max_length=250, blank=True, null=True)
    menu_nextable_id = models.CharField(max_length=250, blank=True, null=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="menu_item_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="menu_item_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'menu_items'
        ordering = ['title']

    def __str__(self):
        return str(self.title or "")

class Migrations(models.Model):
    id = models.AutoField(primary_key=True)
    migration = models.CharField(max_length=191)
    batch = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'migrations'

class ModelHasPermissions(models.Model):
    permission_id = models.PositiveIntegerField(primary_key=True)
    model_type = models.CharField(max_length=191)
    model_id = models.PositiveBigIntegerField()

    class Meta:
        managed = True
        db_table = 'model_has_permissions'
        unique_together = (('permission_id', 'model_id', 'model_type'),)

class ModelHasRoles(models.Model):
    role_id = models.PositiveIntegerField(primary_key=True)
    model_type = models.CharField(max_length=191)
    model_id = models.PositiveBigIntegerField()

    class Meta:
        managed = True
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
    media = models.ForeignKey('MediaLibrary', on_delete=models.SET_NULL, null=True, blank=True, related_name='news')
    status = models.BooleanField(default=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="news_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="news_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'news'
        ordering = ['title']

    def __str__(self):
        return str(self.title or "")

class Notifications(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey('Students', on_delete=models.DO_NOTHING, related_name='notifications')
    notification_type = models.CharField(max_length=50)
    message = models.CharField(max_length=250)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'notifications'

    def __str__(self):
        return str(self.message[:50] or "")

class ObjectiveAnswers(models.Model):
    id = models.AutoField(primary_key=True)
    assignment = models.ForeignKey('StudentsExams', on_delete=models.DO_NOTHING, related_name='objective_answers')
    question = models.ForeignKey('ObjectiveQuestions', on_delete=models.DO_NOTHING, related_name='answers')
    answer = models.CharField(max_length=250, blank=True, null=True)
    mark = models.DecimalField(max_digits=10, decimal_places=0)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'objective_answers'

    def __str__(self):
        return f"Answer for {self.question or ''}"


# --------------------------------------------
# --------------------------------------------
# -------------------------------------------- 


class ObjectiveQuestions(models.Model):
    id = models.AutoField(primary_key=True)
    exam = models.ForeignKey('Exams', on_delete=models.DO_NOTHING, related_name='objective_questions')
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
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="objective_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="objective_updated")


    class Meta:
        managed = True
        db_table = 'objective_questions'

    def __str__(self):
        return str(self.question[:50] or "")

class PageMediaLibrary(models.Model):
    id = models.AutoField(primary_key=True)
    pages = models.ForeignKey('Pages', on_delete=models.CASCADE, related_name='media_libraries')
    media = models.ForeignKey(MediaLibrary, on_delete=models.CASCADE, related_name='page_media')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'page_media_library'

    def __str__(self):
        return f"Media for {self.pages or ''}"

class PageSettings(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=250)
    browser_title = models.CharField(max_length=250, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.TextField(blank=True, null=True)
    status = models.BooleanField(default=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="page_setting_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="page_setting_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'page_settings'

    def __str__(self):
        return str(self.code or "")

class Pages(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=250)
    title = models.CharField(max_length=250)
    description = CKEditor5Field(blank=True, null=True)
    browser_title = models.CharField(max_length=250, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.TextField(blank=True, null=True)
    media = models.ForeignKey(MediaLibrary, on_delete=models.SET_NULL, null=True, blank=True, related_name='pages_media')
    video = models.ForeignKey(MediaLibrary, on_delete=models.SET_NULL, null=True, blank=True, related_name='pages_video')
    youtube = models.ForeignKey('YoutubeVideos', on_delete=models.SET_NULL, null=True, blank=True, related_name='pages_youtube')
    status = models.IntegerField(blank=True, null=True)
    apply_button_top = models.BooleanField(default=False)
    apply_button_bottom = models.BooleanField(default=False)
    parent_id = models.ForeignKey("Pages", on_delete=models.SET_NULL, null=True, blank=True, related_name='parent_page')
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="page_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="page_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'pages'
        ordering = ['title']
    
    def __str__(self):
        return str(self.title or "")

class PasswordResets(models.Model):
    email = models.CharField(max_length=191)
    token = models.CharField(max_length=191)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'password_resets'

    def __str__(self):
        return str(self.email or "")

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
    student = models.ForeignKey('Students', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    church_admin = models.ForeignKey(ChurchAdmins, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_payments')
    subjects_id = models.ForeignKey("Subjects", on_delete=models.SET_NULL,blank=True, null=True, related_name='subject_paid')  # Not a FK in SQL, kept as IntegerField
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'payments'

    def __str__(self):
        return f"{self.code or ''} - {self.amount or 0}"

class PaymentSubjects(models.Model):
    id = models.AutoField(primary_key=True)
    payment = models.ForeignKey(Payments, on_delete=models.DO_NOTHING, related_name='subjects')
    subject = models.ForeignKey('Subjects', on_delete=models.DO_NOTHING, related_name='payments')
    amount = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'payment_subjects'

    def __str__(self):
        return f"{self.payment or ''} - {self.subject or ''}"

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

    def __str__(self):
        return str(self.name or "")

class PhotoGallery(models.Model):
    id = models.AutoField(primary_key=True)
    gallery_name = models.CharField(max_length=250)
    code = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Categories, on_delete=models.DO_NOTHING, related_name='photo_galleries')
    media = models.ForeignKey(MediaLibrary, on_delete=models.DO_NOTHING, related_name='photo_galleries')
    status = models.BooleanField(default=False)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="photo_gallery_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="photo_gallery_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'photo_gallery'

    def __str__(self):
        return str(self.gallery_name or "")

class PhotoGalleryPhotos(models.Model):
    id = models.AutoField(primary_key=True)
    photo_gallery = models.ForeignKey(PhotoGallery, on_delete=models.DO_NOTHING, related_name='photos')
    media = models.ForeignKey(MediaLibrary, on_delete=models.DO_NOTHING, related_name='gallery_photos')
    title = models.CharField(max_length=250, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    alt_text = models.CharField(max_length=250, blank=True, null=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="photo_gallery_photo_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="photo_gallery_photo_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'photo_gallery_photos'

    def __str__(self):
        return str(self.title or "Photo")

class Photos(models.Model):
    id = models.AutoField(primary_key=True)
    media = models.ForeignKey(MediaLibrary, on_delete=models.DO_NOTHING, related_name='photos')
    title = models.CharField(max_length=250, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    alt_text = models.CharField(max_length=250, blank=True, null=True)
    categories = models.ForeignKey(Categories, on_delete=models.SET_NULL, null=True, blank=True, related_name='photos')
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="photos_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="photos_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'photos'

    def __str__(self):
        return str(self.title or "Photo")

class Posts(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=250)
    title = models.CharField(max_length=250)
    description = models.TextField()
    browser_title = models.CharField(max_length=250, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.TextField(blank=True, null=True)
    media = models.ForeignKey(MediaLibrary, on_delete=models.CASCADE, null=True, blank=True, related_name='posts')
    status = models.BooleanField(default=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="posts_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="posts_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'posts'

    def __str__(self):
        return str(self.title or "")

class Qualifications(models.Model):
    id = models.AutoField(primary_key=True)
    qualification_name = models.CharField(max_length=250)
    display_order = models.IntegerField()
    status = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="qualification_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="qualification_updated")


    class Meta:
        managed = True
        db_table = 'qualifications'
        ordering = ['qualification_name']

    def __str__(self):
        return str(self.qualification_name or "")

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

    def __str__(self):
        return f"{self.first_name or ''} {self.last_name or ''}"

class RoleHasPermissions(models.Model):
    id = models.AutoField(primary_key=True)
    permission = models.ForeignKey(Permissions, on_delete=models.CASCADE)
    role = models.ForeignKey(Roles, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'role_has_permissions'
        unique_together = (('permission', 'role'),)

class SliderPhotos(models.Model):
    id = models.AutoField(primary_key=True)
    sliders = models.ForeignKey('Sliders', on_delete=models.CASCADE, related_name='photos')
    media = models.ForeignKey(MediaLibrary, on_delete=models.CASCADE, related_name='slider_photos')
    title = models.CharField(max_length=250, blank=True, null=True)
    description = CKEditor5Field(blank=True, null=True)
    alt_text = models.CharField(max_length=250, blank=True, null=True)
    button_text = models.CharField(max_length=250, blank=True, null=True)
    button_link = models.CharField(max_length=250, blank=True, null=True)
    button_link_target = models.CharField(max_length=10, blank=True, null=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="slider_photos_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="slider_photos_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'slider_photos'

    def __str__(self):
        return str(self.title or "Slider Photo")

class Sliders(models.Model):
    id = models.AutoField(primary_key=True)
    slider_name = models.CharField(max_length=250)
    code = models.CharField(max_length=250)
    width = models.SmallIntegerField()
    height = models.SmallIntegerField()
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="sliders_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="sliders_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'sliders'
        ordering = ['slider_name']

    def __str__(self):
        return str(self.slider_name or "")


import random
import string

class Staffs(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('Users', on_delete=models.DO_NOTHING, related_name='staffs')
    staff_id = models.CharField(max_length=250, blank=True, null=True)
    staff_name = models.CharField(max_length=250)
    title = models.CharField(max_length=250)
    degree = models.CharField(max_length=250)
    email = models.CharField(max_length=250)
    phone_code = models.IntegerField(blank=True, null=True)
    phone_number = models.CharField(max_length=15)
    date_of_joining = models.DateField()
    image = models.FileField(upload_to="Uploads/staffs/", blank=True, null=True)
    description = CKEditor5Field(blank=True, null=True)
    status = models.BooleanField(default=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="staff_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="staff_gallery_updated")

    priority = models.IntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'staffs'
        ordering = ['staff_name']

    def save(self, *args, **kwargs):
        """Auto-generate staff_id if not exists"""
        if not self.staff_id:
            self.staff_id = self.generate_staff_id()
        super().save(*args, **kwargs)

    def generate_staff_id(self):
        """Generate unique staff ID: TTSTECH{YY}{5 random alphanumeric}"""
        year = timezone.now().strftime('%y')  # Get last 2 digits of year
        
        while True:
            # Generate 5 random alphanumeric characters (uppercase)
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            staff_id = f"TTSTECH{year}{random_part}"
            
            # Check if this ID already exists
            if not Staffs.objects.filter(staff_id=staff_id).exists():
                return staff_id

    def __str__(self):
        return str(self.staff_name or "")

class StaffsSubjects(models.Model):
    id = models.AutoField(primary_key=True)
    staff = models.ForeignKey(Staffs, on_delete=models.CASCADE, related_name='subjects')
    subject = models.ForeignKey('Subjects', on_delete=models.CASCADE, related_name='staffs')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="staff_subject_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="staff_subject_updated")

    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'staffs_subjects'

    def __str__(self):
        return f"{self.staff or ''} - {self.subject or ''}"

class Students(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.CharField(max_length=250, blank=True, null=True)
    user = models.ForeignKey('Users', on_delete=models.SET_NULL, null=True, blank=True, related_name='student')
    first_name = models.CharField(max_length=250)
    middle_name = models.CharField(max_length=250, blank=True, null=True)
    last_name = models.CharField(max_length=250, blank=True, null=True)
    email = models.CharField(max_length=250, blank=True, null=True)
    course_completed_email = models.CharField(max_length=250, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    citizenship = models.ForeignKey(Countries,on_delete=models.SET_NULL,blank=True, null=True, related_name='student_citizen',db_column='citizenship')
    phone_code = models.IntegerField(blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    mrital_status = models.CharField(max_length=25, blank=True, null=True)
    spouse_name = models.CharField(max_length=250, blank=True, null=True)
    children = models.IntegerField(blank=True, null=True)
    mailing_address = models.CharField(max_length=500, blank=True, null=True)
    city = models.CharField(max_length=250, blank=True, null=True)
    state = models.CharField(max_length=250, blank=True, null=True)
    country = models.ForeignKey(Countries,on_delete=models.SET_NULL,blank=True, null=True, related_name='student_country', db_column='country')
    photo = models.CharField(max_length=205, blank=True, null=True)
    zip_code = models.CharField(max_length=15, blank=True, null=True)
    timezone = models.CharField(max_length=250)
    highest_education = models.CharField(max_length=100, blank=True, null=True)
    course_applied = models.ForeignKey(Courses,on_delete = models.SET_NULL, blank=True, null=True, db_column='course_applied')
    associate_degree = models.IntegerField(blank=True, null=True)
    language = models.ForeignKey(Languages, on_delete=models.DO_NOTHING, related_name='students', db_column='language_id')
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
    certificate1 = models.FileField(upload_to="uploads/certificates/1/", blank=True, null=True)
    certificate2 = models.FileField(upload_to="uploads/certificates/2/", blank=True, null=True)
    certificate3 = models.FileField(upload_to="uploads/certificates/3/", blank=True, null=True)
    certificate4 = models.FileField(upload_to="uploads/certificates/4/", blank=True, null=True)
    certificate5 = models.FileField(upload_to="uploads/certificates/5/", blank=True, null=True)
    approve_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=False)
    active = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'students'
        unique_together = (('course_applied', 'user'),)
        ordering = ['first_name']

    def __str__(self):
        return f"{self.first_name or ''} {self.last_name or ''}"

    def get_full_name(self):
        """Returns the student's full name"""
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        if self.last_name:
            parts.append(self.last_name)
        return ' '.join(parts)

    def get_course_fee_at_registration(self):
        """Get the frozen course fee at the time of student registration"""
        p_reg = self.payments.filter(subjects_id__isnull=True, deleted_at__isnull=True).order_by('created_at').first()
        if p_reg:
            import re
            if p_reg.message and "Discount applied:" in p_reg.message:
                match = re.search(r'Original:\s*\$?([0-9.]+)', p_reg.message)
                if match:
                    return float(match.group(1))
            return float(p_reg.amount or 0)
        return float(self.course_applied.fees or 0) if self.course_applied else 0.0

    def get_discount(self):
        """Calculate the total discount applied to this student from payments messages"""
        import re
        discount = 0.0
        payments = self.payments.filter(deleted_at__isnull=True)
        for p in payments:
            if p.message and "Discount applied:" in p.message:
                match = re.search(r'Original:\s*\$?([0-9.]+)', p.message)
                if match:
                    original_amount = float(match.group(1))
                    discount += max(0.0, original_amount - float(p.amount or 0))
        return discount

    def get_balance_due(self):
        """Calculate outstanding balance due for this student"""
        course_fee = self.get_course_fee_at_registration()
        
        # Calculate subject fees
        from home.models import StudentsSubjects
        subjects = StudentsSubjects.objects.filter(student=self, deleted_at__isnull=True)
        subject_fees_total = sum(float(ss.subject.fees or 0) for ss in subjects if ss.subject)
        
        total_fee_expected = course_fee + subject_fees_total
        discount = self.get_discount()
        
        # Calculate paid amount
        payments = self.payments.filter(deleted_at__isnull=True)
        total_paid = sum(float(p.amount or 0) for p in payments if p.is_paid)
        
        balance = total_fee_expected - discount - total_paid
        return max(0.0, balance)


class StudentsAssignment(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Students, on_delete=models.CASCADE, related_name='assignments')
    assignment = models.ForeignKey(Assignments, on_delete=models.DO_NOTHING, related_name='student_assignments')
    submission_date = models.DateTimeField(blank=True, null=True)
    submitted_on = models.DateTimeField(blank=True, null=True)
    total_marks = models.FloatField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="student_assignments_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="student_assignments_updated")

    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'students_assignment'

    def __str__(self):
        return f"{self.student or ''} - {self.assignment or ''}"

class StudentsBooks(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Students, on_delete=models.CASCADE, related_name='books')
    book = models.ForeignKey(BookReferences, on_delete=models.DO_NOTHING, related_name='students')
    is_approved = models.BooleanField(default=False)
    requested_by = models.ForeignKey(Users, on_delete=models.SET_NULL, blank=True, null=True, related_name='book_requested')
    updated_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="student_books_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="student_books_updated")

    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'students_books'

    def __str__(self):
        return f"{self.student or ''} - {self.book or ''}"

   

class StudentsExams(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Students, on_delete=models.CASCADE, related_name='exams')
    course = models.ForeignKey('Courses', on_delete=models.SET_NULL, null=True, blank=True, related_name='student_exams')
    subject = models.ForeignKey('Subjects', on_delete=models.SET_NULL, null=True, blank=True, related_name='student_exams')
    exam = models.ForeignKey(Exams, on_delete=models.DO_NOTHING, related_name='students')
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    exam_duration = models.IntegerField()
    timezone = models.CharField(max_length=50)
    requested_by = models.ForeignKey(Users,on_delete=models.SET_NULL, blank=True, null=True, related_name='exam_requested')
    is_approved = models.BooleanField(default=False)
    is_rescheduled = models.BooleanField(default=False)
    reject_reason = models.TextField(blank=True, null=True)
    is_exam_started = models.BooleanField(default=False)
    is_exam_ended = models.BooleanField(default=False)
    show_on_score = models.IntegerField()
    attempt_number = models.IntegerField(default=1)
    is_retest = models.BooleanField(default=False)
    retest_status = models.CharField(
        max_length=20,
        choices=[
            ('none', 'None'),
            ('pending', 'Pending Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        default='none'
    )
    retest_requested_at = models.DateTimeField(blank=True, null=True)
    retest_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    retest_paid = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="student_exams_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="student_exams_updated")

    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'students_exams'

    def __str__(self):
        return f"{self.student or ''} - {self.exam or ''}"

class StudentsInstructor(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Students, on_delete=models.CASCADE, related_name='instructors')
    subject = models.ForeignKey('Subjects', on_delete=models.CASCADE, related_name='student_instructors', null=True, blank=True)
    instructor = models.ForeignKey(Staffs, on_delete=models.CASCADE, related_name='students')
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="instructor_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="instructor_updated")

    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'students_instructor'

    def __str__(self):
        return f"{self.student or ''} - {self.instructor or ''}"

class StudentsSubjects(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Students, on_delete=models.CASCADE, related_name='subjects')
    subject = models.ForeignKey('Subjects', on_delete=models.DO_NOTHING, related_name='students')
    requested_by = models.ForeignKey(Users, on_delete=models.SET_NULL,blank=True, null=True, related_name='subject_requested')
    is_approved = models.BooleanField(default=False)
    reject_reason = models.TextField(blank=True, null=True)
    is_optional = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="student_subject_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="student_subject_updated")

    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'students_subjects'

    def __str__(self):
        return f"{self.student or ''} - {self.subject or ''}"

    def save(self, *args, **kwargs):
        is_approved_changed = False
        if self.pk:
            try:
                old_instance = StudentsSubjects.objects.get(pk=self.pk)
                if self.is_approved and not old_instance.is_approved:
                    is_approved_changed = True
            except StudentsSubjects.DoesNotExist:
                pass
        else:
            if self.is_approved:
                is_approved_changed = True

        super().save(*args, **kwargs)

        if is_approved_changed:
            from home.models import BookReferences, StudentsBooks, Assignments, StudentsAssignment
            from datetime import timedelta
            from django.utils import timezone

            # Auto-assign Books when subject is approved
            books = BookReferences.objects.filter(subject=self.subject, status=True)
            for book in books:
                assigned_by = self.updated_by or self.created_by or getattr(self.student, 'user', None)
                if not assigned_by:
                    assigned_by = Users.objects.filter(is_superuser=True).first() or Users.objects.first()
                StudentsBooks.objects.get_or_create(
                    student=self.student,
                    book=book,
                    defaults={
                        'created_by': assigned_by,
                        'updated_by': assigned_by
                    }
                )

            # Auto-assign Assignments when subject is approved
            assignments = Assignments.objects.filter(subject=self.subject, deleted_at__isnull=True)
            one_year_span = timezone.now() + timedelta(days=365)
            for assignment in assignments:
                if not StudentsAssignment.objects.filter(student=self.student, assignment=assignment, deleted_at__isnull=True).exists():
                    assigned_by = self.updated_by or self.created_by or getattr(self.student, 'user', None)
                    if not assigned_by:
                        assigned_by = Users.objects.filter(is_superuser=True).first() or Users.objects.first()
                    StudentsAssignment.objects.create(
                        student=self.student,
                        assignment=assignment,
                        submission_date=one_year_span,
                        created_by=assigned_by,
                        updated_by=assigned_by
                    )

class StudentsUploads(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Students, on_delete=models.CASCADE, related_name='uploads')
    upload = models.ForeignKey('Uploads', on_delete=models.CASCADE, related_name='students')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="students_upload_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="students_upload_updated")

    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'students_uploads'

    def __str__(self):
        return f"{self.student or ''} - {self.upload or ''}"

class Subjects(models.Model):
    id = models.AutoField(primary_key=True)
    branches = models.ForeignKey(Branches, on_delete=models.DO_NOTHING, related_name='subjects')
    subject_name = models.CharField(max_length=250)
    subject_code = models.CharField(max_length=250)
    no_of_exams = models.IntegerField()
    class_hours = models.DecimalField(max_digits=10, decimal_places=2)
    fees = models.FloatField(blank=True, null=True)
    status = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="subject_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="subject_updated")

    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'subjects'
        ordering = ['subject_name']

    def __str__(self):
        return str(self.subject_name or "")

class Support(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Students, on_delete=models.CASCADE, related_name='supports')
    doubt_question = models.CharField(max_length=1000)
    doubt_answer = models.CharField(max_length=1000)
    category = models.CharField(max_length=50)
    subjects = models.ForeignKey(Subjects, on_delete=models.SET_NULL, null=True, blank=True, related_name='supports')

    status = models.CharField(
        max_length=20,
        choices=[
            ('open', 'Open'),
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
        ],
        default='open'
    )

    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="support_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="support_updated")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'support'

    def __str__(self):
        return str(self.doubt_question[:50] or "")

class SupportReplies(models.Model):
    id = models.AutoField(primary_key=True)
    support = models.ForeignKey(Support, on_delete=models.CASCADE, related_name='replies')
    doubt_answer = models.CharField(max_length=1000)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="support_replay_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="support_replay_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'support_replies'

    def __str__(self):
        return str(self.doubt_answer[:50] or "")

class Tags(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=250)
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    status = models.BooleanField(default=True,blank=True, null=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="tags_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="tags_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'tags'
        ordering = ['name']

    def __str__(self):
        return str(self.name or "")

class Uploads(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=250)
    upload_name = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    format = models.CharField(max_length=5)
    video_id = models.ForeignKey('Videos', on_delete=models.SET_NULL,blank=True, null=True, related_name='video_uploads')  # Assuming not FK, as no constraint
    youtube = models.ForeignKey('YoutubeVideos', on_delete=models.SET_NULL, null=True, blank=True, related_name='uploads')
    aws_url = models.CharField(max_length=250, blank=True, null=True)
    subject = models.ForeignKey(Subjects, on_delete=models.DO_NOTHING, related_name='uploads')
    media = models.ForeignKey(MediaLibrary, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploads')
    status = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="uploads_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="uploads_updated")


    class Meta:
        managed = True
        db_table = 'uploads'
        ordering = ['upload_name']

    def __str__(self):
        return str(self.upload_name or "")


class Videos(models.Model):
    id = models.AutoField(primary_key=True)
    media = models.ForeignKey(MediaLibrary, on_delete=models.CASCADE, null=True, blank=True, related_name='videos')
    youtube = models.ForeignKey('YoutubeVideos', on_delete=models.CASCADE, null=True, blank=True, related_name='videos')
    title = models.CharField(max_length=250, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    categories = models.ForeignKey(Categories, on_delete=models.CASCADE, null=True, blank=True, related_name='videos')
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="videos_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="videos_updated")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'videos'
        ordering = ['title']

    def __str__(self):
        return str(self.title or "")

class WpDb7Forms(models.Model):
    form_id = models.BigAutoField(primary_key=True)
    form_post_id = models.BigIntegerField()
    form_value = models.TextField()
    form_date = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'wp_db7_forms'

    def __str__(self):
        return str(self.form_id)

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
        managed = True
        db_table = 'wp_posts'

    def __str__(self):
        return str(self.post_title or "")

class YoutubeVideos(models.Model):
    id = models.AutoField(primary_key=True)
    file_path = models.CharField(max_length=250)
    thumb_file_path = models.CharField(max_length=250)
    created_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="youtube_created")
    updated_by = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="youtube_updated")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'youtube_videos'

    def __str__(self):
        return str(self.file_path or "")