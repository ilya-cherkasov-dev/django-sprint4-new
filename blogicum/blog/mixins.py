from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from .models import Comment, Post


class PostChangeMixin:
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect(
                'blog:post_detail', post_id=self.kwargs['post_id'],
            )
        return super().dispatch(request, *args, **kwargs)


class CommentMixin:
    model = Comment
    template_name = 'blog/comment.html'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Comment,
            pk=self.kwargs['comment_id'],
            post_id=self.kwargs['post_id'],
        )

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect(
                'blog:post_detail', post_id=self.kwargs['post_id'],
            )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']},
        )
