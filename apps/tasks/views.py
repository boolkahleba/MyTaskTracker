from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
import json
from django.http import Http404, JsonResponse

from .forms import TaskForm, TaskUpdateForm, TaskStatusForm, TaskFilterForm, TaskCommentForm
from .models import Task, Prediction
from boards.models import Board, BoardStatus
from boards.utils import user_has_board_access, user_can_edit_task
from predictions.predictors import get_simple_prediction, save_historical_data


@login_required
def create_task_view(request, board_id):
    board = get_object_or_404(Board, pk=board_id)

    if not user_has_board_access(request.user, board):
        raise Http404

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            first_status = BoardStatus.objects.filter(board=board).order_by('position').first()

            task = form.save(commit=False)
            task.board = board
            task.author = request.user
            task.status = first_status
            task.time_estimate = Decimal('2.00')
            task.save()

            prediction_value = get_simple_prediction(task)
            Prediction.objects.create(
                task=task,
                prediction_time=prediction_value
            )

            return redirect('boards:board_detail', board_id=board.id)
    else:
        form = TaskForm()

    return render(request, 'tasks/create_task.html', {
        'form': form,
        'board': board,
    })


@login_required
def task_detail_view(request, task_id):
    task = get_object_or_404(Task.objects.select_related('board', 'author', 'assignee', 'status'), pk=task_id)

    if not user_has_board_access(request.user, task.board):
        raise Http404

    comments = task.comments.select_related('user').all().order_by('-created_at')
    prediction = task.predictions.order_by('-created_at').first()

    if request.method == 'POST':
        comment_form = TaskCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.task = task
            comment.user = request.user
            comment.save()
            return redirect('tasks:task_detail', task_id=task.id)
    else:
        comment_form = TaskCommentForm()

    return render(request, 'tasks/task_detail.html', {
        'task': task,
        'comments': comments,
        'comment_form': comment_form,
        'prediction': prediction,
    })


@login_required
def update_task_view(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    if not user_can_edit_task(request.user, task):
        raise Http404

    if request.method == 'POST':
        form = TaskUpdateForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('tasks:task_detail', task_id=task.id)
    else:
        form = TaskUpdateForm(instance=task)

    return render(request, 'tasks/update_task.html', {
        'form': form,
        'task': task,
    })


@login_required
def delete_task_view(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    if not user_can_edit_task(request.user, task):
        raise Http404

    board_id = task.board.id

    if request.method == 'POST':
        task.delete()
        return redirect('boards:board_detail', board_id=board_id)

    return render(request, 'tasks/delete_task.html', {
        'task': task,
    })


@login_required
def change_task_status_view(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    if not user_has_board_access(request.user, task.board):
        raise Http404

    old_status_name = task.status.name.lower() if task.status else ''

    if request.method == 'POST':
        form = TaskStatusForm(request.POST, board=task.board)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            actual_time_spent = form.cleaned_data.get('actual_time_spent')

            if old_status_name == 'в работе' and actual_time_spent is not None:
                task.actual_time_spent = actual_time_spent

            if new_status.name.lower() == 'в работе' and task.started_at is None:
                task.started_at = timezone.now()

            task.status = new_status
            task.save()

            if new_status.name.lower() in ['готово', 'done', 'completed', 'завершено']:
                save_historical_data(task)

            return redirect('tasks:task_detail', task_id=task.id)
    else:
        form = TaskStatusForm(board=task.board, initial={'status': task.status})

    return render(request, 'tasks/change_task_status.html', {
        'form': form,
        'task': task,
    })


@login_required
def board_task_search_view(request, board_id):
    board = get_object_or_404(Board, pk=board_id)

    if not user_has_board_access(request.user, board):
        raise Http404

    tasks = Task.objects.filter(board=board).select_related('author', 'assignee', 'status').order_by('-created_at')
    form = TaskFilterForm(request.GET or None, board=board)

    if form.is_valid():
        title = form.cleaned_data.get('title')
        task_type = form.cleaned_data.get('task_type')
        priority = form.cleaned_data.get('priority')
        assignee = form.cleaned_data.get('assignee')
        status = form.cleaned_data.get('status')
        due_date = form.cleaned_data.get('due_date')

        if title:
            tasks = tasks.filter(title__icontains=title)
        if task_type:
            tasks = tasks.filter(task_type=task_type)
        if priority:
            tasks = tasks.filter(priority=priority)
        if assignee:
            tasks = tasks.filter(assignee=assignee)
        if status:
            tasks = tasks.filter(status=status)
        if due_date:
            tasks = tasks.filter(due_date=due_date)

    return render(request, 'tasks/task_search.html', {
        'board': board,
        'tasks': tasks,
        'form': form,
    })


@login_required
def my_tasks_view(request):
    tasks = Task.objects.filter(assignee=request.user).select_related('board', 'status').order_by('-created_at')
    return render(request, 'tasks/my_tasks.html', {
        'tasks': tasks,
    })


@login_required
def drag_update_task_status_view(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    if not user_has_board_access(request.user, task.board):
        raise Http404

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Неверный метод запроса'}, status=400)

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({'success': False, 'error': 'Некорректные данные'}, status=400)

    status_id = data.get('status_id')
    actual_time_spent = data.get('actual_time_spent')

    if not status_id:
        return JsonResponse({'success': False, 'error': 'Не передан статус'}, status=400)

    new_status = get_object_or_404(BoardStatus, pk=status_id, board=task.board)

    old_status_name = task.status.name.lower() if task.status else ''
    new_status_name = new_status.name.lower()

    if old_status_name == 'в работе':
        if actual_time_spent not in [None, '']:
            try:
                task.actual_time_spent = Decimal(str(actual_time_spent))
            except:
                return JsonResponse({'success': False, 'error': 'Некорректное фактическое время'}, status=400)

    if new_status_name == 'в работе' and task.started_at is None:
        task.started_at = timezone.now()

    task.status = new_status
    task.save()

    if new_status_name in ['готово', 'done', 'completed', 'завершено']:
        save_historical_data(task)

    return JsonResponse({
        'success': True,
        'new_status': new_status.name,
        'task_id': task.id,
    })