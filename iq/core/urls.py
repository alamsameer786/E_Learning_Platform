from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/', views.upload_note, name='upload_note'),
    path('note/<int:note_id>/', views.view_note, name='view_note'),
    path('note/<int:note_id>/download/', views.download_note, name='download_note'),
    path('note/<int:note_id>/preview/', views.preview_note, name='preview_note'),
    path('note/<int:note_id>/summary/', views.get_note_summary, name='get_note_summary'),
    path('note/<int:note_id>/questions/', views.get_note_questions, name='get_note_questions'),
    path('notes-summary/', views.notes_summary, name='notes_summary'),
    path('quick-revision/', views.quick_revision, name='quick_revision'),
    path('study-plans/', views.study_plans, name='study_plans'),
    path('get-user-stats/', views.get_user_stats, name='get_user_stats'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('get-video-tutorial/', views.get_video_tutorial, name='get_video_tutorial'),
    path('mark-dsa-complete/', views.mark_dsa_topic_complete, name='mark_dsa_complete'),
    path('reset-password-demo/', views.reset_password_demo, name='reset_password_demo'),
    path('logout/', views.logout_view, name='logout'),  # Add this line
    # Make sure this line exists in your urls.py
    path('note/<int:note_id>/questions/', views.get_note_questions, name='get_note_questions'),
    path('note/<int:note_id>/generate-questions/', views.generate_questions, name='generate_questions'),
    path('notes/', views.note_list, name='note_list'),
    path('note/<int:note_id>/', views.note_detail, name='note_detail'),
    path('note/<int:note_id>/full/', views.get_full_note, name='get_full_note'),
    path('note/<int:note_id>/generate-questions/', views.generate_questions, name='generate_questions'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)