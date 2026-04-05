from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class AcademicNote(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    file = models.FileField(upload_to='notes/', blank=True, null=True)
    subject = models.CharField(max_length=100, blank=True, null=True)
    topic = models.CharField(max_length=200, blank=True, null=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-uploaded_at']

class NoteSummary(models.Model):
    note = models.OneToOneField(AcademicNote, on_delete=models.CASCADE, related_name='summary')
    summary_text = models.TextField()
    key_points = models.TextField(help_text="Key points extracted from the note")
    bullet_points = models.TextField(blank=True, help_text="Bullet point summary")
    one_line_summary = models.CharField(max_length=500, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Summary for {self.note.title}"

class ImportantQuestion(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    note = models.ForeignKey(AcademicNote, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    answer_hint = models.TextField(blank=True)
    answer = models.TextField(blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium')
    topic = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.question_text[:50]

class ContentAnalysis(models.Model):
    note = models.OneToOneField(AcademicNote, on_delete=models.CASCADE, related_name='analysis')
    clarity_score = models.FloatField(default=0.0)
    structure_score = models.FloatField(default=0.0)
    readability_score = models.FloatField(default=0.0)
    word_count = models.IntegerField(default=0)
    sentence_count = models.IntegerField(default=0)
    complexity_level = models.CharField(max_length=50, blank=True)
    feedback = models.TextField()
    suggestions = models.TextField(blank=True)
    analyzed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Analysis for {self.note.title}"

class StudyPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_plans')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    notes = models.ManyToManyField(AcademicNote, related_name='study_plans', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    target_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title

class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    question = models.ForeignKey(ImportantQuestion, on_delete=models.CASCADE, related_name='progress')
    attempted = models.BooleanField(default=False)
    correct = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'question']
        
