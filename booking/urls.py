from django.urls import path
from . import views

urlpatterns = [
    # 1. The Homepage (matches 'def index' in views.py)
    path('', views.index, name='index'),

    # 2. The Manual Booking Submission (matches 'def submit_manual_booking')
    path('submit-manual/', views.submit_manual_booking, name='submit_manual'),
    path('submit-waitlist/', views.submit_waitlist, name='submit_waitlist'),
]