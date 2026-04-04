from django.db import models
from tasks.models import Task


class HistoricalTaskData(models.Model):
    id = models.AutoField(primary_key=True)
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='historical_data')
    task_title = models.CharField(max_length=200)
    task_type = models.CharField(max_length=30)
    assignee_name = models.CharField(max_length=100, blank=True, null=True)
    actual_time_spent = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.task_title

    class Meta:
        db_table = 'Historical_task_data'
        verbose_name = 'Исторические данные задачи'
        verbose_name_plural = 'Исторические данные задач'