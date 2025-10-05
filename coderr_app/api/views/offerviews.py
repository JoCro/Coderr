from rest_framework import generics, status, permissions
from coderr_app.models import Offer, OfferDetail
from ..serializers import OfferListSerializer, OfferCreateSerializer, OfferRetrieveSerializer, OfferUpdateSerializer, OfferDetailRetrieveSerializer
from rest_framework.response import Response
from django.db.models import Min
from ..pagination import OfferListPagination
from ..permissions import IsBusinessUser
from django_filters import rest_framework as filters
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser


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
