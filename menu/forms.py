from django import forms
from home.models import Menus, News, MediaLibrary

class MenuForm(forms.ModelForm):
    STATUS_CHOICES = (
        (1, 'Enabled'),
        (0, 'Disabled'),
    )
    
    POSITION_CHOICES = (
        ('header', 'Header'),
        ('footer', 'Footer'),
        ('sidebar', 'Sidebar'),
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    menu_position = forms.ChoiceField(
        choices=POSITION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Menus
        fields = ['name', 'code', 'menu_position', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter menu name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter menu code'}),
        }




class NewsForm(forms.ModelForm):
    STATUS_CHOICES = (
        (1, 'Active'),
        (0, 'Inactive'),
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    media = forms.ModelChoiceField(
        queryset=MediaLibrary.objects.filter(deleted_at__isnull=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Media"
    )
    
    class Meta:
        model = News
        fields = [
            'code', 'title', 'description', 'browser_title',
            'meta_description', 'meta_keywords', 'media', 'status'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter unique code (e.g., news-2025-01)'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter news title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Enter news description'
            }),
            'browser_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter browser title (SEO)'
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter meta description (SEO)'
            }),
            'meta_keywords': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter keywords separated by commas'
            }),
        }
        
    def clean_code(self):
        code = self.cleaned_data.get('code')
        # Check if code already exists (excluding current instance in edit mode)
        existing = News.objects.filter(code=code, deleted_at__isnull=True)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise forms.ValidationError('This code already exists. Please use a unique code.')
        return code


class MediaLibraryForm(forms.ModelForm):
    file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*,video/*,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx'
        })
    )
    
    class Meta:
        model = MediaLibrary
        fields = ['title', 'description', 'alt_text']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter media title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter description'
            }),
            'alt_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter alt text for accessibility'
            }),
        }


# forms.py
from django import forms
from home.models import Categories, MediaLibrary


class BootstrapModelForm(forms.ModelForm):
    """
    Base form to add Bootstrap 'form-control' and id attributes to fields.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            # Don't apply form-control to checkboxes (like BooleanField)
            if not isinstance(field.widget, forms.CheckboxInput):
                existing_class = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = (existing_class + ' form-control').strip()
            # Ensure an id is present
            field.widget.attrs.setdefault('id', f'id_{name}')


class CategoryForm(BootstrapModelForm):
    class Meta:
        model = Categories
        fields = [
            'code',
            'name',
            'description',
            'parent_id',
            'type',
            'media',        # existing media dropdown
            'table_color',
            'status',
        ]
        widgets = {
            # You can customize any particular widget if needed
            'description': forms.Textarea(attrs={'rows': 3}),
        }



from home.models import Videos, YoutubeVideos, MediaLibrary

class VideoForm(forms.ModelForm):
    class Meta:
        model = Videos
        fields = ['title', 'description', 'categories']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter video title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter video description',
                'rows': 4
            }),
            'categories': forms.Select(attrs={
                'class': 'form-control'
            })
        }

class YoutubeVideoForm(forms.ModelForm):
    class Meta:
        model = YoutubeVideos
        fields = ['file_path', 'thumb_file_path']
        widgets = {
            'file_path': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter YouTube video URL or embed code'
            }),
            'thumb_file_path': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter thumbnail URL (optional)'
            })
        }
        labels = {
            'file_path': 'YouTube URL',
            'thumb_file_path': 'Thumbnail URL'
        }


from django import forms
from home.models import Pages, MediaLibrary, YoutubeVideos

class PageForm(forms.ModelForm):
    STATUS_CHOICES = (
        (1, 'Active'),
        (0, 'Inactive'),
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    media_lib = forms.ModelChoiceField(
        queryset=MediaLibrary.objects.filter(deleted_at__isnull=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Media"
    )
    
    video = forms.ModelChoiceField(
        queryset=MediaLibrary.objects.filter(deleted_at__isnull=True, media_type='video'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Video"
    )
    
    youtube = forms.ModelChoiceField(
        queryset=YoutubeVideos.objects.filter(deleted_at__isnull=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select YouTube Video"
    )
    
    parent_id = forms.ModelChoiceField(
        queryset=Pages.objects.filter(deleted_at__isnull=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="No Parent (Top Level)"
    )
    
    class Meta:
        model = Pages
        fields = [
            'code', 'title', 'browser_title','description',
            'meta_description', 'meta_keywords', 'media_lib', 'video', 'youtube',
            'status', 'apply_button_top', 'apply_button_bottom', 'parent_id'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter unique code (e.g., about-us)'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter page title'
            }),
            'browser_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter browser title (SEO)'
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter meta description (SEO)'
            }),
            'meta_keywords': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter keywords separated by commas'
            }),
            'apply_button_top': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'apply_button_bottom': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        
    def clean_code(self):
        code = self.cleaned_data.get('code')
        existing = Pages.objects.filter(code=code, deleted_at__isnull=True)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise forms.ValidationError('This code already exists. Please use a unique code.')
        return code
    

#language form



from home.models import Languages

class LanguageForm(forms.ModelForm):
    class Meta:
        model = Languages
        fields = [
            'language_name',
            
        ]  # id, created_by, updated_by removed

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add form-control class
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})



from home.models import Subjects

class SubjectsForm(forms.ModelForm):
    class Meta:
        model = Subjects
        fields = [
            "branches",
            "subject_name",
            "subject_code",
            "no_of_exams",
            "class_hours",
            "fees",
            "status",
        ]  # id, created_by, updated_by excluded

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add Bootstrap form-control class for all fields
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ != "CheckboxInput":  # Avoid checkbox styling
                field.widget.attrs.update({'class': 'form-control'})



from home.models import Branches

class BranchesForm(forms.ModelForm):
    class Meta:
        model = Branches
        fields = [
            'branch_name',
            'branch_code',
            'is_associate_degree',
            'status',
           
        ]

        widgets = {
            'branch_name': forms.TextInput(attrs={'class': 'form-control'}),
            'branch_code': forms.TextInput(attrs={'class': 'form-control'}),
            'is_associate_degree': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
        }



from home.models import Exams

class ExamsForm(forms.ModelForm):
    class Meta:
        model = Exams
        fields = [
            'code',
            'subject',
            'exam_name',
            'exam_type',
            'status',
        ]

        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter exam code'
            }),
            'subject': forms.Select(attrs={
                'class': 'form-control'
            }),
            'exam_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter exam name'
            }),
            'exam_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

from home.models import Assignments

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignments
        fields = [
            "code",
            "subject",
            "assignment_name",
            "assignment_type",
            "total_score",
        ]

        widgets = {
            "code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter assignment code"
            }),
            "subject": forms.Select(attrs={
                "class": "form-control"
            }),
            "assignment_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter assignment name"
            }),
            "assignment_type": forms.Select(attrs={
                "class": "form-control",
                "placeholder": "Enter assignment type"
            }),
            "total_score": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter total score"
            }),
        }



from home.models import Staffs
from django_ckeditor_5.widgets import CKEditor5Widget  # make sure django-ckeditor-5 is installed

class StaffForm(forms.ModelForm):
    class Meta:
        model = Staffs
        fields = [
            
            "staff_name",
            "title",
            "degree",
            "email",
            "phone_code",
            "phone_number",
            "date_of_joining",
            "image",
            "description",
            "status",
            "priority",
        ]

        widgets = {
            
            "staff_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter staff name",
            }),
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter title (eg. Professor, Lecturer)",
            }),
            "degree": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter degree (eg. PhD, M.Tech)",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Enter email address",
            }),
            "phone_code": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Country code (eg. 91)",
            }),
            "phone_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter phone number",
            }),
            "date_of_joining": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "image": forms.FileInput(attrs={
                "class": "form-control",
                "placeholder": "Image path / URL",
            }),
           
            # "status": forms.BooleanField(attrs={
            #     "class": "form-control",
            #     "placeholder": "Status (eg. A / I)",
            # }),
            "priority": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Priority (optional)",
            }),
        }



from home.models import BookReferences, MediaLibrary

from django.utils.text import slugify


class BookReferenceForm(forms.ModelForm):

    STATUS_CHOICES = (
        (True, "Active"),
        (False, "Inactive"),
    )

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"})
    )
    
    # Hidden field to store selected media ID
    selected_media_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "selected_media_id"})
    )
    
    # File upload field for new PDF
    new_pdf_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            "class": "form-control",
            "accept": "application/pdf",
            "style": "display:none;"
        }),
        label="Upload New PDF"
    )

    class Meta:
        model = BookReferences
        fields = [
            "title",
            "code",
            "auther_name",
            "subject",
            "format",
            "reference_note",
            "description",
            "status",
        ]

        widgets = {
            "code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Auto-generated from title",
                "readonly": "readonly"
            }),
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter book title",
                "id": "id_title"
            }),
            "auther_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter author name"
            }),
            "subject": forms.Select(attrs={
                "class": "form-control"
            }),
            "format": forms.Select(attrs={
                "class": "form-control",
                "id": "id_format"
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        format_type = cleaned_data.get('format')
        
        # Validate based on format
        if format_type == 'PDF':
            new_file = cleaned_data.get('new_pdf_file')
            selected_media = cleaned_data.get('selected_media_id')
            
            if not new_file and not selected_media and not self.instance.reference_file_id:
                raise forms.ValidationError(
                    "Please either upload a new PDF or select an existing one from media library."
                )
        elif format_type == 'note':
            reference_note = cleaned_data.get('reference_note')
            if not reference_note:
                raise forms.ValidationError(
                    "Please provide reference note content."
                )
        
        return cleaned_data
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title:
            # Auto-generate code from title
            self.cleaned_data['code'] = slugify(title)
        return title
    



from home.models import Roles

class RolesForm(forms.ModelForm):
    class Meta:
        model = Roles
        fields = ["name", "guard_name", "status"]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter role name"
            }),
            "guard_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter guard name"
            }),
            "status": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }



from home.models import Uploads

class UploadForm(forms.ModelForm):
    class Meta:
        model = Uploads
        fields = [
            "code",
            "upload_name",
            "description",
            "format",
            "video_id",
            "youtube",
            "aws_url",
            "subject",
            "media",
            "status",
        ]

        widgets = {
            "code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter upload code"
            }),
            "upload_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter upload name"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter description (optional)"
            }),
            "format": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. mp4, pdf, docx"
            }),
            "video_id": forms.Select(attrs={
                "class": "form-control"
            }),
            "youtube": forms.Select(attrs={
                "class": "form-control"
            }),
            "aws_url": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "AWS file URL (optional)"
            }),
            "subject": forms.Select(attrs={
                "class": "form-control"
            }),
            "media": forms.Select(attrs={
                "class": "form-control"
            }),
            "status": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }

from home.models import ChurchLoginCodeSettings, ChurchAdmins

class ChurchLoginCodeSettingsForm(forms.ModelForm):
    STATUS_CHOICES = (
        (1, 'Active'),
        (0, 'Inactive'),
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ChurchLoginCodeSettings
        fields = [
            "branches",
            "name",
            "max_user_no",
            "amount",
            "expired_in_days",
            "status",
        ]
        
        widgets = {
            "branches": forms.Select(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter code name"}),
            "max_user_no": forms.NumberInput(attrs={"class": "form-control"}),
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
            "expired_in_days": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 365"}),
        }

class ChurchAdminForm(forms.ModelForm):
    church_code_id = forms.ModelChoiceField(
        queryset=ChurchLoginCodeSettings.objects.filter(deleted_at__isnull=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Church Code",
        label="Church Login Code"
    )

    class Meta:
        model = ChurchAdmins
        fields = [
            "name_of_church",
            "name_of_paster",
            "church_address",
            "church_code_id",
            "amount",
            "max_user_no",
        ]
        
        widgets = {
            "name_of_church": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter church name"}),
            "name_of_paster": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter pastor name"}),
            "church_address": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Enter address"}),
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
            "max_user_no": forms.NumberInput(attrs={"class": "form-control"}),
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('church_code_id'):
             instance.church_code_id = self.cleaned_data['church_code_id'].id
        
        if commit:
            instance.save()
        return instance
