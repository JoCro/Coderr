from rest_framework import serializers
from django.contrib.auth import get_user_model
from coderr_app.models import Offer, OfferDetail
from django.urls import reverse
from ..fields import Base64ImageField


User = get_user_model()


class OfferDetailSerializer(serializers.Serializer):
    """
    Serializer for minimal offer detail representation.

    - Returns the offer detail ID and its API URL.
    - Used within offer listings to reference related offer detail endpoints.
    """

    id = serializers.IntegerField()
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        return f"/offerdetails/{obj.id}/"


class OfferListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing offers with summary details.

    - Includes offer metadata, pricing, delivery time, and related detail URLs.
    - Embeds basic creator information (username, first/last name).
    - Returns absolute image URLs when available.
    - Used in GET /api/offers/ for paginated offer listings.
    """

    user = serializers.IntegerField(source="user.id", read_only=True)
    details = serializers.SerializerMethodField()
    min_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True)
    min_delivery_time = serializers.IntegerField(read_only=True)
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            "id", "user", "title", "image", "description",
            "created_at", "updated_at", "details", "min_price", "min_delivery_time",
            "user_details",
        ]

    def get_details(self, obj):
        data = []
        for d in getattr(obj, "_prefetched_details", obj.details.all()):
            data.append({"id": d.id, "url": f"/offerdetails/{d.id}/"})
        return data

    def get_user_details(self, obj):
        u = obj.user
        return {
            "fist_name": u.first_name or "",
            "last_name": u.last_name or "",
            "username": u.username,
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.image:
            request = self.context.get("request")
            url = instance.image.url
            data["image"] = request.build_absolute_uri(url) if request else url
        else:
            data["image"] = None
        return data


class OfferDetailCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating offer detail entries.

    - Handles offer detail data including title, price, delivery time, and features.
    - Maps `delivery_time_in_days` to the model field `delivery_time`.
    - Allows an optional list of feature strings.
    - Used when creating or updating offers with nested detail data.
    """

    delivery_time_in_days = serializers.IntegerField(source="delivery_time")
    features = serializers.ListField(
        child=serializers.CharField(), allow_empty=True, required=False)

    class Meta:
        model = OfferDetail
        fields = ["id", "title", "revisions",
                  "delivery_time_in_days", "price", "features", "offer_type"]
        read_only_fields = ["id"]


class OfferCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new offers with nested offer details.

    - Accepts a Base64-encoded image and a list of at least 3 offer details.
    - Automatically assigns the authenticated user as the offer creator.
    - Validates the presence and structure of nested detail data.
    - Returns a structured response including created details and image reference.
    """

    image = Base64ImageField(required=False, allow_null=True)
    details = OfferDetailCreateSerializer(many=True)

    class Meta:
        model = Offer
        fields = ["id", "title", "image", "description", "details"]
        read_only_fields = ["id"]

    def validate_details(self, value):
        if not isinstance(value, list) or len(value) < 3:
            raise serializers.ValidationError(
                "An offer must contain at least 3 details")
        return value

    def create(self, validated_data):
        details_data = validated_data.pop("details", [])

        if "image" in validated_data and not validated_data["image"]:
            validated_data["image"] = None

        user = self.context["request"].user
        offer = Offer.objects.create(user=user, **validated_data)
        OfferDetail.objects.bulk_create(
            [OfferDetail(offer=offer, **d) for d in details_data])
        offer.refresh_from_db()
        return offer

    def to_representation(self, instance):
        data = {

            "id": instance.id,
            "title": instance.title,
            "image": (instance.image.name if instance.image else None),
            "description": instance.description,
            "details": [
                {
                    "id": d.id,
                    "title": d.title,
                    "revisions": d.revisions,
                    "delivery_time_in_days": d.delivery_time,
                    "price": float(d.price),
                    "features": d.features or [],
                    "offer_type": d.offer_type,
                }
                for d in instance.details.all().order_by("id")
            ],

        }
        return data


class OfferRetrieveSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving detailed information about a specific offer.

    - Includes offer metadata, image, pricing, and delivery information.
    - Provides absolute URLs for all related offer details.
    - Automatically formats image references if available.
    - Used for GET /api/offers/{id}/ endpoint.
    """

    user = serializers.IntegerField(source="user.id", read_only=True)
    details = serializers.SerializerMethodField()
    min_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True)
    min_delivery_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = Offer
        fields = [
            "id", "user", "title", "image", "description", "created_at", "updated_at", "details", "min_price", "min_delivery_time",
        ]

    def get_details(self, obj):
        request = self.context.get("request")
        items = []
        for d in obj.details.all():
            path = reverse("offer-detail-item", kwargs={"id": d.id})
            url = request.build_absolute_uri(path) if request else path
            items.append({"id": d.id, "url": url})
        return items

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get("image") is None and instance.image:
            data["image"] = instance.image.name
        return data


class OfferDetailPatchSerializer(serializers.Serializer):
    """
    Serializer for partial updates to offer detail entries.

    - Supports updating specific fields such as title, price, or delivery time.
    - Requires an `offer_type` to identify which detail is being modified.
    - Validates that at least one updatable field is provided.
    - Used for PATCH operations within offer updates.
    """

    id = serializers.IntegerField(required=False)
    offer_type = serializers.ChoiceField(choices=[(
        "basic", "basic"), ("standard", "standard"), ("premium", "premium")], required=True)
    title = serializers.CharField(required=False, allow_blank=True)
    revisions = serializers.IntegerField(required=False, min_value=0)
    delivery_time_in_days = serializers.IntegerField(
        required=False, min_value=0)
    price = serializers.DecimalField(
        required=False, max_digits=10, decimal_places=2)
    features = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True)

    def validate(self, attrs):
        change_fields = {"title", "revisions",
                         "delivery_time_in_days", "price", "features"}
        if not any(k in attrs for k in change_fields):
            raise serializers.ValidationError(
                "No update fields provided for detail")
        return attrs


class OfferUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing offers and their details.

    - Allows partial updates of offer fields (title, description, image).
    - Supports nested updates for related offer details via `OfferDetailPatchSerializer`.
    - Ensures that each updated detail belongs to the current offer.
    - Validates and handles both ID-based and offer_type-based detail identification.
    - Used for PATCH /api/offers/{id}/ endpoint.
    """

    details = OfferDetailPatchSerializer(many=True, required=False)

    class Meta:
        model = Offer
        fields = ["title", "image", "description", "details"]

    def update(self, instance, validated_data):
        for attr in ["title", "description"]:
            if attr in validated_data:
                setattr(instance, attr, validated_data[attr])

        if "image" in validated_data:
            instance.image = validated_data["image"]

        instance.save()

        details_payload = validated_data.get("details")
        if details_payload:
            for d in details_payload:
                detail_obj = None
                detail_id = d.get("id")
                offer_type = d.get("offer_type")

                if detail_id is not None:
                    try:
                        detail_obj = OfferDetail.objects.get(
                            id=detail_id, offer=instance)
                    except OfferDetail.DoesNotExist:
                        raise serializers.ValidationError(
                            {"details": f"Detail with id={detail_id} not found for this offer"})
                else:
                    qs = OfferDetail.objects.filter(
                        offer=instance, offer_type=offer_type)
                    count = qs.count()
                    if count == 0:
                        raise serializers.ValidationError(
                            {"details": f"No detail with offer_type='{offer_type}' for this offer"})
                    if count > 1:
                        raise serializers.ValidationError(
                            {"details": f"Multiple details with offer_type='{offer_type}' found; provide 'id' to disambiguate"})
                    detail_obj = qs.first()

                if "title" in d:
                    detail_obj.title = d["title"]
                if "revisions" in d:
                    detail_obj.revisions = d["revisions"]
                if "delivery_time_in_days" in d:
                    detail_obj.delivery_time = d["delivery_time_in_days"]
                if "price" in d:
                    detail_obj.price = d["price"]
                if "features" in d:
                    detail_obj.features = d["features"]

                detail_obj.save()
        return instance


class OfferDetailRetrieveSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving detailed information about a single offer detail.

    - Maps `delivery_time` from the model to `delivery_time_in_days` in the response.
    - Provides all key information such as title, price, revisions, and features.
    - Used for GET /api/offerdetails/{id}/ endpoint.
    """

    delivery_time_in_days = serializers.IntegerField(
        source="delivery_time", read_only=True)

    class Meta:
        model = OfferDetail
        fields = [
            "id",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
        ]
