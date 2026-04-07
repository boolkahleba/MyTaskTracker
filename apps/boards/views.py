from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404

from .forms import BoardForm, BoardUpdateForm
from .models import Board, BoardStatus, BoardMember, UserGroupRights
from .utils import get_user_boards, user_has_board_access
from accounts.models import User, UserGroup


@login_required
def board_list_view(request):
    boards = get_user_boards(request.user)
    return render(request, 'boards/board_list.html', {
        'boards': boards,
    })


@login_required
def create_board_view(request):
    if not request.user.is_staff:
        raise Http404

    if request.method == 'POST':
        form = BoardForm(request.POST)
        if form.is_valid():
            board = Board.objects.create(
                name=form.cleaned_data['name'],
                description=form.cleaned_data['description'],
                created_by=request.user
            )

            statuses_text = form.cleaned_data['statuses']
            statuses = [item.strip() for item in statuses_text.split(',') if item.strip()]
            for index, status_name in enumerate(statuses):
                BoardStatus.objects.create(
                    board=board,
                    name=status_name,
                    position=index
                )

            users = form.cleaned_data['users']
            for user in users:
                BoardMember.objects.get_or_create(
                    board=board,
                    user=user,
                    defaults={'access': 'write'}
                )

            groups = form.cleaned_data['groups']
            for group in groups:
                UserGroupRights.objects.get_or_create(
                    board=board,
                    group=group,
                    defaults={'rights': 'read,write'}
                )

            return redirect('boards:board_list')
    else:
        form = BoardForm()

    return render(request, 'boards/create_board.html', {
        'form': form,
    })


@login_required
def board_detail_view(request, board_id):
    board = get_object_or_404(Board, pk=board_id)

    if not user_has_board_access(request.user, board):
        raise Http404

    statuses = board.statuses.all()
    tasks_by_status = {}
    for status in statuses:
        tasks_by_status[status] = board.tasks.filter(status=status).select_related(
            'assignee', 'author', 'status'
        ).prefetch_related('predictions')

    return render(request, 'boards/board_detail.html', {
        'board': board,
        'statuses': statuses,
        'tasks_by_status': tasks_by_status,
    })


@login_required
def update_board_view(request, board_id):
    if not request.user.is_staff:
        raise Http404

    board = get_object_or_404(Board, pk=board_id)

    initial_statuses = ', '.join(board.statuses.values_list('name', flat=True))

    if request.method == 'POST':
        form = BoardUpdateForm(request.POST, instance=board)
        if form.is_valid():
            form.save()

            board.statuses.all().delete()
            statuses_text = form.cleaned_data['statuses']
            statuses = [item.strip() for item in statuses_text.split(',') if item.strip()]

            for index, status_name in enumerate(statuses):
                BoardStatus.objects.create(
                    board=board,
                    name=status_name,
                    position=index
                )

            return redirect('boards:board_detail', board_id=board.id)
    else:
        form = BoardUpdateForm(instance=board, initial={'statuses': initial_statuses})

    return render(request, 'boards/update_board.html', {
        'form': form,
        'board': board,
    })


@login_required
def delete_board_view(request, board_id):
    if not request.user.is_staff:
        raise Http404

    board = get_object_or_404(Board, pk=board_id)

    if request.method == 'POST':
        board.delete()
        return redirect('boards:board_list')

    return render(request, 'boards/delete_board.html', {
        'board': board,
    })


@login_required
def board_access_view(request, board_id):
    if not request.user.is_staff:
        raise Http404

    board = get_object_or_404(Board, pk=board_id)

    users = User.objects.all().order_by('full_name')
    groups = UserGroup.objects.all().order_by('name')
    members = BoardMember.objects.filter(board=board).select_related('user')
    group_rights = UserGroupRights.objects.filter(board=board).select_related('group')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        group_id = request.POST.get('group_id')

        if user_id:
            user = get_object_or_404(User, pk=user_id)
            BoardMember.objects.get_or_create(
                board=board,
                user=user,
                defaults={'access': 'write'}
            )

        if group_id:
            group = get_object_or_404(UserGroup, pk=group_id)
            UserGroupRights.objects.get_or_create(
                board=board,
                group=group,
                defaults={'rights': 'read,write'}
            )

        return redirect('boards:board_access', board_id=board.id)

    return render(request, 'boards/board_access.html', {
        'board': board,
        'users': users,
        'groups': groups,
        'members': members,
        'group_rights': group_rights,
    })


@login_required
def delete_board_member_view(request, board_id, member_id):
    if not request.user.is_staff:
        raise Http404

    member = get_object_or_404(BoardMember, pk=member_id, board_id=board_id)

    if request.method == 'POST':
        member.delete()
        return redirect('boards:board_access', board_id=board_id)

    return render(request, 'boards/delete_board_member.html', {
        'member': member,
    })


@login_required
def delete_board_group_right_view(request, board_id, right_id):
    if not request.user.is_staff:
        raise Http404

    right = get_object_or_404(UserGroupRights, pk=right_id, board_id=board_id)

    if request.method == 'POST':
        right.delete()
        return redirect('boards:board_access', board_id=board_id)

    return render(request, 'boards/delete_board_group_right.html', {
        'right': right,
    })