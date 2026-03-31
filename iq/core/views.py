from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Avg
from .models import AcademicNote, NoteSummary, ImportantQuestion, ContentAnalysis, StudyPlan, UserProgress
from .forms import AcademicNoteForm, StudyPlanForm
from .ai_utils import generate_summary, extract_key_points, generate_questions, analyze_content
from datetime import datetime
from django.db import models

def home(request):
    """Home page view"""
    return render(request, 'core/home.html')

def about(request):
    """About page view"""
    return render(request, 'core/about.html')

@login_required
def dashboard(request):
    """User dashboard with statistics and recent notes"""
    try:
        # Get user's notes
        notes = AcademicNote.objects.filter(uploaded_by=request.user)
        
        # Statistics
        total_notes = notes.count()
        total_questions = ImportantQuestion.objects.filter(note__in=notes).count()
        
        # Average clarity score
        avg_clarity_data = ContentAnalysis.objects.filter(note__in=notes).aggregate(Avg('clarity_score'))
        avg_clarity = avg_clarity_data['clarity_score__avg'] or 0
        
        # Recent notes (last 5)
        recent_notes = notes[:5]
        
        # Study plans - with error handling
        study_plans = []
        try:
            study_plans = StudyPlan.objects.filter(user=request.user)[:3]
        except:
            # Table might not exist yet
            pass
        
        context = {
            'notes': notes,
            'total_notes': total_notes,
            'total_questions': total_questions,
            'avg_clarity': round(avg_clarity, 1),
            'recent_notes': recent_notes,
            'study_plans': study_plans,
        }
        return render(request, 'core/dashboard.html', context)
    
    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        return render(request, 'core/dashboard.html', {'notes': [], 'total_notes': 0})

@login_required
def upload_note(request):
    """Upload and process academic notes with AI"""
    if request.method == 'POST':
        form = AcademicNoteForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                note = form.save(commit=False)
                note.uploaded_by = request.user
                note.save()
                
                # Process with AI (with error handling)
                try:
                    generate_summary(note)
                    extract_key_points(note)
                    generate_questions(note)
                    analyze_content(note)
                    messages.success(request, 'Note uploaded and AI processing completed successfully!')
                except Exception as ai_error:
                    messages.warning(request, f'Note uploaded but AI processing encountered an issue: {str(ai_error)}')
                
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f'Error saving note: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AcademicNoteForm()
    
    return render(request, 'core/upload_note.html', {'form': form})

@login_required
def view_note(request, note_id):
    """View individual note with AI-generated content"""
    try:
        note = get_object_or_404(AcademicNote, id=note_id, uploaded_by=request.user)
        
        # Get AI-generated content
        summary = getattr(note, 'summary', None)
        questions = note.questions.all()
        analysis = getattr(note, 'analysis', None)
        
        context = {
            'note': note,
            'summary': summary,
            'questions': questions,
            'analysis': analysis,
        }
        return render(request, 'core/view_note.html', context)
    
    except Exception as e:
        messages.error(request, f'Error loading note: {str(e)}')
        return redirect('dashboard')

@login_required
def generate_questions_view(request, note_id):
    """Generate and display practice questions for a note"""
    note = get_object_or_404(AcademicNote, id=note_id, uploaded_by=request.user)
    questions = note.questions.all()
    
    # Get user progress for these questions
    progress_dict = {}
    try:
        for q in questions:
            user_progress = UserProgress.objects.filter(user=request.user, question=q).first()
            if user_progress:
                progress_dict[q.id] = user_progress.correct
    except:
        # UserProgress table might not exist yet
        pass
    
    if request.method == 'POST':
        # Handle quiz submission
        score = 0
        total = questions.count()
        
        for question in questions:
            answer = request.POST.get(f'answer_{question.id}', '')
            
            # Simple evaluation - in real app, compare with actual answer
            # For now, just mark as attempted
            is_correct = len(answer) > 20  # Simple placeholder logic
            
            try:
                UserProgress.objects.update_or_create(
                    user=request.user,
                    question=question,
                    defaults={
                        'attempted': True,
                        'correct': is_correct
                    }
                )
                if is_correct:
                    score += 1
            except:
                pass
        
        if total > 0:
            messages.success(request, f'Quiz completed! Your score: {score}/{total}')
        else:
            messages.info(request, 'No questions available for this note.')
        
        return redirect('view_note', note_id=note.id)
    
    context = {
        'note': note,
        'questions': questions,
        'progress': progress_dict,
    }
    return render(request, 'core/questions.html', context)

@login_required
def study_plans(request):
    """Manage study plans"""
    plans = []
    try:
        plans = StudyPlan.objects.filter(user=request.user)
    except Exception as e:
        messages.warning(request, 'Study plans feature will be available soon. Please run migrations first.')
    
    if request.method == 'POST':
        try:
            form = StudyPlanForm(request.POST)
            if form.is_valid():
                plan = form.save(commit=False)
                plan.user = request.user
                plan.save()
                messages.success(request, 'Study plan created successfully!')
                return redirect('study_plans')
            else:
                messages.error(request, 'Please correct the errors below.')
        except Exception as e:
            messages.error(request, f'Could not create study plan: {str(e)}')
    else:
        form = StudyPlanForm()
    
    context = {
        'plans': plans,
        'form': form,
    }
    return render(request, 'core/study_plans.html', context)

@login_required
def quick_revision(request):
    """Quick revision page with all key points"""
    notes = AcademicNote.objects.filter(uploaded_by=request.user)
    
    # Get all key points from notes
    all_key_points = []
    for note in notes:
        if hasattr(note, 'summary') and note.summary.key_points:
            all_key_points.append({
                'note_title': note.title,
                'note_id': note.id,
                'key_points': note.summary.key_points
            })
    
    context = {
        'key_points': all_key_points,
        'total_notes': notes.count(),
    }
    return render(request, 'core/quick_revision.html', context)

@login_required
def note_analytics(request):
    """Display analytics for all notes"""
    notes = AcademicNote.objects.filter(uploaded_by=request.user)
    
    analytics_data = []
    for note in notes:
        if hasattr(note, 'analysis') and note.analysis:
            analytics_data.append({
                'title': note.title,
                'clarity': note.analysis.clarity_score,
                'structure': note.analysis.structure_score,
                'words': note.analysis.word_count,
                'date': note.uploaded_at
            })
    
    context = {
        'analytics': analytics_data,
        'total_notes': len(analytics_data),
    }
    return render(request, 'core/analytics.html', context)

@login_required
def delete_note(request, note_id):
    """Delete a note and all related AI data"""
    note = get_object_or_404(AcademicNote, id=note_id, uploaded_by=request.user)
    
    if request.method == 'POST':
        try:
            note_title = note.title
            note.delete()
            messages.success(request, f'Note "{note_title}" has been deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting note: {str(e)}')
        
        return redirect('dashboard')
    
    return render(request, 'core/confirm_delete.html', {'note': note})

@login_required
def regenerate_ai_content(request, note_id):
    """Regenerate AI content for a note"""
    note = get_object_or_404(AcademicNote, id=note_id, uploaded_by=request.user)
    
    if request.method == 'POST':
        try:
            # Delete existing AI content
            if hasattr(note, 'summary'):
                note.summary.delete()
            note.questions.all().delete()
            if hasattr(note, 'analysis'):
                note.analysis.delete()
            
            # Regenerate
            generate_summary(note)
            extract_key_points(note)
            generate_questions(note)
            analyze_content(note)
            
            messages.success(request, 'AI content regenerated successfully!')
        except Exception as e:
            messages.error(request, f'Error regenerating AI content: {str(e)}')
        
        return redirect('view_note', note_id=note.id)
    
    return render(request, 'core/regenerate_confirm.html', {'note': note})

@login_required
def export_note(request, note_id):
    """Export note with all AI content"""
    note = get_object_or_404(AcademicNote, id=note_id, uploaded_by=request.user)
    
    # Prepare export data
    export_data = {
        'title': note.title,
        'subject': note.subject,
        'topic': note.topic,
        'content': note.content,
        'uploaded_at': note.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    # Add AI content if available
    if hasattr(note, 'summary'):
        export_data['summary'] = note.summary.summary_text
        export_data['key_points'] = note.summary.key_points
    
    if hasattr(note, 'analysis'):
        export_data['clarity_score'] = note.analysis.clarity_score
        export_data['structure_score'] = note.analysis.structure_score
        export_data['feedback'] = note.analysis.feedback
    
    questions = []
    for q in note.questions.all():
        questions.append({
            'question': q.question_text,
            'difficulty': q.difficulty,
            'hint': q.answer_hint
        })
    export_data['questions'] = questions
    
    # For now, just display JSON (could also generate PDF/DOC)
    return JsonResponse(export_data, json_dumps_params={'indent': 2})

@login_required
def search_notes(request):
    """Search notes by title, subject, or content"""
    query = request.GET.get('q', '')
    
    if query:
        notes = AcademicNote.objects.filter(
            uploaded_by=request.user
        ).filter(
            models.Q(title__icontains=query) |
            models.Q(subject__icontains=query) |
            models.Q(topic__icontains=query) |
            models.Q(content__icontains=query)
        )
    else:
        notes = AcademicNote.objects.filter(uploaded_by=request.user)
    
    context = {
        'notes': notes,
        'query': query,
        'total_results': notes.count(),
    }
    return render(request, 'core/search_results.html', context)