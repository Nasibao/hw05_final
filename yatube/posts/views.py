from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.urls import reverse

from .forms import PostForm, CommentForm
from .models import Follow, Group, Post
from .paginator import get_page_obj

User = get_user_model()


@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    template = "posts/index.html"
    context = {
        "page_obj": get_page_obj(request, post_list),
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = "posts/group_list.html"
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    context = {
        "group": group,
        "page_obj": get_page_obj(request, posts),
    }
    return render(request, template, context)


def profile(request, username):
    template = "posts/profile.html"
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author).exists()

    context = {
        "author": author,
        "page_obj": get_page_obj(request, posts),
        "following": following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    form = CommentForm()
    user_posts_count = post.author.posts.all().count()
    context = {
        "post": post,
        'comments': comments,
        'form': form,
        "user_posts_count": user_posts_count,
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        author = request.user
        form.instance.author = author
        form.save()
        return redirect(reverse("posts:profile", args=[author.username]))
    return render(request, "posts/post_create.html", {"form": form})


@login_required
def post_edit(request, post_id):
    template = "posts/post_create.html"
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect("posts:post_detail", post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect(reverse("posts:post_detail", args=[post_id]))
    context = {
        "form": form,
        "is_edit": True,
        "post": post,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
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
    posts = Post.objects.filter(
        author__following__user=request.user)
    context = {"page_obj": get_page_obj(request, posts)}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author:
        Follow.objects.get_or_create(
            user=user,
            author=author,
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        user=request.user, author__username=username).delete()
    return redirect('posts:profile', username=username)
