from django.contrib import admin
from .models import Board, BoardStatus, BoardMember, UserGroupRights

admin.site.register(Board)
admin.site.register(BoardStatus)
admin.site.register(BoardMember)
admin.site.register(UserGroupRights)