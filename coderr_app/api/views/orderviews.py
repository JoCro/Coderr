from rest_framework import generics, status, permissions
from coderr_app.models import Order
from ..serializers import OrderListSerializer, OrderCreateSerializer, OrderStatusUpdateSerializer
from rest_framework.response import Response
from django.db.models import Q
from ..permissions import IsCustomerUser
from rest_framework.views import APIView
from django.contrib.auth import get_user_model


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
