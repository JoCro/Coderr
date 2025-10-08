from rest_framework import generics, status, permissions, viewsets
from coderr_app.models import Profile, Offer, Review
from ..serializers import ReviewListSerializer, ReviewCreateSerializer, ReviewUpdateSerializer
from rest_framework.response import Response
from django.db.models import Avg
from ..permissions import IsCustomerUser
from rest_framework.views import APIView
from ..filters import ReviewFilter


# class ReviewListCreateView(generics.ListCreateAPIView):
#     """
#     API view for listing and creating reviews.

#     - GET: Returns a list of all reviews. Supports filtering by `business_user_id` and `reviewer_id`,
#       as well as ordering by `updated_at` or `rating`.
#     - POST: Allows authenticated users with a 'customer' profile to create a new review for a business user.
#       A customer can only leave one review per business user.

#     Permissions:
#         - GET: Any authenticated user.
#         - POST: Authenticated users with a 'customer' profile only.

#     Filtering & Ordering:
#         - FilterSet: ReviewFilter
#         - Ordering fields: ['updated_at', 'rating']
#         - Default ordering: '-updated_at'
#     """

#     permission_classes = [permissions.IsAuthenticated]
#     queryset = Review.objects.select_related("business_user", "reviewer").all()
#     filterset_class = ReviewFilter
#     ordering_fields = ["updated_at", "rating"]
#     ordering = ["-updated_at"]
#     pagination_class = None

#     def get_serializer_class(self):
#         if self.request.method == "POST":
#             return ReviewCreateSerializer
#         return ReviewListSerializer

#     def get_permissions(self):
#         if self.request.method == "POST":
#             return [permissions.IsAuthenticated(), IsCustomerUser()]
#         return [permissions.IsAuthenticated()]

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(
#             data=request.data, context={"request": request})
#         serializer.is_valid(raise_exception=True)
#         review = serializer.save()
#         out = ReviewListSerializer(review)
#         return Response(out.data, status=status.HTTP_201_CREATED)


# class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
#     """
#     API view for retrieving, updating, and deleting a specific review.

#     - GET: Returns the details of a specific review by ID.
#     - PATCH: Allows the review's author (reviewer) to update the 'rating' and/or 'description' fields.
#     - DELETE: Allows the review's author (reviewer) to delete their review.

#     Permissions:
#         - Only the creator (reviewer) of a review can update or delete it.
#         - Any authenticated user can retrieve reviews.

#     Serializer classes:
#         - GET: ReviewListSerializer
#         - PATCH: ReviewUpdateSerializer

#     URL Parameters:
#         - id: The unique identifier of the review.
#     """

#     permission_classes = [permissions.IsAuthenticated]
#     lookup_field = "id"
#     lookup_url_kwarg = "id"

#     def get_queryset(self):
#         return Review.objects.all()

#     def get_serializer_class(self):
#         if self.request.method == "PATCH":
#             return ReviewUpdateSerializer
#         return ReviewListSerializer

#     def patch(self, request, *args, **kwargs):
#         review = self.get_object()
#         if review.reviewer_id != request.user.id:
#             return Response({"detail": "You do not have permission to perform this action."},
#                             status=status.HTTP_403_FORBIDDEN)
#         serializer = ReviewUpdateSerializer(
#             review, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         review.refresh_from_db()
#         full = ReviewListSerializer(review)
#         return Response(full.data, status=status.HTTP_200_OK)

#     def delete(self, request, *args, **kwargs):
#         review = self.get_object()
#         if review.reviewer_id != request.user.id:
#             return Response({"detail": "You do not have permission to perform this action."},
#                             status=status.HTTP_403_FORBIDDEN)
#         self.perform_destroy(review)
#         return Response(status=status.HTTP_204_NO_CONTENT)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    CRUD für Reviews:
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

    # Falls du Search/Ordering nicht brauchst, reicht DjangoFilterBackend:

    # unterstützt business_user_id / reviewer_id aus deiner bisherigen View
    filterset_class = ReviewFilter

    # Fallback-Serializer (wird durch get_serializer_class überschrieben)
    serializer_class = ReviewListSerializer

    def get_permissions(self):
        # Liste/Detail öffentlich wie zuvor (falls du das bei dir so hattest)
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        # Anlegen: nur eingeloggte Customer
        if self.action == "create":
            return [permissions.IsAuthenticated(), IsCustomerUser()]
        # Ändern/Löschen: nur der Ersteller (Owner-Check folgt unten) & eingeloggt
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

    # Reviewer wird serverseitig gesetzt; NICHT vom Frontend erwarten
    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)

    # Owner-Check: nur der Reviewer darf sein Review ändern/löschen
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
