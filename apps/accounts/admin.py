from django.contrib import admin
from .models import User, UserGroup, UserInGroup

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'is_staff', 'is_admin')

    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data:
            obj.set_password(obj.password)

        super().save_model(request, obj, form, change)
admin.site.register(UserGroup)
admin.site.register(UserInGroup)