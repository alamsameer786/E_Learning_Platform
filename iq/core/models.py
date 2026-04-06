from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"

class AcademicNote(models.Model):
    NOTE_TYPES = [
        ('lecture', 'Lecture Notes'),
        ('pyq', 'Previous Year Questions'),
        ('assignment', 'Assignment'),
        ('reference', 'Reference Material'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    file = models.FileField(upload_to='notes/', blank=True, null=True)
    subject = models.CharField(max_length=100, blank=True, null=True)
    topic = models.CharField(max_length=200, blank=True, null=True)
    semester = models.CharField(max_length=50, blank=True, null=True)
    note_type = models.CharField(max_length=50, choices=NOTE_TYPES, default='lecture')
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-uploaded_at']

class NoteSummary(models.Model):
    note = models.OneToOneField(AcademicNote, on_delete=models.CASCADE, related_name='summary')
    summary_text = models.TextField()
    key_points = models.TextField()
    bullet_points = models.TextField(blank=True)
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
    progress = models.IntegerField(default=0)
    
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

class DSATopic(models.Model):
    name = models.CharField(max_length=100)
    video_url = models.URLField()
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name

class UserDSATopicProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dsa_progress')
    topic = models.ForeignKey(DSATopic, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    quiz_score = models.IntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'topic']

# Signal to create UserProfile automatically
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'profile'):
        UserProfile.objects.create(user=instance)
    instance.profile.save()