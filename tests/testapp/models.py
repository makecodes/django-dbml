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
    shelves = models.ManyToManyField("Shelf", through="BookPlacement", related_name="books")
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["title", "status"], name="book_title_status_idx"),
        ]
        unique_together = ("author", "title")
        db_table_comment = "Stores books"


class Shelf(models.Model):
    label = models.CharField(max_length=50)


class BookPlacement(models.Model):
    """Explicit ``through`` model, so no join table is synthesized for it."""

    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    shelf = models.ForeignKey(Shelf, on_delete=models.CASCADE)
    position = models.PositiveIntegerField(default=0)


class Warehouse(models.Model):
    """Mirrors the shape reported in issue #38: explicit ``AutoField`` pk and a custom ``db_table``."""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=40)

    class Meta:
        db_table = "warehouse"


class Shipment(models.Model):
    id = models.AutoField(primary_key=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    operator = models.OneToOneField(Warehouse, on_delete=models.CASCADE, related_name="operated_shipment")
    code = models.CharField(max_length=40)

    class Meta:
        db_table = "shipment_record"
