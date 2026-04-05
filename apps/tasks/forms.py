from django import forms
from .models import Task, TaskComment
from boards.models import BoardStatus
from accounts.models import User


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'task_type',
            'priority',
            'due_date',
            'assignee',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название задачи'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Описание задачи'
            }),
            'task_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'assignee': forms.Select(attrs={'class': 'form-select'}),
        }


class TaskUpdateForm(TaskForm):
    pass


class TaskStatusForm(forms.Form):
    status = forms.ModelChoiceField(
        queryset=BoardStatus.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    actual_time_spent = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите часы (например 3.5)'
        })
    )

    def __init__(self, *args, **kwargs):
        board = kwargs.pop('board', None)
        super().__init__(*args, **kwargs)
        if board:
            self.fields['status'].queryset = BoardStatus.objects.filter(board=board)


class TaskFilterForm(forms.Form):
    title = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    task_type = forms.ChoiceField(
        required=False,
        choices=[('', '---')] + list(Task.TASK_TYPE_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    priority = forms.ChoiceField(
        required=False,
        choices=[('', '---')] + list(Task.PRIORITY_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    assignee = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    status = forms.ModelChoiceField(
        queryset=BoardStatus.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    def __init__(self, *args, **kwargs):
        board = kwargs.pop('board', None)
        super().__init__(*args, **kwargs)
        if board:
            self.fields['status'].queryset = BoardStatus.objects.filter(board=board)


class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Введите комментарий...'
            }),
        }