from django.db import models
from django.conf import settings
from boards.models import Board, BoardStatus


class Task(models.Model):
    TASK_TYPE_CHOICES = [
        ('bug', 'Ошибка'),
        ('feature', 'Фича'),
        ('task', 'Задача'),
        ('research', 'Ресерч')
    ]

    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
    ]

    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='tasks', verbose_name='Доска')
    status = models.ForeignKey(BoardStatus, on_delete=models.SET_NULL, null=True, related_name='tasks',
                               verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='authored_tasks',
                               verbose_name='Автор')
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='assigned_tasks', verbose_name='Исполнитель')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='Время начала')
    due_date = models.DateField(null=True, blank=True, verbose_name='Срок выполнения')
    time_estimate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                        verbose_name='Оценка времени')
    task_type = models.CharField(max_length=30, choices=TASK_TYPE_CHOICES, default='task', verbose_name='Тип задачи')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name='Приоритет')
    actual_time_spent = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                            verbose_name='Фактическое время, ч')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        db_table = 'Task'


class TaskComment(models.Model):
    id = models.AutoField(primary_key=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments', verbose_name='Задача')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_comments',
                             verbose_name='Пользователь')
    comment = models.TextField(verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Комментарий к задаче'
        verbose_name_plural = 'Комментарии к задачам'
        db_table = 'Task_comment'


class Prediction(models.Model):
    id = models.AutoField(primary_key=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='predictions', verbose_name='Задача')
    prediction_time = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Прогноз времени')
    prediction_text = models.CharField(max_length=255, blank=True, null=True, verbose_name='Текст прогноза')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата прогноза')

    class Meta:
        verbose_name = 'Прогноз'
        verbose_name_plural = 'Прогнозы'
        db_table = 'Prediction'
        ordering = ['-created_at']
