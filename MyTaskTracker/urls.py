from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


def redirect_to_boards(request):
    return redirect('boards:board_list')


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', redirect_to_boards),

    path('accounts/', include('accounts.urls')),
    path('boards/', include('boards.urls')),
    path('tasks/', include('tasks.urls')),
    path('predictions/', include('predictions.urls')),
    path('stats/', include('stats.urls')),
]