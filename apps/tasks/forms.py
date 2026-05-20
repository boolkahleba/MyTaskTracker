from django import forms
from django.db.models import Q
from .models import Task, TaskComment
from boards.models import BoardStatus, BoardMember, UserGroupRights
from accounts.models import User, UserInGroup

def get_board_available_users(board):
    group_ids = UserGroupRights.objects.filter(
        board=board
    ).values_list('group_id', flat=True)

    group_user_ids = UserInGroup.objects.filter(
        group_id__in=group_ids
    ).values_list('user_id', flat=True)

    direct_user_ids = BoardMember.objects.filter(
        board=board
    ).values_list('user_id', flat=True)

    return User.objects.filter(
        Q(id=board.created_by_id) |
        Q(id__in=direct_user_ids) |
        Q(id__in=group_user_ids) |
        Q(is_staff=True)
    ).distinct().order_by('full_name')

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

    def __init__(self, *args, **kwargs):
        board = kwargs.pop('board', None)
        super().__init__(*args, **kwargs)

        if board:
            self.fields['assignee'].queryset = get_board_available_users(board)
        else:
            self.fields['assignee'].queryset = User.objects.none()


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