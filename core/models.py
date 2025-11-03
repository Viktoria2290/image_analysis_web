from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return f"{self.user.username} Profile"


class Document(models.Model):
    STATUS_UPLOADED = 'uploaded'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_UPLOADED, 'Uploaded'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]

    FILE_TYPE_PNG = 'png'
    FILE_TYPE_OTHER = 'other'

    FILE_TYPE_CHOICES = [
        (FILE_TYPE_PNG, 'PNG'),
        (FILE_TYPE_OTHER, 'Other'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    file_path = models.CharField(max_length=500)
    original_name = models.CharField(max_length=255)
    size = models.BigIntegerField()
    file_type = models.CharField(
        max_length=10,
        choices=FILE_TYPE_CHOICES,
        default=FILE_TYPE_PNG
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default=STATUS_UPLOADED
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    analysis_result = models.JSONField(blank=True, null=True)
    proxy_document_id = models.CharField(max_length=100, blank=True, null=True)
    external_metadata = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'documents'
        ordering = ['-uploaded_at']

    def get_file_type_display(self):
        return self.file_type.upper()

    def is_uploaded(self):
        return self.status == self.STATUS_UPLOADED

    def is_processing(self):
        return self.status == self.STATUS_PROCESSING

    def is_completed(self):
        return self.status == self.STATUS_COMPLETED

    def is_failed(self):
        return self.status == self.STATUS_FAILED

    def __str__(self):
        return self.original_name


class Pricing(models.Model):
    UNIT_PAGE = 'page'
    UNIT_DOCUMENT = 'document'
    UNIT_MB = 'mb'
    UNIT_HOUR = 'hour'

    UNIT_CHOICES = [
        (UNIT_PAGE, 'Page'),
        (UNIT_DOCUMENT, 'Document'),
        (UNIT_MB, 'Megabyte'),
        (UNIT_HOUR, 'Hour'),
    ]

    service_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    unit_type = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        default=UNIT_PAGE
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pricing'
        ordering = ['service_name']

    def __str__(self):
        return f"{self.service_name} - ${self.price_per_unit:.2f}"


class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    pricing = models.ForeignKey(
        Pricing,
        on_delete=models.CASCADE
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    proxy_order_id = models.CharField(max_length=100, blank=True, null=True)
    external_order_data = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.pk} - {self.document.original_name}"

    def is_pending(self):
        return self.status == self.STATUS_PENDING

    def is_processing(self):
        return self.status == self.STATUS_PROCESSING

    def is_completed(self):
        return self.status == self.STATUS_COMPLETED

    def is_cancelled(self):
        return self.status == self.STATUS_CANCELLED

    def can_be_cancelled(self):
        return self.status in [self.STATUS_PENDING, self.STATUS_PROCESSING]


@receiver(post_save, sender=User)
def create_user_profile(instance, created, **_):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(instance, **_):
    instance.profile.save()