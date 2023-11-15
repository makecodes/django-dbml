from django.db import models
from django.contrib.auth.models import User


class Follow(models.Model):
    """The user follow model."""

    following_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following"
    )
    followed_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="followed"
    )
    created_at = models.DateTimeField(auto_now_add=True)


class Post(models.Model):
    """The post model."""

    title = models.CharField(max_length=255)
    body = models.TextField(help_text="Content of the post")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10,
        choices=(
            ("draft", "Draft"),
            ("published", "Published"),
        ),
        default="draft",
    )
    created_at = models.DateTimeField(auto_now_add=True)
