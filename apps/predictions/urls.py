from django.urls import path
from . import views

app_name = 'predictions'

urlpatterns = [
    path('history/', views.historical_data_list_view, name='history'),
]