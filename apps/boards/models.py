from django.db import models
from django.conf import settings
from accounts.models import User, UserGroup


class Board(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name='Название доски')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_boards',
                                   verbose_name='Создатель')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Доска'
        verbose_name_plural = 'Доски'
        db_table = 'Board'


class BoardMember(models.Model):
    ACCESS_CHOICES = [
        ('read', 'Чтение'),
        ('write', 'Запись'),
        ('admin', 'Администрирование'),
    ]
    id = models.AutoField(primary_key=True)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='members', verbose_name='Доска')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='board_memberships',
                             verbose_name='Пользователь')
    access = models.CharField(max_length=10, choices=ACCESS_CHOICES, verbose_name='Уровень доступа')

    class Meta:
        unique_together = [['board', 'user']]
        verbose_name = 'Участник доски'
        verbose_name_plural = 'Участники доски'
        db_table = 'Board_member'


class UserGroupRights(models.Model):
    id = models.AutoField(primary_key=True)
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE, related_name='board_rights', verbose_name='Группа')
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='group_rights', verbose_name='Доска')
    rights = models.CharField(max_length=100, verbose_name='Права (например, read,write)')

    class Meta:
        unique_together = [['group', 'board']]
        verbose_name = 'Права группы на доску'
        verbose_name_plural = 'Права групп на доски'
        db_table = 'User_group_rights'