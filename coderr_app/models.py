from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.


class Profile(models.Model):
    """
    Represents a user profile associated with a Django User model. 
    This model extends the default user by storing additional profile-related information, 
    distingusishing between tow user types -customer and -business.
    """

    TYPE_CHOICES = (
        ('customer', 'Customer'),
        ('business', 'Business'),
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    file = models.ImageField(upload_to='profiles/', blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    tel = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    working_hours = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.user_type})"


class Offer(models.Model):
    """
    Represents an Offer by its given fields.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, related_name='offers')
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='offers/', blank=True, null=True)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.user.username}"


class OfferDetail(models.Model):
    """
    Represents Details about an offer with additional fields to extend the information of the Offer-Model
    """
    OFFER_TYPE_CHOICES = (("basic", "basic"), ("standard",
                          "standard"), ("premium", "premium"))
    offer = models.ForeignKey(
        Offer, on_delete=models.CASCADE, related_name='details')
    title = models.CharField(max_length=255)
    revisions = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_time = models.PositiveIntegerField()
    features = models.JSONField(default=list, blank=True)
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPE_CHOICES)

    def __str__(self):
        return f"{self.title} (offer{self.offer_id})"


class Order(models.Model):
    """
    Represents an order placed by a customer for a business offer.

    This model stores transactional data between customers and business users,
    including pricing, delivery time, and order status.
    """

    STATUS_CHOICES = (
        ("pending", "pending"),
        ("in_progress", "in_progress"),
        ("completed", "completed"),
        ("cancelled", "cancelled"),
    )

    customer_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_orders"
    )

    business_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="business_orders"
    )

    title = models.CharField(max_length=255)
    revisions = models.PositiveIntegerField()
    delivery_time_in_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list, blank=True)
    offer_type = models.CharField(max_length=20)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="in_progress")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id}: {self.title} ({self.customer_user_id} -> {self.business_user_id})"


class Review(models.Model):
    """
    Represents a Review placed by a customer account for a business account. 
    This model makes sure, that the Rating of a business-user must be in the range from 1 to 5
    """
    business_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_reviews"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="written_reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)])
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business_user", "reviewer"], name="uniq_review_per_business_per_reviewer")
        ]
        indexes = [
            models.Index(fields=["business_user"]),
            models.Index(fields=["reviewer"]),
            models.Index(fields=["rating"]),
            models.Index(fields=["-updated_at"]),
        ]

    def __str__(self):
        return f"Review {self.id} by {self.reviewer_id} -> {self.business_user_id} ({self.rating})"
