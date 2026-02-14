from django.shortcuts import render, redirect
from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views import generic
from django.db.models import Q
from django.http import Http404


@login_required
def home(request):
    groups = request.user.profile.group.all()
    context = {
        'groups': groups,
    }
    return render(request, 'groupapp/home.html', context)


@login_required
def profile(request):
    if request.method == "POST":
        p_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=request.user.profile)
        if p_form.is_valid():
            p_form.save()
            messages.success(request, f'Profile successfully Updated!')
            return redirect('home')
    else:
        try:
            p_form = ProfileUpdateForm(instance=request.user.profile)
        except:
            p_form = ProfileUpdateForm()
    context = {'p_form': p_form}
    return render(request, 'groupapp/profile.html', context)


def register(request):
    if request.method == "POST":
        u_form = UserRegisterForm(request.POST)
        if u_form.is_valid():
            u_form.save()
            username = u_form.cleaned_data.get('username')
            messages.success(request, f'Account Created for {username}!')
            return redirect('profile')
    else:
        u_form = UserRegisterForm()
    return render(request, 'groupapp/register.html', {'u_form': u_form})


def groups(request):
    groups = Group.objects.filter(~Q(id__in=request.user.profile.group.all()))
    context = {
        'groups': groups,
    }
    return render(request, 'groupapp/group_list.html', context)


# class GroupDetailView(generic.DetailView):
#     model = Group

#     def get_context_data(self, **kwargs):
#         context = super(GroupDetailView, self).get_context_data(**kwargs)
#         user_groups = self.request.user.profile.group.all()
#         context['user_groups'] = user_groups
#         posts = Post.objects.filter(group=self.kwargs['pk'])
#         context['posts'] = posts
#         context['post_form'] = PostForm()
#         context['comment_form'] = PostCommentForm()
#         return context


def group_detail(request, pk=None):
    try:
        request.user.profile.group.get(id=pk)
        group = Group.objects.get(id=pk)
        user_groups = request.user.profile.group.all()
        posts = Post.objects.filter(group=pk)
        context = {
            'group': group,
            'comment_form': PostCommentForm(),
            'post_form': PostForm(),
            'posts': posts,
            'user_groups': user_groups,
        }
        return render(request, 'groupapp/group_detail.html', context)
    except:
        raise Http404("You are not authorised")


def add_post(request, pk=None):
    post_form = PostForm(request.POST, request.FILES)
    if post_form.is_valid():
        post = post_form.save(commit=False)
        post.group = Group.objects.get(id=pk)
        post.profile = request.user.profile
        post.save()
    return redirect(f'/group_detail/{pk}')


def profile_detail(request, pk=None):
    profile = Profile.objects.get(id=pk)
    return render(request, 'groupapp/profile_detail.html', {'profile': profile})


def join(request, pk=None):
    request.user.profile.group.add(Group.objects.get(id=pk))
    return redirect(f'/group_detail/{pk}')


def leave(request, pk=None):
    request.user.profile.group.remove(Group.objects.get(id=pk))
    return redirect('group_list')


def cat_list(request, pk=None):
    groups = Group.objects.filter(category=pk)
    return render(request, 'groupapp/cat_list.html', {'groups': groups})
