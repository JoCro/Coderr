from rest_framework import generics, status, permissions, viewsets
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


class OfferViewSet(viewsets.ModelViewSet):
    """
    A CRUD ViewSet for the OFFER-Model. Gives correct permissions and serializers due to the Method which is used on the Endpoint

        - list => GET /offers/
        - retrieve => GET /offers/{id}/
        - create => POST /offers/
        - update => PUT/PATCH /offers/{id}/
        - destroy => DELETE /offers/{id}/
    """

    lookup_field = "id"
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    pagination_class = OfferListPagination
    filterset_class = OfferFilter
    search_fields = ["title", "description"]
    ordering_fields = ["updated_at", "min_price"]
    ordering = ["-updated_at"]

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

    def get_permissions(self):
        if self.action == "list":
            return []
        if self.action == "retrieve":
            return [permissions.IsAuthenticated()]
        if self.action == "create":
            return [permissions.IsAuthenticated(), IsBusinessUser()]
        if self.action in ("update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "list":
            return OfferListSerializer
        if self.action == "retrieve":
            return OfferRetrieveSerializer
        if self.action == "create":
            return OfferCreateSerializer
        if self.action in ("update", "partial_update"):
            return OfferUpdateSerializer
        return OfferListSerializer

    def perform_create(self, serializer):
        serializer.save()

    def update(self, request, *args, **kwargs):
        offer = self.get_object()
        if request.user.id != offer.user_id:
            return Response({"detail": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN,)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        offer = self.get_object()
        if request.user.id != offer.user_id:
            return Response({"detail": "You do not have permission to perform this action"}, status=status.HTTP_403_FORBIDDEN,)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        offer = self.get_object()
        if request.user.id != offer.user_id:
            return Response({"detail": "You do not have permission to perform this action"}, status=status.HTTP_403_FORBIDDEN,)
        return super().destroy(request, *args, **kwargs)


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
