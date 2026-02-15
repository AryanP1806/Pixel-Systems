from django.urls import path
from django.contrib.auth import views as auth_views # Added this
from django.views.generic import TemplateView
from . import views
from .views import CustomLoginView # Added this

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.add_student, name='add_student'),
    path('fees/<int:student_id>/', views.manage_fees, name='manage_fees'),
    path('fees/pay/<int:fee_id>/', views.add_payment, name='add_payment'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('batches/', views.batch_list, name='batch_list'),
    path('batches/create/', views.batch_create, name='batch_create'),
    path('batches/<int:batch_id>/', views.batch_detail, name='batch_detail'),
    path('batches/<int:batch_id>/add-student/', views.add_student_to_batch, name='add_student_to_batch'),
    path('subjects/', views.manage_subjects, name='manage_subjects'),
    path('batches/<int:batch_id>/attendance/', views.take_attendance, name='take_attendance'),
    path('batches/<int:batch_id>/tests/create/', views.create_test, name='create_test'),
    path('tests/<int:test_id>/marks/', views.enter_marks, name='enter_marks'),
    path('my-attendance/', views.student_attendance, name='student_attendance'),
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/add/', views.add_teacher, name='add_teacher'),
    path('receipt/<int:transaction_id>/', views.view_receipt, name='view_receipt'),
    path('my-marks/', views.student_marks, name='student_marks'),
    path('finance_dashboard/', views.finance_dashboard, name='finance_dashboard'),
    path('promote-academic-year/', views.promote_students, name='promote_students'),
    path('students/<int:student_id>/profile/', views.student_profile, name='student_profile'),
    path('students/<int:student_id>/report-card/', views.report_card, name='report_card'), # Add this view!
    path('notices/add/', views.create_notice, name='create_notice'),
    path('materials/upload/', views.upload_material, name='upload_material'),
    path('materials/', views.study_material_list, name='study_material_list'),
    path('notices/add/', views.create_notice, name='create_notice'),
    path('materials/upload/', views.upload_material, name='upload_material'),
    path('materials/', views.study_material_list, name='study_material_list'),
    path('service-worker.js', 
         TemplateView.as_view(template_name="service-worker.js", content_type='application/javascript'), 
         name='service-worker'),
    path('manifest.json', 
         TemplateView.as_view(template_name="manifest.json", content_type='application/json'), 
         name='manifest'),
]