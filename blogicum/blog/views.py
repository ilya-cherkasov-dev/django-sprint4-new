from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from users.forms import ProfileForm
from .forms import CommentForm, PostForm
from .mixins import CommentMixin, PostChangeMixin
from .models import Category, Comment, Post

User = get_user_model()

POSTS_BY_PAGE = 10


def get_post_queryset(manager=Post.objects, filters=True, with_comments=True):
    """Собрать queryset публикаций с общими правилами выборки."""
    queryset = manager.select_related('author', 'category', 'location')
    if filters:
        queryset = queryset.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
        )
    if with_comments:
        queryset = queryset.annotate(
            comment_count=Count('comments'),
        ).order_by('-pub_date')
    return queryset


class IndexListView(ListView):
    template_name = 'blog/index.html'
    paginate_by = POSTS_BY_PAGE

    def get_queryset(self):
        return get_post_queryset()


class CategoryListView(ListView):
    template_name = 'blog/category.html'
    paginate_by = POSTS_BY_PAGE

    @cached_property
    def category(self):
        return get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True,
        )

    def get_queryset(self):
        return get_post_queryset(self.category.posts)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class ProfileListView(ListView):
    template_name = 'blog/profile.html'
    paginate_by = POSTS_BY_PAGE

    @cached_property
    def profile(self):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_queryset(self):
        return get_post_queryset(
            self.profile.posts,
            filters=self.request.user != self.profile,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'blog/user.html'
    form_class = ProfileForm

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username},
        )


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_object(self, queryset=None):
        post = get_object_or_404(
            Post.objects.select_related('author', 'category', 'location'),
            pk=self.kwargs['post_id'],
        )
        if post.author != self.request.user and not (
            post.is_published
            and post.pub_date <= timezone.now()
            and post.category is not None
            and post.category.is_published
        ):
            raise Http404
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username},
        )


class PostUpdateView(PostChangeMixin, UpdateView):
    form_class = PostForm

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']},
        )


class PostDeleteView(PostChangeMixin, DeleteView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username},
        )


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post, pk=self.kwargs['post_id'],
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']},
        )


class CommentUpdateView(CommentMixin, UpdateView):
    form_class = CommentForm


class CommentDeleteView(CommentMixin, DeleteView):
    pass
