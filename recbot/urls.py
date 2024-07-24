from django.urls import path
from . import views

urlpatterns = [
    path('', views.recbot, name='recbot'),
    path('bot/', views.recbotResponse, name='recbotResponse'),
    path('recomender/', views.recbotRecomender, name='recbotRecomender')
    ]