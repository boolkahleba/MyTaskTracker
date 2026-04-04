from decimal import Decimal
from .models import HistoricalTaskData


def get_simple_prediction(task):
    return Decimal('2.00')


def save_historical_data(task):
    HistoricalTaskData.objects.get_or_create(
        task=task,
        defaults={
            'task_title': task.title,
            'task_type': task.task_type,
            'assignee_name': task.assignee.full_name if task.assignee else '',
            'actual_time_spent': task.actual_time_spent,
        }
    )