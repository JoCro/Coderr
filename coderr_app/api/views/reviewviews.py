from rest_framework import generics, status, permissions, viewsets
from coderr_app.models import Profile, Offer, Review
from ..serializers import ReviewListSerializer, ReviewCreateSerializer, ReviewUpdateSerializer
from rest_framework.response import Response
from django.db.models import Avg
from ..permissions import IsCustomerUser
from rest_framework.views import APIView
from ..filters import ReviewFilter


class ReviewViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for the REVIEW-Model with appropriate permissions and serializers based on the action.:

    - list        GET    /reviews/
    - retrieve    GET    /reviews/{id}/
    - create      POST   /reviews/
    - update      PUT    /reviews/{id}/
    - partial     PATCH  /reviews/{id}/
    - destroy     DELETE /reviews/{id}/
    """
    queryset = (
        Review.objects
        .select_related("business_user", "reviewer",)
    )
    lookup_field = "id"
    ordering_fields = ["updated_at", "rating", "id", "created_at"]
    ordering = ["-updated_at",]
    filterset_class = ReviewFilter
    serializer_class = ReviewListSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        if self.action == "create":
            return [permissions.IsAuthenticated(), IsCustomerUser()]
        if self.action in ("update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "list" or self.action == "retrieve":
            return ReviewListSerializer
        if self.action == "create":
            return ReviewCreateSerializer
        if self.action in ("update", "partial_update"):
            return ReviewUpdateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)

    def update(self, request, *args, **kwargs):
        review = self.get_object()
        if request.user.id != review.reviewer_id:
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        review = self.get_object()
        if request.user.id != review.reviewer_id:
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        review = self.get_object()
        if request.user.id != review.reviewer_id:
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


class BaseInfoView(APIView):
    """
    API view for retrieving general platform statistics.

    Provides key metrics about the platform, including:
      - Total number of reviews
      - Average rating (rounded to one decimal)
      - Total number of business profiles
      - Total number of offers

    Methods:
        GET: Returns a JSON object with aggregated platform data.

    Permissions:
        - Public endpoint (no authentication required).
    """
    permission_classes = []

    def get(self, request):
        review_count = Review.objects.count()
        avg = Review.objects.aggregate(avg=Avg("rating"))["avg"]
        average_rating = round(float(avg), 1) if avg is not None else 0.0

        business_profile_count = Profile.objects.filter(
            user_type="business").count()
        offer_count = Offer.objects.count()

        data = {
            "review_count": review_count,
            "average_rating": average_rating,
            "business_profile_count": business_profile_count,
            "offer_count": offer_count,
        }
        return Response(data, status=status.HTTP_200_OK)
