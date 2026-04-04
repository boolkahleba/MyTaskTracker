from django.urls import path
from . import views

app_name = 'stats'

urlpatterns = [
    path('board/<int:board_id>/', views.board_stats_view, name='board_stats'),
]