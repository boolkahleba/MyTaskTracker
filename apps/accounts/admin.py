from django.contrib import admin
from .models import User, UserGroup, UserInGroup

admin.site.register(User)
admin.site.register(UserGroup)
admin.site.register(UserInGroup)