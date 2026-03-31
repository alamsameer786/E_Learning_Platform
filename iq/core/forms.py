from django import forms
from .models import AcademicNote, StudyPlan

class AcademicNoteForm(forms.ModelForm):
    class Meta:
        model = AcademicNote
        fields = ['title', 'subject', 'topic', 'content', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter note title'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Mathematics, Physics, History'}),
            'topic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specific topic name'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Enter your academic content here...'}),
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