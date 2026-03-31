from .models import NoteSummary, ImportantQuestion, ContentAnalysis
import re
from textstat import textstat

def generate_summary(note):
    """Generate comprehensive AI summary"""
    content = note.content
    
    # Advanced summarization logic
    sentences = [s.strip() for s in content.split('.') if s.strip()]
    
    # Generate different types of summaries
    # 1. Short summary (first 3-4 sentences)
    short_summary = '. '.join(sentences[:4]) + '.'
    
    # 2. Key sentences (sentences with important keywords)
    important_keywords = ['important', 'key', 'critical', 'essential', 'significant', 'major']
    key_sentences = [s for s in sentences if any(keyword in s.lower() for keyword in important_keywords)]
    if not key_sentences:
        key_sentences = sentences[:5]
    
    bullet_points = '\n'.join([f'• {s[:100]}...' for s in key_sentences[:5]])
    
    # 3. One line summary
    one_line = sentences[0][:150] + '...' if len(sentences[0]) > 150 else sentences[0]
    
    NoteSummary.objects.update_or_create(
        note=note,
        defaults={
            'summary_text': short_summary,
            'key_points': '\n'.join([f'• {s}' for s in key_sentences[:7]]),
            'bullet_points': bullet_points,
            'one_line_summary': one_line
        }
    )

def extract_key_points(note):
    """Extract key points with definitions and concepts"""
    content = note.content
    
    # Extract potential definitions (sentences with 'is', 'are', 'refers to')
    definition_patterns = [r'\b\w+\s+is\s+', r'\b\w+\s+are\s+', r'\brefers to\b', r'\bmeans\b']
    definitions = []
    
    sentences = content.split('.')
    for sentence in sentences:
        for pattern in definition_patterns:
            if re.search(pattern, sentence, re.IGNORECASE):
                definitions.append(sentence.strip())
                break
    
    # Extract concepts (capitalized terms, technical words)
    concepts = re.findall(r'\b[A-Z][a-z]+\b', content)
    unique_concepts = list(set(concepts))[:10]
    
    key_points_text = "📌 **Key Concepts:**\n"
    key_points_text += '\n'.join([f'• {concept}' for concept in unique_concepts])
    key_points_text += "\n\n📖 **Important Definitions:**\n"
    key_points_text += '\n'.join([f'• {defn[:150]}...' for defn in definitions[:5]])
    
    if hasattr(note, 'summary'):
        note.summary.key_points = key_points_text
        note.summary.save()

def generate_questions(note):
    """Generate comprehensive exam-oriented questions"""
    content = note.content
    sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 20]
    
    questions_generated = []
    
    # Question templates by type
    question_templates = {
        'definition': [
            "What is meant by '{}'?",
            "Define {} in your own words.",
            "Explain the concept of {}."
        ],
        'explain': [
            "Explain the importance of {}.",
            "Describe the process of {}.",
            "How does {} work?",
            "What are the key features of {}?"
        ],
        'compare': [
            "Compare and contrast {} with other approaches.",
            "What are the advantages and disadvantages of {}?"
        ],
        'application': [
            "Provide examples of {}.",
            "How can {} be applied in real-world scenarios?",
            "What are the practical implications of {}?"
        ]
    }
    
    # Extract key terms for questions
    key_terms = re.findall(r'\b[A-Za-z]{5,}\b', content)
    key_terms = list(set([term for term in key_terms if term.lower() not in ['there', 'their', 'these', 'those', 'would', 'could']]))[:15]
    
    # Generate different types of questions
    for i, term in enumerate(key_terms[:8]):  # Limit to 8 questions
        question_type = list(question_templates.keys())[i % len(question_templates)]
        template = question_templates[question_type][i % len(question_templates[question_type])]
        question_text = template.format(term)
        
        # Find answer hint from content
        answer_hint = ""
        for sentence in sentences:
            if term.lower() in sentence.lower():
                answer_hint = sentence[:200]
                break
        
        difficulty = 'easy' if i < 3 else 'medium' if i < 6 else 'hard'
        
        ImportantQuestion.objects.create(
            note=note,
            question_text=question_text,
            answer_hint=answer_hint if answer_hint else "Review the content for this concept",
            difficulty=difficulty,
            topic=term
        )
        questions_generated.append(question_text)
    
    # If no questions were generated, create default ones
    if not questions_generated:
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
                answer_hint="Review the main sections of your note",
                difficulty='medium'
            )

def analyze_content(note):
    """Comprehensive content analysis"""
    content = note.content
    
    # Basic metrics
    words = len(content.split())
    sentences = len([s for s in content.split('.') if s.strip()])
    avg_word_length = sum(len(word) for word in content.split()) / max(words, 1)
    
    # Readability score (using textstat if available, otherwise custom)
    try:
        readability = textstat.flesch_reading_ease(content)
    except:
        # Custom readability calculation
        readability = 60  # Default medium readability
    
    # Complexity level
    if readability > 70:
        complexity = "Easy to read"
    elif readability > 50:
        complexity = "Moderately challenging"
    else:
        complexity = "Complex - requires focus"
    
    # Clarity score based on various factors
    clarity_score = min(100, (
        (min(words / 200, 1) * 30) +  # Content length
        (min(sentences / 15, 1) * 20) +  # Structure
        (min(avg_word_length / 7, 1) * 20) +  # Word complexity
        (min(readability / 100, 1) * 30)  # Readability
    ))
    
    # Structure score
    has_paragraphs = len([p for p in content.split('\n\n') if p.strip()]) > 1
    has_bullets = '•' in content or '-' in content or '*' in content
    has_numbers = any(c.isdigit() for c in content)
    
    structure_score = (
        (30 if has_paragraphs else 0) +
        (40 if has_bullets else 20) +
        (30 if has_numbers else 10)
    )
    
    # Generate detailed feedback
    feedback = []
    suggestions = []
    
    if words < 100:
        feedback.append("⚠️ Content is quite short. Consider expanding on key concepts.")
        suggestions.append("Add more details, examples, and explanations to strengthen your notes.")
    elif words > 1000:
        feedback.append("📚 Comprehensive content! Consider breaking into sections for better organization.")
        suggestions.append("Use headings and subheadings to improve structure.")
    
    if not has_paragraphs:
        feedback.append("📝 Consider organizing content into paragraphs for better readability.")
        suggestions.append("Group related ideas into separate paragraphs.")
    
    if not has_bullets:
        suggestions.append("Use bullet points or numbered lists to highlight key information.")
    
    if readability < 50:
        feedback.append("🎯 Content is quite technical. Consider adding simpler explanations.")
        suggestions.append("Add examples or analogies to make complex concepts more accessible.")
    elif readability > 80:
        feedback.append("✅ Content is very accessible and easy to understand.")
    
    if clarity_score > 80:
        feedback.append("🌟 Excellent clarity! Your content is well-structured and clear.")
    elif clarity_score > 60:
        feedback.append("👍 Good clarity. Minor improvements could make it excellent.")
    
    if not feedback:
        feedback.append("✅ Content looks good overall. Keep up the great work!")
    
    ContentAnalysis.objects.update_or_create(
        note=note,
        defaults={
            'clarity_score': clarity_score,
            'structure_score': structure_score,
            'readability_score': readability,
            'word_count': words,
            'sentence_count': sentences,
            'complexity_level': complexity,
            'feedback': ' '.join(feedback),
            'suggestions': ' '.join(suggestions)
        }
    )