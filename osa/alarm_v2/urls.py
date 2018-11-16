from django.urls import path
from . import views

urlpatterns = [
    path('', views.alarm_main, name='alarm_v2'),
]
