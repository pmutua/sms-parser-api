from django.urls import path
from api.views import get_latest_sms

urlpatterns = [
    path('sms/latest/', get_latest_sms, name='latest-sms'),
]