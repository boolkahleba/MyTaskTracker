from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Avg
from django.utils import timezone
from decimal import Decimal
import math

from boards.models import Board
from boards.utils import user_has_board_access
from tasks.models import Task


@login_required
def board_stats_view(request, board_id):
    board = get_object_or_404(Board, pk=board_id)

    if not request.user.is_staff:
        raise Http404

    all_tasks = Task.objects.filter(board=board)

    total_tasks = all_tasks.count()

    completed_tasks = all_tasks.filter(
        status__name__in=['Готово', 'Done', 'Completed', 'Завершено']
    ).count()

    overdue_tasks = all_tasks.filter(
        due_date__lt=timezone.now().date()
    ).exclude(
        status__name__in=['Готово', 'Done', 'Completed', 'Завершено']
    ).count()

    status_stats = all_tasks.values('status__name').annotate(
        total=Count('id')
    ).order_by('status__name')

    assignee_stats = all_tasks.values('assignee__full_name').annotate(
        total=Count('id')
    ).order_by('assignee__full_name')

    type_stats = []

    task_types = all_tasks.values_list('task_type', flat=True).distinct()

    for task_type in task_types:
        tasks_by_type = all_tasks.filter(task_type=task_type)

        predictions = []
        actual_times = []
        abs_errors = []
        squared_errors = []
        percent_errors = []

        for task in tasks_by_type:
            prediction = task.predictions.order_by('-created_at').first()

            if prediction and prediction.prediction_time is not None:
                predictions.append(float(prediction.prediction_time))

            if task.actual_time_spent is not None:
                actual_times.append(float(task.actual_time_spent))

            if (
                prediction and
                prediction.prediction_time is not None and
                task.actual_time_spent is not None
            ):
                predicted = float(prediction.prediction_time)
                actual = float(task.actual_time_spent)

                error = abs(actual - predicted)
                abs_errors.append(error)
                squared_errors.append(error ** 2)

                if actual != 0:
                    percent_errors.append(error / actual * 100)

        avg_prediction = round(sum(predictions) / len(predictions), 2) if predictions else None
        avg_actual = round(sum(actual_times) / len(actual_times), 2) if actual_times else None
        mae = round(sum(abs_errors) / len(abs_errors), 2) if abs_errors else None
        rmse = round(math.sqrt(sum(squared_errors) / len(squared_errors)), 2) if squared_errors else None
        mape = round(sum(percent_errors) / len(percent_errors), 2) if percent_errors else None

        type_stats.append({
            'task_type': task_type,
            'total': tasks_by_type.count(),
            'avg_prediction': avg_prediction,
            'avg_actual': avg_actual,
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
        })

    all_abs_errors = []
    all_squared_errors = []
    all_percent_errors = []

    for task in all_tasks:
        prediction = task.predictions.order_by('-created_at').first()

        if (
            prediction and
            prediction.prediction_time is not None and
            task.actual_time_spent is not None
        ):
            predicted = float(prediction.prediction_time)
            actual = float(task.actual_time_spent)

            error = abs(actual - predicted)

            all_abs_errors.append(error)
            all_squared_errors.append(error ** 2)

            if actual != 0:
                all_percent_errors.append(error / actual * 100)

    model_mae = round(sum(all_abs_errors) / len(all_abs_errors), 2) if all_abs_errors else None
    model_rmse = round(math.sqrt(sum(all_squared_errors) / len(all_squared_errors)), 2) if all_squared_errors else None
    model_mape = round(sum(all_percent_errors) / len(all_percent_errors), 2) if all_percent_errors else None

    return render(request, 'stats/board_stats.html', {
        'board': board,
        'total_tasks': total_tasks,
        'overdue_tasks': overdue_tasks,
        'completed_tasks': completed_tasks,
        'status_stats': status_stats,
        'assignee_stats': assignee_stats,
        'type_stats': type_stats,
        'model_mae': model_mae,
        'model_rmse': model_rmse,
        'model_mape': model_mape,
    })