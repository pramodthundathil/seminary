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