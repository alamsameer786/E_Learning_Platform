from django.urls import path
from . import views

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Note management
    path('upload/', views.upload_note, name='upload_note'),
    path('note/<int:note_id>/', views.view_note, name='view_note'),
    path('note/<int:note_id>/delete/', views.delete_note, name='delete_note'),
    path('note/<int:note_id>/regenerate/', views.regenerate_ai_content, name='regenerate_ai'),
    path('note/<int:note_id>/export/', views.export_note, name='export_note'),
    
    # Learning features
    path('note/<int:note_id>/questions/', views.generate_questions_view, name='generate_questions'),
    path('quick-revision/', views.quick_revision, name='quick_revision'),
    path('study-plans/', views.study_plans, name='study_plans'),
    path('analytics/', views.note_analytics, name='analytics'),
    path('search/', views.search_notes, name='search_notes'),
]