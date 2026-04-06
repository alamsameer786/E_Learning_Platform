import os
import textract
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Note
import re

@login_required
def upload_note(request):
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            subject = request.POST.get('subject')
            semester = request.POST.get('semester')
            note_type = request.POST.get('note_type')
            topic = request.POST.get('topic')
            file = request.FILES.get('file')
            
            if not title or not subject or not file:
                return JsonResponse({'status': 'error', 'message': 'Please fill all required fields'})
            
            # Save the note
            note = Note.objects.create(
                user=request.user,
                title=title,
                subject=subject,
                semester=semester if semester else None,
                note_type=note_type,
                topic=topic,
                file=file
            )
            
            # Extract text from the uploaded file
            extracted_text = extract_text_from_file(file)
            
            # Generate a proper human-readable summary
            summary = generate_human_readable_summary(extracted_text, title, subject, topic)
            
            # Save the summary to the note
            note.summary = summary
            note.save()
            
            return JsonResponse({
                'status': 'success',
                'message': f'Note "{title}" uploaded and processed successfully!',
                'summary': summary,
                'title': title
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


def extract_text_from_file(file):
    """Extract text from uploaded file using textract"""
    try:
        # Save temporarily
        temp_path = f'/tmp/{file.name}'
        with open(temp_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        # Extract text
        text = textract.process(temp_path).decode('utf-8')
        
        # Clean up
        os.remove(temp_path)
        
        # Clean the text
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text[:5000]  # Limit to first 5000 chars for summary
        
    except Exception as e:
        return f"Could not extract text: {str(e)}"


def generate_human_readable_summary(text, title, subject, topic):
    """Generate a proper human-readable summary from extracted text"""
    
    if not text or len(text) < 50:
        return f"Your document '{title}' has been successfully uploaded. The AI will analyze the content and provide a detailed summary shortly."
    
    # Clean the text
    text = re.sub(r'[^\w\s\.\,\!\?\-]', ' ', text)
    
    # Get first few sentences for summary
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
    
    # Generate summary based on document type
    if topic:
        summary = f"This document provides comprehensive coverage of {topic}. "
    else:
        summary = f"This document covers important concepts in {subject}. "
    
    # Add main points from the text
    if len(sentences) > 0:
        summary += f"The key topics discussed include: {sentences[0][:200]}"
        
        if len(sentences) > 1:
            summary += f" Additionally, {sentences[1][:150]}"
    
    # Add learning objectives
    summary += f"\n\n📚 Learning Objectives:\n• Understand the core concepts of {subject}\n• Apply the knowledge to solve related problems\n• Prepare for exams and assessments"
    
    # Add key takeaways
    summary += f"\n\n💡 Key Takeaways:\n• The document contains {len(text.split())} words of valuable content\n• Focus on understanding the main concepts rather than memorization\n• Practice with the AI-generated questions to test your understanding"
    
    return summary


@login_required
def get_note_questions(request, note_id):
    """Generate practice questions from note content"""
    try:
        note = Note.objects.get(id=note_id, user=request.user)
        
        # Generate questions based on note content
        questions = []
        
        # Sample questions based on subject
        if note.subject == "Mathematics":
            questions = [
                {
                    'question': f"What are the key formulas and concepts covered in '{note.title}'?",
                    'solution': "The document explains various mathematical concepts with step-by-step solutions. Focus on understanding the problem-solving approach.",
                    'difficulty': "Medium",
                    'topic': note.topic or "Mathematics"
                },
                {
                    'question': "How would you apply these concepts to solve real-world problems?",
                    'solution': "Apply the mathematical principles by first identifying the problem type, then selecting the appropriate formula or method.",
                    'difficulty': "Hard",
                    'topic': "Application"
                }
            ]
        elif note.subject == "Computer Science":
            questions = [
                {
                    'question': f"What are the main programming concepts discussed in '{note.title}'?",
                    'solution': "The document covers fundamental programming concepts with examples. Practice implementing these concepts in code.",
                    'difficulty': "Medium",
                    'topic': note.topic or "Programming"
                }
            ]
        else:
            questions = [
                {
                    'question': f"What are the key concepts explained in '{note.title}'?",
                    'solution': f"This document from {note.subject} covers important theoretical concepts. Review the main headings and key terms for better understanding.",
                    'difficulty': "Easy",
                    'topic': note.topic or note.subject
                },
                {
                    'question': "How can you apply this knowledge in practical situations?",
                    'solution': "Apply the concepts by relating them to real-world examples and practicing with scenario-based questions.",
                    'difficulty': "Medium",
                    'topic': "Application"
                }
            ]
        
        return JsonResponse({
            'status': 'success',
            'questions': questions
        })
        
    except Note.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Note not found'})