import re
import random
from .models import NoteSummary, ImportantQuestion, ContentAnalysis

def generate_summary(note):
    """Generate comprehensive AI summary (6-7 lines)"""
    content = note.content
    
    # Split into sentences
    sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 30]
    
    if len(sentences) < 3:
        # If content is short, use word-based summarization
        words = content.split()
        if len(words) > 50:
            sentences = [' '.join(words[i:i+15]) for i in range(0, len(words), 15)]
    
    # Generate 6-7 line summary
    summary_lines = []
    
    # Line 1: Introduction/Topic sentence
    if sentences:
        summary_lines.append(sentences[0][:150])
    
    # Lines 2-5: Key information
    important_keywords = ['important', 'key', 'critical', 'essential', 'significant', 'major', 'therefore', 'thus', 'consequently', 'because', 'result']
    important_sentences = [s for s in sentences if any(keyword in s.lower() for keyword in important_keywords)]
    
    if len(important_sentences) >= 4:
        summary_lines.extend([s[:150] for s in important_sentences[:5]])
    else:
        # Take every nth sentence for variety
        step = max(1, len(sentences) // 5)
        for i in range(0, min(5, len(sentences)), step):
            if sentences[i] not in summary_lines:
                summary_lines.append(sentences[i][:150])
    
    # Ensure we have 6-7 lines
    while len(summary_lines) < 6 and sentences:
        for s in sentences:
            if s not in summary_lines:
                summary_lines.append(s[:150])
                if len(summary_lines) >= 6:
                    break
    
    # Join into 6-7 line summary
    full_summary = '. '.join(summary_lines[:7]) + '.'
    
    # Generate bullet points
    bullet_points = []
    for i, sent in enumerate(summary_lines[:5]):
        bullet_points.append(f"• {sent[:100]}...")
    
    # One line summary
    one_line = summary_lines[0][:120] + '...' if len(summary_lines[0]) > 120 else summary_lines[0]
    
    # Extract key points
    key_points_list = []
    for sent in important_sentences[:6]:
        key_points_list.append(f"• {sent[:100]}...")
    
    key_points = '\n'.join(key_points_list) if key_points_list else "• Key points are being processed..."
    
    NoteSummary.objects.update_or_create(
        note=note,
        defaults={
            'summary_text': full_summary,
            'key_points': key_points,
            'bullet_points': '\n'.join(bullet_points),
            'one_line_summary': one_line
        }
    )
    
    return full_summary

def generate_questions(note):
    """Generate questions based on the note content"""
    content = note.content
    sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 30]
    
    # Extract key terms
    words = content.split()
    key_terms = []
    for word in words:
        if len(word) > 5 and word.lower() not in ['there', 'their', 'these', 'those', 'would', 'could', 'should', 'because', 'however', 'therefore']:
            if word.isalpha() and word[0].isupper() or word.lower() in ['algorithm', 'function', 'method', 'process', 'system']:
                key_terms.append(word)
    
    key_terms = list(set(key_terms))[:8]
    
    question_templates = [
        "What is {term}? Explain in detail.",
        "Describe the importance of {term} in this context.",
        "How does {term} work? Provide examples.",
        "What are the key features of {term}?",
        "Compare {term} with related concepts.",
        "Why is {term} significant?",
        "Explain the role of {term}.",
        "What are the applications of {term}?"
    ]
    
    for i, term in enumerate(key_terms[:6]):
        template = random.choice(question_templates)
        question_text = template.format(term=term)
        
        # Find answer hint
        answer_hint = ""
        for sent in sentences:
            if term.lower() in sent.lower():
                answer_hint = sent[:200] + "..."
                break
        
        difficulty = 'easy' if i < 2 else 'medium' if i < 4 else 'hard'
        
        ImportantQuestion.objects.create(
            note=note,
            question_text=question_text,
            answer_hint=answer_hint if answer_hint else "Review the content for this concept.",
            difficulty=difficulty,
            topic=term
        )
    
    # If no questions generated, create default ones
    if ImportantQuestion.objects.filter(note=note).count() == 0:
        default_questions = [
            "What are the main topics covered in this note?",
            "Explain the most important concept from this material.",
            "How would you summarize the key takeaways?",
            "What are the practical applications of this knowledge?"
        ]
        for q in default_questions:
            ImportantQuestion.objects.create(
                note=note,
                question_text=q,
                answer_hint="Review the main sections of your note for the answer.",
                difficulty='medium'
            )

def analyze_content(note):
    """Analyze content quality"""
    content = note.content
    words = len(content.split())
    sentences = len([s for s in content.split('.') if s.strip()])
    
    if words == 0:
        words = 1
    
    # Calculate scores
    avg_word_length = sum(len(word) for word in content.split()) / words
    clarity_score = min(100, max(0, 70 - (avg_word_length * 2) + (min(sentences, 15) * 2)))
    
    has_paragraphs = len([p for p in content.split('\n\n') if p.strip()]) > 1
    structure_score = 60 + (30 if has_paragraphs else 0) + (10 if words > 200 else 0)
    
    # Complexity level
    if avg_word_length > 7:
        complexity = "Advanced"
    elif avg_word_length > 5:
        complexity = "Intermediate"
    else:
        complexity = "Beginner"
    
    # Feedback
    feedback = []
    if words < 100:
        feedback.append("Note is short. Consider adding more details.")
    elif words > 500:
        feedback.append("Comprehensive content! Well organized.")
    
    if not has_paragraphs and words > 200:
        feedback.append("Consider breaking content into paragraphs.")
    
    if clarity_score > 70:
        feedback.append("Excellent clarity!")
    elif clarity_score > 50:
        feedback.append("Good clarity. Keep improving!")
    
    if not feedback:
        feedback.append("Content looks good!")
    
    ContentAnalysis.objects.update_or_create(
        note=note,
        defaults={
            'clarity_score': round(clarity_score, 1),
            'structure_score': structure_score,
            'readability_score': round(50 + clarity_score * 0.4, 1),
            'word_count': words,
            'sentence_count': sentences,
            'complexity_level': complexity,
            'feedback': ' '.join(feedback),
            'suggestions': "Add examples and break into sections for better readability."
        }
    )