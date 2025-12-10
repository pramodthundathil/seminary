from django import forms
from .models import Students, Countries, Courses, Languages

class StudentProfileEditForm(forms.ModelForm):
    class Meta:
        model = Students
        fields = [
            'first_name', 'middle_name', 'last_name', 'email',
            'date_of_birth', 'gender', 'citizenship', 'mailing_address', 'city', 'state',
            'country', 'zip_code', 'timezone', 'highest_education', 'course_applied',
            'ministerial_status', 'church_affiliation', 'scholarship_needed',
            'currently_employed', 'income', 'affordable_amount', 'message',
            'mrital_status', 'spouse_name', 'children',
            'reference_name1', 'reference_email1', 'reference_phone1',
            'reference_name2', 'reference_email2', 'reference_phone2',
            'reference_name3', 'reference_email3', 'reference_phone3'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'citizenship': forms.Select(attrs={'class': 'form-control'}),
            'mailing_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'timezone': forms.TextInput(attrs={'class': 'form-control'}),
            'highest_education': forms.TextInput(attrs={'class': 'form-control'}),
            'course_applied': forms.Select(attrs={'class': 'form-control'}),
            'ministerial_status': forms.Select(attrs={'class': 'form-control'}),
            'church_affiliation': forms.TextInput(attrs={'class': 'form-control'}),
            'scholarship_needed': forms.Select(attrs={'class': 'form-control', 'choices': [('Yes', 'Yes'), ('No', 'No')]}),
            'currently_employed': forms.Select(attrs={'class': 'form-control', 'choices': [('Yes', 'Yes'), ('No', 'No')]}),
            'income': forms.TextInput(attrs={'class': 'form-control'}),
            'affordable_amount': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'mrital_status': forms.Select(attrs={'class': 'form-control'}),
            'spouse_name': forms.TextInput(attrs={'class': 'form-control'}),
            'children': forms.NumberInput(attrs={'class': 'form-control'}),
            'reference_name1': forms.TextInput(attrs={'class': 'form-control'}),
            'reference_email1': forms.EmailInput(attrs={'class': 'form-control'}),
            'reference_phone1': forms.TextInput(attrs={'class': 'form-control'}),
            'reference_name2': forms.TextInput(attrs={'class': 'form-control'}),
            'reference_email2': forms.EmailInput(attrs={'class': 'form-control'}),
            'reference_phone2': forms.TextInput(attrs={'class': 'form-control'}),
            'reference_name3': forms.TextInput(attrs={'class': 'form-control'}),
            'reference_email3': forms.EmailInput(attrs={'class': 'form-control'}),
            'reference_phone3': forms.TextInput(attrs={'class': 'form-control'}),
        }
