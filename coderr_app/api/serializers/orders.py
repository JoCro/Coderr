from rest_framework import serializers
from django.contrib.auth import get_user_model
from coderr_app.models import OfferDetail, Order


User = get_user_model()


class OrderListSerializer(serializers.ModelSerializer):
    """
    Serializer to present the needed information about an Order

    -Provieds all key information such as id, customer_user, business_user,title, revisions etc.
    """
    class Meta:
        model = Order
        fields = [
            "id",
            "customer_user",
            "business_user",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
            "status",
            "created_at",
            "updated_at",
        ]


class OrderCreateSerializer(serializers.Serializer):
    """
    Serializer for creating new orders based on an existing offer detail.

    - Accepts an `offer_detail_id` to generate an order from.
    - Validates that the referenced OfferDetail exists.
    - Automatically assigns the authenticated user as the customer
      and links the corresponding business user from the offer.
    - Copies relevant fields (title, price, delivery time, etc.) into the new order.
    - Used for POST /api/orders/ endpoint.
    """

    offer_detail_id = serializers.IntegerField()

    def validate_offer_detail_id(self, value):
        if not OfferDetail.objects.filter(pk=value).exists():
            raise serializers.ValidationError("OfferDetail not found")
        return value

    def create(self, validated_data):
        request = self.context["request"]
        customer = request.user

        detail = OfferDetail.objects.select_related(
            "offer__user").get(pk=validated_data["offer_detail_id"])
        business = detail.offer.user

        order = Order.objects.create(
            customer_user=customer,
            business_user=business,
            title=detail.title,
            revisions=detail.revisions,
            delivery_time_in_days=detail.delivery_time,
            price=detail.price,
            features=detail.features or [],
            offer_type=detail.offer_type,
        )
        return order


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating the status of an existing order.

    - Allows modification of the `status` field only.
    - Validates that no other fields are included in the update request.
    - Ensures the new status value is one of the allowed `Order.STATUS_CHOICES`.
    - Used for PATCH /api/orders/{id}/ endpoint.
    """

    class Meta:
        model = Order
        fields = ["status"]
        extra_kwargs = {"status": {"required": True}}

    def validate(self, attrs):
        extra = set(self.initial_data.keys()) - {"status"}
        if extra:
            raise serializers.ValidationError("Only 'status' may be updated")

        status_value = attrs.get("status")
        valid = {k for k, _ in Order.STATUS_CHOICES}
        if status_value not in valid:
            raise serializers.ValidationError(
                {"status": f"Invalid status. Allowed: {', '.join(sorted(valid))}"})
        return attrs
