from rest_framework import generics, status, permissions
from django.shortcuts import get_object_or_404
from coderr_app.models import Profile, Offer, OfferDetail, Order, Review
from .serializers import ProfileSerializer, BusinessProfileListSerializer, CustomerProfileListSerializer, OfferListSerializer, OfferCreateSerializer, OfferRetrieveSerializer, OfferUpdateSerializer, OfferDetailRetrieveSerializer, OrderListSerializer, OrderCreateSerializer, OrderStatusUpdateSerializer, ReviewListSerializer, ReviewCreateSerializer, ReviewUpdateSerializer
from rest_framework.response import Response
from django.db.models import Min, Q, Avg
from .pagination import OfferListPagination
from .permissions import IsBusinessUser, IsCustomerUser
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .filters import ReviewFilter
from django_filters import rest_framework as filters
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    API view for retrieving and updating user profiles.

    - GET: Returns detailed profile information for a given user ID.
    - PATCH: Allows partial profile updates, restricted to the profile owner.
    - Supports JSON and multipart/form-data for profile image uploads.
    - Returns 403 if a user attempts to edit another user’s profile.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = ProfileSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_object(self):
        user_id = self.kwargs['pk']
        return get_object_or_404(Profile.objects.select_related("user"), user__id=user_id)

    def patch(self, request, *args, **kwargs):
        obj = self.get_object()
        if request.user.id != obj.user.id:
            return Response({"detail": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)
        return super().patch(request, *args, **kwargs)


class BusinessProfileView(generics.ListAPIView):
    """
    API view for listing all business user profiles.

    - Accessible only to authenticated users.
    - Returns profiles where `user_type` is 'business'.
    - Orders results alphabetically by username.
    - Used for GET /api/profiles/business/ endpoint.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BusinessProfileListSerializer

    def get_queryset(self):
        return (Profile.objects
                .select_related("user")
                .filter(user_type='business')
                .order_by('user__username')

                )


class CustomerProfileView(generics.ListAPIView):
    """
    API view for listing all customer user profiles.

    - Accesible only to authenticated users.
    - Returns profiles where 'user-type' is customer.
    - Orders result alphabetically by username as default.
    - Used for GET /api/profiles/customer/ endpoint.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CustomerProfileListSerializer

    def get_queryset(self):
        return (Profile.objects
                .select_related("user")
                .filter(user_type='customer')
                .order_by('user__username')
                )


class OfferFilter(filters.FilterSet):
    """
    FilterSet for filtering offers based on creator, price, and delivery time.

    - `creator_id`: Filters offers by the user who created them.
    - `min_price`: Returns offers with a minimum price greater than or equal to the given value.
    - `max_delivery_time`: Returns offers with delivery time less than or equal to the given value.
    - Used in GET /api/offers/ endpoint for query-based filtering.
    """

    creator_id = filters.NumberFilter(field_name="user_id")
    min_price = filters.NumberFilter(method="filter_min_price")
    max_delivery_time = filters.NumberFilter(method="filter_max_delivery")

    class Meta:
        model = Offer
        fields = ["creator_id"]

    def filter_min_price(self, queryset, name, value):
        return queryset.filter(mind_price__gte=value)

    def filter_max_delivery(self, queryset, name, value):
        return queryset.filter(min_delivery_time__lte=value)


class OfferListCreateView(generics.ListCreateAPIView):
    """
    API view for listing and creating offers.

    - GET: Returns a paginated, filterable, and searchable list of all offers.
      Supports filters for creator, price, and delivery time.
    - POST: Allows authenticated business users to create new offers with details.
    - Uses custom pagination, filtering, and ordering.
    - Prefetches related offer details and calculates minimum price and delivery time for efficiency.
    - Used for /api/offers/ endpoint.
    """

    serializer_class = OfferListSerializer
    filterset_class = OfferFilter
    search_fields = ["title", "description"]
    ordering_fields = ["updated_at", "min_price"]
    ordering = ["-updated_at"]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    pagination_class = OfferListPagination

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsBusinessUser()]
        return []

    def get_queryset(self):
        qs = (Offer.objects
              .select_related("user")
              .prefetch_related("details")
              .annotate(
                  min_price=Min("details__price"),
                  min_delivery_time=Min("details__delivery_time"),
              )

              )

        for o in qs:
            o._prefetched_details = list(o.details.all())
        return qs

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OfferCreateSerializer
        return super().get_serializer_class()


class OfferDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a specific offer.

    - GET: Returns detailed information about an offer, including related details.
    - PATCH: Allows the offer creator to partially update the offer and its details.
    - DELETE: Permits only the creator to delete the offer.
    - Ensures ownership-based access control (403 if unauthorized).
    - Annotates minimum price and delivery time for optimized retrieval.
    - Used for /api/offers/{id}/ endpoint.
    """

    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        return (
            Offer.objects
            .select_related("user")
            .prefetch_related("details")
            .annotate(
                min_price=Min("details__price"),
                min_delivery_time=Min("details__delivery_time"),
            )
        )

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return OfferUpdateSerializer
        return OfferRetrieveSerializer

    def patch(self, request, *args, **kwargs):
        offer = self.get_object()
        if request.user.id != offer.user_id:
            return Response({"detail": "You do not have permission to perform this action."},
                            status=status.HTTP_403_FORBIDDEN)
        return super().patch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        offer = self.get_object()
        if request.user.id != offer.user_id:
            return Response({"detail": "You do not have permission to perform this action."},
                            status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(offer)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OfferDetailItemView(generics.RetrieveAPIView):
    """
    API view for retrieving a single offer detail entry.

    - GET: Returns detailed information about a specific OfferDetail.
    - Accessible only to authenticated users.
    - Uses OfferDetailRetrieveSerializer for structured output.
    - Used for /api/offerdetails/{id}/ endpoint.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OfferDetailRetrieveSerializer
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        return OfferDetail.objects.all()


class OrderListCreateView(generics.ListCreateAPIView):
    """
    API view for listing and creating orders.

    - GET: Returns all orders related to the authenticated user (as customer or business).
      Supports optional filtering by business_user_id, customer_user_id, and status.
      Staff users can view all orders.
    - POST: Allows only authenticated customers to create new orders based on OfferDetails.
    - Enforces role-based permissions and context-aware filtering.
    - Used for /api/orders/ endpoint.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderListSerializer
    pagination_class = None

    def get_queryset(self):
        u = self.request.user
        qs = Order.objects.all()
        business_user_id = self.request.query_params.get("business_user_id")
        customer_user_id = self.request.query_params.get("customer_user_id")
        status_param = self.request.query_params.get("status")

        if business_user_id:
            qs = qs.filter(business_user_id=business_user_id)
        if customer_user_id:
            qs = qs.filter(customer_user_id=customer_user_id)
        if status_param:
            qs = qs.filter(status=status_param)

        if not u.is_staff:
            allowed = Q(customer_user=u) | Q(business_user=u)
            if business_user_id and business_user_id.isdigit() and int(business_user_id) == u.id:
                pass
            elif customer_user_id and customer_user_id.isdigit() and int(customer_user_id) == u.id:
                pass
            else:
                qs = qs.filter(allowed)

        return qs.order_by("-created_at")

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsCustomerUser()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        out = OrderListSerializer(order)
        return Response(out.data, status=status.HTTP_201_CREATED)


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting specific orders.

    - GET: Returns a specific order if the authenticated user is the customer or business user.
    - PATCH: Allows only the assigned business user to update the order status.
    - DELETE: Only staff (admin) users can delete an order.
    - Uses dynamic serializer selection depending on the request method.
    - Endpoint: /api/orders/{id}/
    """

    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        u = self.request.user
        return Order.objects.filter(Q(customer_user=u) | Q(business_user=u) | Q(id__isnull=False))

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return OrderStatusUpdateSerializer
        return OrderListSerializer

    def patch(self, request, *args, **kwargs):
        order = self.get_object()

        if not (hasattr(request.user, "profile")
                and request.user.profile.user_type == "business"
                and request.user.id == order.business_user_id):
            return Response({"detail": "You do not have permission to perforn this action"}, status=status.HTTP_403_FORBIDDEN)

        return super().patch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response({"detail": "You do not have permission to perform this action"}, status=status.HTTP_403_FORBIDDEN)

        order = self.get_object()
        self.perform_destroy(order)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderCountView(APIView):
    """
    API view that returns the number of active ('in_progress') orders for a specific business user.

    - GET: Retrieves the count of all ongoing orders associated with the given business user ID.
    - Validates that the user exists and has a business profile.
    - Returns a 404 response if the user is not found or is not a business profile.
    - Endpoint: /api/order-count/{business_user_id}/
    - Permissions: Requires authentication.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, business_user_id: int):
        User = get_user_model()
        try:
            user = User.objects.select_related(
                "profile").get(pk=business_user_id)
        except User.DoesNotExist:
            return Response({"detail": "Business user not found"}, status=status.HTTP_404_NOT_FOUND)

        if not hasattr(user, "profile") or getattr(user.profile, "user_type", None) != "business":
            return Response({"detail": "Business user not found"}, status=status.HTTP_404_NOT_FOUND)

        count = Order.objects.filter(
            business_user_id=user.id, status="in_progress").count()
        return Response({"order_count": count}, status=status.HTTP_200_OK)


class CompletedOrderCountView(APIView):
    """
    API view that returns the number of completed ('completed') orders for a specific business user.

    - GET: Retrieves the count of all completed orders associated with the given business user ID.
    - Validates that the user exists and has a business profile.
    - Returns a 404 response if the user is not found or is not a business profile.
    - Endpoint: /api/completed-order-count/{business_user_id}/
    - Permissions: Requires authentication.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, business_user_id: int):
        User = get_user_model()
        try:
            user = User.objects.select_related(
                "profile").get(pk=business_user_id)
        except User.DoesNotExist:
            return Response({"detail": "Business user not found"}, status=status.HTTP_404_NOT_FOUND)

        if not hasattr(user, "profile") or getattr(user.profile, "user_type", None) != "business":
            return Response({"detail": "Business user not found"}, status=status.HTTP_404_NOT_FOUND)

        count = Order.objects.filter(
            business_user_id=user.id, status="completed").count()
        return Response({"completed_order_count": count}, status=status.HTTP_200_OK)


class ReviewListCreateView(generics.ListCreateAPIView):
    """
    API view for listing and creating reviews.

    - GET: Returns a list of all reviews. Supports filtering by `business_user_id` and `reviewer_id`,
      as well as ordering by `updated_at` or `rating`.
    - POST: Allows authenticated users with a 'customer' profile to create a new review for a business user.
      A customer can only leave one review per business user.

    Permissions:
        - GET: Any authenticated user.
        - POST: Authenticated users with a 'customer' profile only.

    Filtering & Ordering:
        - FilterSet: ReviewFilter
        - Ordering fields: ['updated_at', 'rating']
        - Default ordering: '-updated_at'
    """

    permission_classes = [permissions.IsAuthenticated]
    queryset = Review.objects.select_related("business_user", "reviewer").all()
    filterset_class = ReviewFilter
    ordering_fields = ["updated_at", "rating"]
    ordering = ["-updated_at"]
    pagination_class = None

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ReviewCreateSerializer
        return ReviewListSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsCustomerUser()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        out = ReviewListSerializer(review)
        return Response(out.data, status=status.HTTP_201_CREATED)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a specific review.

    - GET: Returns the details of a specific review by ID.
    - PATCH: Allows the review's author (reviewer) to update the 'rating' and/or 'description' fields.
    - DELETE: Allows the review's author (reviewer) to delete their review.

    Permissions:
        - Only the creator (reviewer) of a review can update or delete it.
        - Any authenticated user can retrieve reviews.

    Serializer classes:
        - GET: ReviewListSerializer
        - PATCH: ReviewUpdateSerializer

    URL Parameters:
        - id: The unique identifier of the review.
    """

    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        return Review.objects.all()

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return ReviewUpdateSerializer
        return ReviewListSerializer

    def patch(self, request, *args, **kwargs):
        review = self.get_object()
        if review.reviewer_id != request.user.id:
            return Response({"detail": "You do not have permission to perform this action."},
                            status=status.HTTP_403_FORBIDDEN)
        serializer = ReviewUpdateSerializer(
            review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        review.refresh_from_db()
        full = ReviewListSerializer(review)
        return Response(full.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        review = self.get_object()
        if review.reviewer_id != request.user.id:
            return Response({"detail": "You do not have permission to perform this action."},
                            status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(review)
        return Response(status=status.HTTP_204_NO_CONTENT)


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
