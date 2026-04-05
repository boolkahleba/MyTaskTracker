from django import forms
from .models import Board
from accounts.models import User, UserGroup


class BoardForm(forms.ModelForm):
    statuses = forms.CharField(
        help_text='Например: Открытые, В работе, Готово',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите статусы через запятую'
        })
    )

    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )

    groups = forms.ModelMultipleChoiceField(
        queryset=UserGroup.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Board
        fields = ['name', 'description', 'statuses', 'users', 'groups']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название доски'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Описание доски'
            }),
        }


class BoardUpdateForm(forms.ModelForm):
    statuses = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите статусы через запятую'
        })
    )

    class Meta:
        model = Board
        fields = ['name', 'description', 'statuses']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }