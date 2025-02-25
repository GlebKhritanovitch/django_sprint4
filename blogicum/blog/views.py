from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import UpdateView
from .forms import CommentForm, PostCreateForm, ProfileEditForm
from .models import Category, Comments, Post, User
# Create your views here.


def index(request):
    template = 'blog/index.html'

    posts = (
        Post.objects.filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True
        )
        .annotate(comment_count=Count('comments'))
        .order_by('-pub_date')
    )
    paginator = Paginator(posts, 10)  # Количество постов на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'page_obj': page_obj}
    return render(request, template, context)


def post_detail(request, id):
    template = 'blog/detail.html'
    post = get_object_or_404(Post, id=id)

    if post.pub_date > timezone.now():
        if post.author != request.user:
            raise Http404("Публикация еще не доступна.")

    # Проверяем, что публикация опубликована
    if not post.is_published and post.author != request.user:
        raise Http404("Публикация скрыта.")

    # Проверяем, что категория публикации опубликована
    if not post.category.is_published:
        if post.author == request.user:
            pass
        else:
            raise Http404("Категория этой публикации скрыта.")

    form = CommentForm()
    context = {'post': post, 'form': form,
               'comments': post.comments.select_related('author')}
    return render(request, template, context)


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(
        Category, slug=category_slug, is_published=True)
    posts = (
        Post.objects.filter(
            category=category,
            is_published=True,
            pub_date__lte=timezone.now()
        )
        .order_by('-pub_date')
        .annotate(comment_count=Count('comments'))
    )
    paginator = Paginator(posts, 10)  # Количество постов на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'category': category, 'page_obj': page_obj}
    return render(request, template, context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    if request.user == user:
        posts = Post.objects.filter(author=user).annotate(
            comment_count=Count('comments')).order_by('-pub_date')
    else:
        posts = Post.objects.filter(
            author=user, is_published=True,
            category__is_published=True,
            pub_date__lt=timezone.now()
        ).annotate(comment_count=Count('comments')).order_by('-pub_date')
    paginator = Paginator(posts, 10)  # Количество постов на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'profile': user, 'page_obj': page_obj}
    return render(request, 'blog/profile.html', context)


@login_required
def create_post(request):
    template = 'blog/create.html'
    form = PostCreateForm(request.POST or None, files=request.FILES or None)
    context = {'form': form}
    if form.is_valid():
        fields = form.save(commit=False)
        fields.author = request.user
        fields.save()
        return redirect('blog:profile', request.user.username)
    return render(request, template, context)


@login_required
def edit_profile(request):
    template = 'blog/user.html'
    form = ProfileEditForm(request.POST or None, instance=request.user)
    context = {'form': form}
    if form.is_valid():
        form.save()
        return redirect('blog:profile', request.user.username)
    return render(request, template, context)


@login_required
def edit_post(request, id):
    template = 'blog/create.html'
    obj = get_object_or_404(Post, id=id)
    if obj.author != request.user:
        return redirect('blog:post_detail', id=id)
    form = PostCreateForm(request.POST or None,
                          files=request.FILES or None, instance=obj)
    context = {'form': form}
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', id=id)
    return render(request, template, context)


@login_required
def delete_post(request, id):
    post = get_object_or_404(Post, id=id)
    if post.author != request.user:
        return redirect('blog:post_detail', id=id)

    if request.method == "GET":
        form = PostCreateForm(instance=post)  # Передаем форму в шаблон
        return render(request, 'blog/create.html', {'form': form})

    # Если POST-запрос — удаляем пост
    if request.method == "POST":
        post.delete()
        return redirect('blog:profile', username=request.user.username)

    return redirect('blog:post_detail', id=id)


@login_required
def add_comment(request, id):
    post_info = get_object_or_404(Post, id=id)
    form = CommentForm(request.POST)
    if form.is_valid():
        text = form.save(commit=False)
        text.author = request.user
        text.post_info = post_info
        text.save()
    return redirect('blog:post_detail', id=id)


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comments
    fields = ['text']
    context_object_name = 'comment'
    template_name = 'blog/comment.html'

    def get_object(self):
        return get_object_or_404(Comments, id=self.kwargs['slug'])

    # Проверка на авторство перед выполнением любого метода
    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != self.request.user:
            return redirect('blog:post_detail', id=self.kwargs['id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', args=[self.kwargs['id']])
# @login_required
# def edit_comment(request, id, slug):
#     tamplate = 'blog/comment.html'
#     post = get_object_or_404(Post, id=id)
#     comment = get_object_or_404(Comments, id=slug)

#     if comment.author != request.user:
#         return redirect('blog:post_detail', id=id)

#     form = CommentForm(request.POST, instance=comment)

#     if form.is_valid():
#         form.save()
#         return redirect('blog:post_detail', id=id)

#     context = {'form': form, 'post': post, 'comment': comment}


#     return render(request, tamplate, context)


@login_required
def delete_comment(request, id, slug):
    tamplate = 'blog/comment.html'
    comment = get_object_or_404(Comments, id=slug)
    if comment.author != request.user:
        return redirect('blog:post_detail', id=id)

    if request.method == "GET":
        context = {'comment': comment}
        return render(request, tamplate, context)

    if request.method == "POST":
        comment.delete()
        return redirect('blog:post_detail', id=id)

    return redirect('blog:post_detail', id=id)
