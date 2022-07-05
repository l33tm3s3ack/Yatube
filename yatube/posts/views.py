from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import post_listing


@cache_page(timeout=20, key_prefix='index_page')
def index(request):
    """Отображение главной страницы сайта"""
    post_list = Post.objects.select_related('group')
    template = '../templates/posts/index.html'
    context = {
        'page_obj': post_listing(post_list, request),
    }
    return render(request, template, context)


def group_posts(request, slug):
    """Отображение страницы постов группы"""
    group = get_object_or_404(Group, slug=slug)
    template = '../templates/posts/group_list.html'
    posts = group.group_posts.all()
    context = {
        'group': group,
        'page_obj': post_listing(posts, request),
    }
    return render(request, template, context)


def profile(request, username):
    """Отображение профиля пользователя и его сообщений"""
    profile_user = get_object_or_404(User, username=username)
    template = 'posts/profile.html'
    posts = profile_user.posts.all()
    post_count = posts.count()
    if request.user.is_authenticated and Follow.objects.filter(
            user=request.user, author=profile_user).exists():
        following = True
    else:
        following = False
    context = {
        'post_count': post_count,
        'username': profile_user,
        'page_obj': post_listing(posts, request),
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    """Отображении детальной информации о посте"""
    post = get_object_or_404(Post.objects.select_related('author'), pk=post_id)
    post_count = post.author.posts.count()
    template = 'posts/post_detail.html'
    form = CommentForm()
    comments = post.comment.all()
    context = {
        'form': form,
        'post': post,
        'post_count': post_count,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    """Отображение формы для создания нового поста"""
    template = 'posts/create_post.html'
    groups = Group.objects.all()
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.author = request.user
        obj.save()
        return redirect(reverse('posts:profile',
                        kwargs={'username': obj.author.username}))
    context = {
        'form': form,
        'groups': groups,
        'is_edit': False
    }
    return render(request, template, context)


def post_edit(request, post_id):
    """Отображение формы для редактирования поста"""
    template = 'posts/create_post.html'
    groups = Group.objects.all()
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect(reverse('posts:post_detail',
                        kwargs={'post_id': post_id}))
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect(reverse('posts:post_detail',
                        kwargs={'post_id': post_id}))
    context = {
        'post': post,
        'form': form,
        'groups': groups,
        'is_edit': True
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    """Добавление комментария к посту."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Просмотр записей, на которых подписан пользователь"""
    author_list = Follow.objects.filter(user=request.user).values('author')
    posts = Post.objects.filter(author__in=author_list)
    context = {'page_obj': post_listing(posts, request), }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора"""
    author = get_object_or_404(User, username=username)
    if request.user != author:
        if not Follow.objects.filter(
                user=request.user, author=author).exists():
            Follow.objects.create(user=request.user, author=author)
        return redirect('posts:follow_index')
    return redirect(reverse('posts:profile', args=[author.username]))


@login_required
def profile_unfollow(request, username):
    """Перестать читать автора"""
    author = User.objects.get(username=username)
    if Follow.objects.filter(user=request.user, author=author).exists():
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:main_page')
