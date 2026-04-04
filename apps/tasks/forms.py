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


class TaskUpdateForm(forms.ModelForm):
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


class TaskStatusForm(forms.Form):
    status = forms.ModelChoiceField(queryset=BoardStatus.objects.none())
    actual_time_spent = forms.DecimalField(required=False, min_value=0)

    def __init__(self, *args, **kwargs):
        board = kwargs.pop('board', None)
        super().__init__(*args, **kwargs)
        if board is not None:
            self.fields['status'].queryset = BoardStatus.objects.filter(board=board).order_by('position')


class TaskFilterForm(forms.Form):
    title = forms.CharField(required=False)
    task_type = forms.ChoiceField(
        required=False,
        choices=[('', '---------')] + list(Task.TASK_TYPE_CHOICES)
    )
    priority = forms.ChoiceField(
        required=False,
        choices=[('', '---------')] + list(Task.PRIORITY_CHOICES)
    )
    assignee = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False
    )
    status = forms.ModelChoiceField(
        queryset=BoardStatus.objects.none(),
        required=False
    )
    due_date = forms.DateField(required=False)

    def __init__(self, *args, **kwargs):
        board = kwargs.pop('board', None)
        super().__init__(*args, **kwargs)
        if board is not None:
            self.fields['status'].queryset = BoardStatus.objects.filter(board=board).order_by('position')


class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ['comment']