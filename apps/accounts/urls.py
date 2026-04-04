from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    path('users/', views.user_list_view, name='user_list'),
    path('groups/', views.group_list_view, name='group_list'),
    path('groups/create/', views.create_group_view, name='create_group'),
    path('groups/<int:group_id>/', views.group_detail_view, name='group_detail'),
    path('groups/<int:group_id>/members/<int:member_id>/delete/', views.delete_group_member_view, name='delete_group_member'),
]