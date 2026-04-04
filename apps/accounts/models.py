from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, full_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True, verbose_name='Email')
    full_name = models.CharField(max_length=100, verbose_name='Полное имя')
    is_admin = models.BooleanField(default=False, verbose_name='Администратор')
    registered_at = models.DateTimeField(default=timezone.now, verbose_name='Дата регистрации')

    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        db_table = 'User'


class UserGroup(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, verbose_name='Название группы')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups',
                                   verbose_name='Создатель')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Группа пользователей'
        verbose_name_plural = 'Группы пользователей'
        db_table = 'User_group'


class UserInGroup(models.Model):
    id = models.AutoField(primary_key=True)
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE, related_name='members', verbose_name='Группа')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='groups_membership',
                             verbose_name='Пользователь')

    class Meta:
        unique_together = [['group', 'user']]
        verbose_name = 'Участник группы'
        verbose_name_plural = 'Участники групп'
        db_table = 'User_in_group'