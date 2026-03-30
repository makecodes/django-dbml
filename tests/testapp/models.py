from django.db import models


class Status(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"


class Author(models.Model):
    """Stores authors used by command tests."""

    name = models.CharField(max_length=100, unique=True, help_text="Public author name", db_comment="Shown in catalogs")
    website_url = models.URLField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table_comment = "Stores authors"


class AuthorProfile(models.Model):
    author = models.OneToOneField(Author, on_delete=models.CASCADE, related_name="profile")
    ip_address = models.GenericIPAddressField(null=True, blank=True)


class Tag(models.Model):
    label = models.CharField(max_length=50)


class Book(models.Model):
    """Catalog entry used by tests."""

    title = models.CharField(max_length=200, db_index=True, help_text="Visible title")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books")
    tags = models.ManyToManyField(Tag, related_name="books")
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["title", "status"], name="book_title_status_idx"),
        ]
        unique_together = ("author", "title")
        db_table_comment = "Stores books"
