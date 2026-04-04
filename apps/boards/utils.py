from accounts.models import UserInGroup
from .models import Board, BoardMember, UserGroupRights


def user_has_board_access(user, board):
    if user.is_staff:
        return True

    if board.created_by == user:
        return True

    if BoardMember.objects.filter(board=board, user=user).exists():
        return True

    group_ids = UserInGroup.objects.filter(user=user).values_list('group_id', flat=True)
    if UserGroupRights.objects.filter(board=board, group_id__in=group_ids).exists():
        return True

    return False


def user_can_edit_task(user, task):
    if user.is_staff:
        return True

    if task.author == user:
        return True

    return False


def get_user_boards(user):
    if user.is_staff:
        return Board.objects.all().distinct()

    direct_board_ids = BoardMember.objects.filter(user=user).values_list('board_id', flat=True)
    group_ids = UserInGroup.objects.filter(user=user).values_list('group_id', flat=True)
    group_board_ids = UserGroupRights.objects.filter(group_id__in=group_ids).values_list('board_id', flat=True)

    return Board.objects.filter(id__in=list(direct_board_ids) + list(group_board_ids)).distinct()