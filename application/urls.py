from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('set-password/<str:username>/', views.set_new_password, name='set_new_password'),

    path('recruiter/dashboard/', views.recruiter_dashboard, name='recruiter_dashboard'),
    path('candidate/dashboard/', views.candidate_dashboard, name='candidate_dashboard'),
    path("candidate/register/", views.candidate_register, name="candidate_register"),

    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-users/", views.admin_users, name="admin_users"),
    path("admin-jobs/", views.admin_jobs, name="admin_jobs"),
    path("admin-applications/", views.admin_applications, name="admin_applications"),

    path('recruiter/job/add/', views.create_job, name='create_job'),
    path('recruiter/job/edit/<int:job_id>/', views.edit_job, name='edit_job'),
    path('recruiter/job/delete/<int:job_id>/', views.delete_job, name='delete_job'),
    path('recruiter/job/<int:job_id>/applications/', views.recruiter_applications, name='recruiter_applications'),

    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('application/<int:app_id>/status/', views.update_application_status, name='update_application_status'),

    path('notifications/', views.notifications, name='notifications'),
]   
