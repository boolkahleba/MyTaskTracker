from django.urls import path
from . import views

app_name = 'boards'

urlpatterns = [
    path('', views.board_list_view, name='board_list'),
    path('create/', views.create_board_view, name='create_board'),
    path('<int:board_id>/', views.board_detail_view, name='board_detail'),
    path('<int:board_id>/update/', views.update_board_view, name='update_board'),
    path('<int:board_id>/delete/', views.delete_board_view, name='delete_board'),
    path('<int:board_id>/access/', views.board_access_view, name='board_access'),
    path('<int:board_id>/members/<int:member_id>/delete/', views.delete_board_member_view, name='delete_board_member'),
    path('<int:board_id>/groups/<int:right_id>/delete/', views.delete_board_group_right_view, name='delete_board_group_right'),
]