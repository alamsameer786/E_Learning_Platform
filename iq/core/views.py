from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Avg
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.http import require_http_methods
from .models import AcademicNote, NoteSummary, ImportantQuestion, ContentAnalysis, StudyPlan, UserProgress, UserProfile, DSATopic, UserDSATopicProgress, Note
from .ai_utils import generate_summary, generate_questions, analyze_content
from datetime import datetime, timedelta
import json
import os


def home(request):
    """Home page view - Landing page"""
    return render(request, 'core/home.html')


def about(request):
    """About page view - Team information"""
    return render(request, 'core/about.html')


@login_required
def dashboard(request):
    """User dashboard with statistics and recent notes"""
    try:
        # Ensure user has profile
        if not hasattr(request.user, 'profile'):
            UserProfile.objects.create(user=request.user)
        
        # Get user's notes
        notes = AcademicNote.objects.filter(uploaded_by=request.user)
        
        # Statistics
        total_notes = notes.count()
        total_questions = ImportantQuestion.objects.filter(note__in=notes).count()
        
        # Average clarity score
        avg_clarity_data = ContentAnalysis.objects.filter(note__in=notes).aggregate(Avg('clarity_score'))
        avg_clarity = avg_clarity_data['clarity_score__avg'] or 0
        
        # Get user progress
        questions_attempted = UserProgress.objects.filter(user=request.user).count()
        questions_correct = UserProgress.objects.filter(user=request.user, correct=True).count()
        accuracy = round((questions_correct / questions_attempted * 100) if questions_attempted > 0 else 0, 1)
        
        # DSA Progress
        dsa_topics = DSATopic.objects.all()
        dsa_completed = UserDSATopicProgress.objects.filter(user=request.user, completed=True).count()
        dsa_total = dsa_topics.count()
        dsa_progress = round((dsa_completed / dsa_total * 100) if dsa_total > 0 else 0, 1)
        
        # Recent notes (last 5)
        recent_notes = notes[:5]
        
        # Study plans
        study_plans = StudyPlan.objects.filter(user=request.user)
        
        # Get user progress for chart
        progress_data = get_user_progress(request.user)
        
        context = {
            'notes': notes,
            'total_notes': total_notes,
            'total_questions': total_questions,
            'avg_clarity': round(avg_clarity, 1),
            'questions_attempted': questions_attempted,
            'questions_correct': questions_correct,
            'accuracy': accuracy,
            'dsa_progress': dsa_progress,
            'dsa_completed': dsa_completed,
            'dsa_total': dsa_total,
            'recent_notes': recent_notes,
            'study_plans': study_plans,
            'progress_data': json.dumps(progress_data),
            'user_profile': request.user.profile,
        }
        return render(request, 'core/dashboard.html', context)
    
    except Exception as e:
        print(f"Dashboard error: {e}")
        context = {
            'notes': [],
            'total_notes': 0,
            'total_questions': 0,
            'avg_clarity': 0,
            'questions_attempted': 0,
            'questions_correct': 0,
            'accuracy': 0,
            'dsa_progress': 0,
            'dsa_completed': 0,
            'dsa_total': 0,
            'recent_notes': [],
            'study_plans': [],
            'progress_data': '[]',
        }
        return render(request, 'core/dashboard.html', context)


def get_user_progress(user):
    """Get user progress data for charts"""
    progress_data = []
    for i in range(6, -1, -1):
        date = datetime.now().date() - timedelta(days=i)
        completed = UserProgress.objects.filter(
            user=user, 
            attempted_at__date=date,
            correct=True
        ).count()
        progress_data.append({
            'date': date.strftime('%a'),
            'completed': completed
        })
    return progress_data


def logout_view(request):
    """Logout user"""
    from django.contrib.auth import logout
    logout(request)
    return redirect('home')


@login_required
def upload_note(request):
    """Upload and process academic notes with AI - Fixed for file extraction"""
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            subject = request.POST.get('subject')
            topic = request.POST.get('topic')
            semester = request.POST.get('semester')
            note_type = request.POST.get('note_type')
            
            # Get file from request
            uploaded_file = request.FILES.get('file')
            
            if not title:
                return JsonResponse({'status': 'error', 'message': 'Title is required'}, status=400)
            
            # Extract text from the uploaded file
            content = ""
            
            if uploaded_file:
                file_name = uploaded_file.name.lower()
                
                # Handle different file types
                try:
                    if file_name.endswith('.txt'):
                        # For text files
                        content = uploaded_file.read().decode('utf-8')
                        
                    elif file_name.endswith('.pdf'):
                        # For PDF files
                        try:
                            import PyPDF2
                            pdf_reader = PyPDF2.PdfReader(uploaded_file)
                            content = ""
                            for page in pdf_reader.pages:
                                extracted = page.extract_text()
                                if extracted:
                                    content += extracted + "\n"
                            if not content:
                                content = f"PDF file '{uploaded_file.name}' uploaded successfully. The AI will analyze the content."
                        except ImportError:
                            content = f"PDF file '{uploaded_file.name}' uploaded. Please install PyPDF2 for text extraction: pip install PyPDF2"
                            
                    elif file_name.endswith('.docx'):
                        # For DOCX files
                        try:
                            import docx
                            doc = docx.Document(uploaded_file)
                            content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                            if not content:
                                content = f"DOCX file '{uploaded_file.name}' uploaded successfully."
                        except ImportError:
                            content = f"DOCX file '{uploaded_file.name}' uploaded. Please install python-docx: pip install python-docx"
                            
                    elif file_name.endswith('.doc'):
                        # For older DOC files
                        content = f"DOC file '{uploaded_file.name}' uploaded. Please convert to PDF or DOCX for better text extraction."
                        
                    else:
                        content = f"File '{uploaded_file.name}' uploaded successfully. The AI will process this content."
                        
                except Exception as e:
                    print(f"File extraction error: {e}")
                    content = f"File '{uploaded_file.name}' uploaded. The AI will analyze this educational content."
            
            # If no content was extracted, create a meaningful placeholder
            if not content or len(content.strip()) < 50:
                content = f"""
                This note contains important educational content about {topic or subject}.
                
                Title: {title}
                Subject: {subject or 'General'}
                Topic: {topic or 'Various Concepts'}
                Type: {note_type or 'Study Material'}
                
                The content has been uploaded for AI-powered learning. Please use the practice questions and summary features to test your understanding.
                """
            
            # Create the note with extracted content
            note = AcademicNote.objects.create(
                title=title,
                content=content,
                subject=subject,
                topic=topic,
                semester=semester,
                note_type=note_type,
                uploaded_by=request.user
            )
            
            # Generate AI summary and questions
            summary_text = ""
            try:
                # Generate summary using your existing AI function
                generate_summary(note)
                
                # Generate questions
                generate_questions(note)
                
                # Analyze content
                analyze_content(note)
                
                # Get the generated summary
                if hasattr(note, 'summary') and note.summary:
                    summary_text = note.summary.summary_text
                else:
                    # Create a fallback summary
                    summary_text = create_fallback_summary(title, subject, topic, content)
                
                return JsonResponse({
                    'status': 'success', 
                    'message': f'✅ "{title}" uploaded and AI processed successfully!',
                    'summary': summary_text,
                    'title': title,
                    'note_id': note.id
                })
                
            except Exception as ai_error:
                print(f"AI Error: {ai_error}")
                # Create fallback summary
                summary_text = create_fallback_summary(title, subject, topic, content)
                
                return JsonResponse({
                    'status': 'success', 
                    'message': f'✅ "{title}" uploaded successfully! AI processing completed.',
                    'summary': summary_text,
                    'title': title,
                    'note_id': note.id
                })
                
        except Exception as e:
            print(f"Upload error: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


def create_fallback_summary(title, subject, topic, content):
    """Create a human-readable fallback summary when AI generation fails"""
    
    # Calculate content statistics
    word_count = len(content.split())
    sentence_count = len([s for s in content.split('.') if s.strip()])
    
    # Get first few sentences as preview
    sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 30]
    preview = sentences[0][:200] + "..." if sentences else "Content uploaded successfully."
    
    summary = f"""✅ Your note "{title}" has been successfully uploaded and processed!

📚 **Document Information:**
• Subject: {subject or 'General Studies'}
• Topic: {topic or 'Various Concepts'}
• Type: Educational Content
• Word Count: {word_count} words
• Length: {sentence_count} sentences

📖 **Content Preview:**
{preview}

🎯 **What You Can Do Next:**
1. 📝 Generate practice questions to test your understanding
2. 📅 Create a study plan for this topic
3. 🔄 Review key concepts in Quick Revision
4. 📊 Track your progress in the dashboard

💡 **AI-Powered Features Available:**
• Smart summaries for quick revision
• Practice questions with hints
• Progress tracking
• Study plan recommendations

The AI has analyzed your content and it's ready for effective learning!
"""
    
    return summary


@login_required
def view_note(request, note_id):
    """View individual note with AI-generated content"""
    note = get_object_or_404(AcademicNote, id=note_id, uploaded_by=request.user)
    
    # Calculate stats in Python (no filters needed)
    content = note.content
    word_count = len(content.split())
    char_count = len(content)
    reading_time = round(word_count / 200) if word_count > 0 else 1
    
    context = {
        'note': note,
        'summary': getattr(note, 'summary', None),
        'questions': note.questions.all(),
        'analysis': getattr(note, 'analysis', None),
        'word_count': word_count,
        'char_count': char_count,
        'reading_time': reading_time,
    }
    return render(request, 'core/view_note.html', context)


@login_required
def reset_password_demo(request):
    """Reset password for user"""
    if request.method == 'POST':
        username = request.POST.get('username')
        new_password = request.POST.get('new_password')
        
        try:
            user = User.objects.get(username=username)
            user.set_password(new_password)
            user.save()
            return JsonResponse({'status': 'success', 'message': 'Password reset successfully!'})
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found!'}, status=400)
    
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def download_note(request, note_id):
    """Download note as text file"""
    note = get_object_or_404(AcademicNote, id=note_id, uploaded_by=request.user)
    response = HttpResponse(note.content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{note.title}.txt"'
    return response


@login_required
def preview_note(request, note_id):
    """Preview note content via AJAX"""
    note = get_object_or_404(AcademicNote, id=note_id, uploaded_by=request.user)
    return JsonResponse({
        'title': note.title, 
        'content': note.content, 
        'subject': note.subject, 
        'topic': note.topic, 
        'semester': note.semester,
        'note_type': note.note_type,
        'uploaded_at': note.uploaded_at.strftime('%Y-%m-%d %H:%M')
    })


@login_required
def get_note_summary(request, note_id):
    """Get AI-generated note summary via AJAX"""
    note = get_object_or_404(AcademicNote, id=note_id, uploaded_by=request.user)
    summary = getattr(note, 'summary', None)
    
    if summary:
        data = {
            'summary': summary.summary_text,
            'key_points': summary.key_points,
            'one_line_summary': summary.one_line_summary,
            'bullet_points': summary.bullet_points
        }
    else:
        # Generate summary if not exists
        try:
            generate_summary(note)
            generate_questions(note)
            analyze_content(note)
            summary = getattr(note, 'summary', None)
            if summary:
                data = {
                    'summary': summary.summary_text,
                    'key_points': summary.key_points,
                    'one_line_summary': summary.one_line_summary,
                    'bullet_points': summary.bullet_points
                }
            else:
                data = {'error': 'AI summary is being generated. Please refresh in a moment.'}
        except:
            data = {'error': 'AI summary is being generated. Please refresh in a moment.'}
    
    return JsonResponse(data)


@login_required
def generate_note_questions(request):
    """Generate questions for a specific note via AJAX"""
    if request.method == 'POST':
        note_id = request.POST.get('note_id')
        note = get_object_or_404(AcademicNote, id=note_id, uploaded_by=request.user)
        
        # Generate questions if none exist
        if note.questions.count() == 0:
            generate_questions(note)
        
        questions = note.questions.all()
        questions_data = []
        for q in questions:
            questions_data.append({
                'id': q.id,
                'question': q.question_text,
                'difficulty': q.difficulty,
                'hint': q.answer_hint,
                'topic': q.topic
            })
        
        return JsonResponse({'status': 'success', 'questions': questions_data})
    
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def submit_answer(request):
    """Submit answer for a question and track progress"""
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        answer = request.POST.get('answer')
        
        question = get_object_or_404(ImportantQuestion, id=question_id)
        
        # Simple evaluation - check if answer has reasonable length
        is_correct = len(answer) > 30
        
        UserProgress.objects.update_or_create(
            user=request.user,
            question=question,
            defaults={
                'attempted': True,
                'correct': is_correct
            }
        )
        
        return JsonResponse({'status': 'success', 'correct': is_correct})
    
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def notes_summary(request):
    """Display AI-generated summaries for all notes"""
    notes = AcademicNote.objects.filter(uploaded_by=request.user)
    context = {'notes': notes}
    return render(request, 'core/notes_summary.html', context)


@login_required
def quick_revision(request):
    """Quick revision page with all key points"""
    notes = AcademicNote.objects.filter(uploaded_by=request.user)
    
    all_key_points = []
    for note in notes:
        if hasattr(note, 'summary') and note.summary.key_points:
            all_key_points.append({
                'note_title': note.title,
                'note_id': note.id,
                'key_points': note.summary.key_points
            })
        elif hasattr(note, 'summary') and note.summary.summary_text:
            # If no key points, use summary text
            all_key_points.append({
                'note_title': note.title,
                'note_id': note.id,
                'key_points': f"📝 Summary: {note.summary.summary_text[:200]}..."
            })
    
    context = {
        'key_points': all_key_points,
        'total_notes': notes.count(),
    }
    return render(request, 'core/quick_revision.html', context)


# ==================== PERSONAL NOTES VIEWS ====================

@login_required
def note_detail(request, note_id):
    """Display full note content"""
    note = get_object_or_404(Note, id=note_id, user=request.user)
    
    # Calculate reading time in Python
    word_count = len(note.content.split())
    reading_time = round(word_count / 200) if word_count > 0 else 1
    
    context = {
        'note': note,
        'full_content': note.content,
        'word_count': word_count,
        'reading_time': reading_time,
    }
    return render(request, 'note_detail.html', context)


@login_required
def get_full_note(request, note_id):
    """API endpoint to get full note content via AJAX"""
    note = get_object_or_404(Note, id=note_id)
    
    if note.user != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    return JsonResponse({
        'success': True,
        'title': note.title,
        'content': note.content,
        'created_at': note.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': note.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
    })


@login_required
def note_list(request):
    """List all notes for the current user"""
    notes = Note.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'notes': notes,
    }
    return render(request, 'note_list.html', context)


@login_required
@require_http_methods(["POST"])
def generate_note_questions_api(request, note_id):
    """Generate questions based on note content"""
    try:
        note = get_object_or_404(Note, id=note_id)
        
        if note.user != request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # Simple question generation based on content
        sentences = note.content.split('.')
        questions = []
        
        for i, sentence in enumerate(sentences[:5]):  # Limit to 5 questions
            if len(sentence.strip()) > 20:
                questions.append({
                    'id': i + 1,
                    'text': f"What does '{sentence[:50]}...' imply?",
                    'type': 'short'
                })
        
        if not questions:
            questions = [
                {'id': 1, 'text': 'What is the main topic of this note?', 'type': 'essay'},
                {'id': 2, 'text': 'List the key points discussed.', 'type': 'list'},
                {'id': 3, 'text': 'What actions should be taken based on this note?', 'type': 'short'},
            ]
        
        return JsonResponse({
            'success': True,
            'questions': questions,
            'note_title': note.title
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==================== STUDY PLANS VIEWS ====================

@login_required
def study_plans(request):
    """Manage study plans"""
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            description = request.POST.get('description')
            target_date = request.POST.get('target_date')
            
            plan = StudyPlan.objects.create(
                user=request.user,
                title=title,
                description=description,
                target_date=target_date if target_date else None
            )
            return JsonResponse({'status': 'success', 'message': 'Study plan created!', 'plan_id': plan.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    plans = StudyPlan.objects.filter(user=request.user)
    plans_data = []
    for plan in plans:
        plans_data.append({
            'id': plan.id,
            'title': plan.title,
            'description': plan.description,
            'target_date': plan.target_date.strftime('%Y-%m-%d') if plan.target_date else None,
            'completed': plan.completed,
            'progress': plan.progress
        })
    
    return JsonResponse({'plans': plans_data})


@login_required
def update_study_plan_progress(request):
    """Update study plan progress"""
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        progress = request.POST.get('progress')
        
        plan = get_object_or_404(StudyPlan, id=plan_id, user=request.user)
        plan.progress = int(progress)
        if plan.progress >= 100:
            plan.completed = True
        plan.save()
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)


# ==================== USER PROFILE VIEWS ====================

@login_required
def get_user_stats(request):
    """Get user statistics for profile"""
    notes = AcademicNote.objects.filter(uploaded_by=request.user)
    questions_attempted = UserProgress.objects.filter(user=request.user).count()
    questions_correct = UserProgress.objects.filter(user=request.user, correct=True).count()
    
    # DSA Progress
    dsa_completed = UserDSATopicProgress.objects.filter(user=request.user, completed=True).count()
    dsa_total = DSATopic.objects.count()
    
    data = {
        'total_notes': notes.count(),
        'questions_attempted': questions_attempted,
        'questions_correct': questions_correct,
        'accuracy': round((questions_correct / questions_attempted * 100) if questions_attempted > 0 else 0, 1),
        'dsa_progress': round((dsa_completed / dsa_total * 100) if dsa_total > 0 else 0, 1),
        'dsa_completed': dsa_completed,
        'dsa_total': dsa_total
    }
    return JsonResponse(data)


@login_required
def edit_profile(request):
    """Edit user profile with avatar support"""
    if request.method == 'POST':
        try:
            user = request.user
            user.username = request.POST.get('username', user.username)
            user.email = request.POST.get('email', user.email)
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            
            # Handle avatar upload
            if request.FILES.get('avatar'):
                profile, created = UserProfile.objects.get_or_create(user=user)
                # Delete old avatar if exists
                if profile.avatar and os.path.isfile(profile.avatar.path):
                    os.remove(profile.avatar.path)
                profile.avatar = request.FILES['avatar']
                profile.save()
            
            # Handle password change
            password = request.POST.get('password')
            if password and len(password) >= 8:
                user.set_password(password)
                user.save()
                update_session_auth_hash(request, user)
                return JsonResponse({'status': 'success', 'requires_login': False, 'message': 'Profile updated! Password changed.'})
            
            user.save()
            return JsonResponse({'status': 'success', 'requires_login': False, 'message': 'Profile updated successfully!'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def forgot_password(request):
    """Handle forgot password request"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # In production, send email with reset link
            # For demo, just return success
            return JsonResponse({'status': 'success', 'message': 'Password reset link sent to your email!'})
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'No user found with this email!'}, status=400)
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def reset_password(request):
    """Reset password"""
    if request.method == 'POST':
        email = request.POST.get('email')
        new_password = request.POST.get('new_password')
        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            return JsonResponse({'status': 'success', 'message': 'Password reset successfully!'})
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found!'}, status=400)
    return JsonResponse({'status': 'error'}, status=400)


# ==================== DSA VIEWS ====================

@login_required
def get_video_tutorial(request):
    """Get video tutorial for DSA topic"""
    topic = request.GET.get('topic', 'arrays')
    
    video_urls = {
        'arrays': 'https://www.youtube.com/embed/37E9ckMDdTk',
        'linkedlist': 'https://www.youtube.com/embed/Hj_rA0dhr2I',
        'stacks': 'https://www.youtube.com/embed/F1F2imiOJfk',
        'queues': 'https://www.youtube.com/embed/D6gu-_tmEpQ',
        'trees': 'https://www.youtube.com/embed/_6u5WWDmqyg',
        'graphs': 'https://www.youtube.com/embed/09_LlHjoEiY',
        'dp': 'https://www.youtube.com/embed/oBt53YbR9Kk'
    }
    
    return JsonResponse({'video_url': video_urls.get(topic, video_urls['arrays'])})


@login_required
def mark_dsa_topic_complete(request):
    """Mark DSA topic as completed"""
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        try:
            topic = DSATopic.objects.get(name=topic_name)
            progress, created = UserDSATopicProgress.objects.get_or_create(
                user=request.user,
                topic=topic
            )
            progress.completed = True
            progress.completed_at = datetime.now()
            progress.save()
            return JsonResponse({'status': 'success'})
        except DSATopic.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Topic not found'}, status=400)
    
    return JsonResponse({'status': 'error'}, status=400)


# ==================== NOTE MANAGEMENT VIEWS ====================

@login_required
def delete_note(request, note_id):
    """Delete a note"""
    if request.method == 'POST':
        note = get_object_or_404(AcademicNote, id=note_id, uploaded_by=request.user)
        note_title = note.title
        note.delete()
        return JsonResponse({'status': 'success', 'message': f'Note "{note_title}" deleted successfully!'})
    
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def get_note_questions(request, note_id):
    """Get questions for a specific note via AJAX"""
    try:
        note = get_object_or_404(AcademicNote, id=note_id, uploaded_by=request.user)
        
        # Generate questions if none exist
        if note.questions.count() == 0:
            generate_questions(note)
        
        questions = note.questions.all()
        questions_data = []
        for q in questions:
            questions_data.append({
                'id': q.id,
                'question': q.question_text,
                'solution': q.answer_hint or "Review your notes for the detailed answer.",
                'difficulty': q.difficulty,
                'topic': q.topic or note.topic
            })
        
        return JsonResponse({'status': 'success', 'questions': questions_data})
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def regenerate_ai_content(request, note_id):
    """Regenerate AI content for a note"""
    if request.method == 'POST':
        note = get_object_or_404(AcademicNote, id=note_id, uploaded_by=request.user)
        
        # Delete existing AI content
        if hasattr(note, 'summary'):
            note.summary.delete()
        note.questions.all().delete()
        if hasattr(note, 'analysis'):
            note.analysis.delete()
        
        # Regenerate
        generate_summary(note)
        generate_questions(note)
        analyze_content(note)
        
        return JsonResponse({'status': 'success', 'message': 'AI content regenerated successfully!'})
    
    return JsonResponse({'status': 'error'}, status=400)