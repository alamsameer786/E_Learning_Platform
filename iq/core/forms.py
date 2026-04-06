from django import forms
from django.contrib.auth.models import User
from .models import AcademicNote, StudyPlan

class AcademicNoteForm(forms.ModelForm):
    class Meta:
        model = AcademicNote
        fields = ['title', 'subject', 'topic', 'content', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter note title'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Mathematics, Physics'}),
            'topic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specific topic name'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': 'Enter your academic content here...'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }

class StudyPlanForm(forms.ModelForm):
    class Meta:
        model = StudyPlan
        fields = ['title', 'description', 'target_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Plan title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe your study plan'}),
            'target_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class UserProfileForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False, min_length=8)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']