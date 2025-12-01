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
