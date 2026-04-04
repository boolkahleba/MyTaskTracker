from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('board/<int:board_id>/create/', views.create_task_view, name='create_task'),
    path('<int:task_id>/', views.task_detail_view, name='task_detail'),
    path('<int:task_id>/update/', views.update_task_view, name='update_task'),
    path('<int:task_id>/delete/', views.delete_task_view, name='delete_task'),
    path('<int:task_id>/change-status/', views.change_task_status_view, name='change_task_status'),
    path('board/<int:board_id>/search/', views.board_task_search_view, name='task_search'),
]