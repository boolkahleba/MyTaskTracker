from django import forms
from .models import Board
from accounts.models import User, UserGroup


class BoardForm(forms.ModelForm):
    statuses = forms.CharField(
        help_text='Введите статусы через запятую. Например: Открытые, В работе, Готово'
    )
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=UserGroup.objects.all(),
        required=False
    )

    class Meta:
        model = Board
        fields = ['name', 'description', 'statuses', 'users', 'groups']


class BoardUpdateForm(forms.ModelForm):
    statuses = forms.CharField(
        help_text='Введите статусы через запятую. Например: Открытые, В работе, Готово'
    )

    class Meta:
        model = Board
        fields = ['name', 'description', 'statuses']


class BoardAccessForm(forms.Form):
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=UserGroup.objects.all(),
        required=False
    )