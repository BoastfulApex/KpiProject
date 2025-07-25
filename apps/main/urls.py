from django.urls import path 

from apps.main.api_views import SimpleCheckAPIView


urlpatterns = [
    path('check_user_location/', SimpleCheckAPIView.as_view(), name='simple-check')
    ]
