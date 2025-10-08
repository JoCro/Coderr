from rest_framework import generics, permissions
from django_filters import rest_framework as filters
from coderr_app.models import Review
from .serializers import ReviewListSerializer


class ReviewFilter(filters.FilterSet):
    """
    Enables filtering of reviews by business user or reviewer.

    - `business_user_id`: Filters reviews for a specific business user.
    - `reviewer_id`: Filters reviews created by a specific reviewer.

    Used in GET /api/reviews/ for query-based filtering.
    """
    business_user_id = filters.NumberFilter(field_name="business_user_id")
    reviewer_id = filters.NumberFilter(field_name="reviewer_id")
    offer_id = filters.NumberFilter(field_name="offer_id")

    class Meta:
        model = Review
        fields = ["business_user_id", "reviewer_id", "offer_id"]
