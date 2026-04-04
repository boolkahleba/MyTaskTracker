from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404

from .forms import RegisterForm, LoginForm, UserGroupForm, UserInGroupForm
from .models import User, UserGroup, UserInGroup


def register_view(request):
    submitted = False
    if 'sub' in request.GET:
        submitted = True

    if request.user.is_authenticated:
        return redirect('boards:board_list')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('boards:board_list')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {
        'form': form,
        'submitted': submitted,
    })


def login_view(request):
    submitted = False
    if 'sub' in request.GET:
        submitted = True

    if request.user.is_authenticated:
        return redirect('boards:board_list')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            return redirect('boards:board_list')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {
        'form': form,
        'submitted': submitted,
    })


@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {
        'profile_user': request.user,
    })


@login_required
def user_list_view(request):
    if not request.user.is_staff:
        raise Http404

    users = User.objects.all().order_by('full_name')
    return render(request, 'accounts/user_list.html', {
        'users': users,
    })


@login_required
def group_list_view(request):
    groups = UserGroup.objects.all().order_by('name')
    return render(request, 'accounts/group_list.html', {
        'groups': groups,
    })


@login_required
def create_group_view(request):
    if not request.user.is_staff:
        raise Http404

    if request.method == 'POST':
        form = UserGroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            return redirect('accounts:group_list')
    else:
        form = UserGroupForm()

    return render(request, 'accounts/create_group.html', {
        'form': form,
    })


@login_required
def group_detail_view(request, group_id):
    group = get_object_or_404(UserGroup, pk=group_id)
    members = UserInGroup.objects.filter(group=group).select_related('user')
    users = User.objects.all().order_by('full_name')

    if request.method == 'POST':
        if not request.user.is_staff:
            raise Http404

        user_id = request.POST.get('user_id')
        if user_id:
            user = get_object_or_404(User, pk=user_id)
            UserInGroup.objects.get_or_create(group=group, user=user)
            return redirect('accounts:group_detail', group_id=group.id)

    return render(request, 'accounts/group_detail.html', {
        'group': group,
        'members': members,
        'users': users,
    })


@login_required
def delete_group_member_view(request, group_id, member_id):
    if not request.user.is_staff:
        raise Http404

    member = get_object_or_404(UserInGroup, pk=member_id, group_id=group_id)

    if request.method == 'POST':
        member.delete()
        return redirect('accounts:group_detail', group_id=group_id)

    return render(request, 'accounts/delete_group_member.html', {
        'member': member,
    })