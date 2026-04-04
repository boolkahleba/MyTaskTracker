from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from boards.models import Board
from boards.utils import user_has_board_access
from tasks.models import Task


@login_required
def board_stats_view(request, board_id):
    board = get_object_or_404(Board, pk=board_id)

    if not request.user.is_staff:
        raise Http404

    if not user_has_board_access(request.user, board):
        raise Http404

    all_tasks = Task.objects.filter(board=board)

    total_tasks = all_tasks.count()
    overdue_tasks = all_tasks.filter(due_date__lt=timezone.now().date()).exclude(
        status__name__in=['Готово', 'Done', 'Completed', 'Завершено']
    ).count()

    status_stats = all_tasks.values('status__name').annotate(total=Count('id')).order_by('status__name')
    assignee_stats = all_tasks.values('assignee__full_name').annotate(total=Count('id')).order_by('assignee__full_name')
    avg_time = all_tasks.aggregate(avg_value=Avg('actual_time_spent'))['avg_value']

    completed_tasks = all_tasks.filter(status__name__in=['Готово', 'Done', 'Completed', 'Завершено']).count()

    return render(request, 'stats/board_stats.html', {
        'board': board,
        'total_tasks': total_tasks,
        'overdue_tasks': overdue_tasks,
        'completed_tasks': completed_tasks,
        'status_stats': status_stats,
        'assignee_stats': assignee_stats,
        'avg_time': avg_time,
    })