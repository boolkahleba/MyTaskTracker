from django.contrib import admin
from .models import Task, TaskComment, Prediction

admin.site.register(Task)
admin.site.register(TaskComment)
admin.site.register(Prediction)