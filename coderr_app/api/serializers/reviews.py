from rest_framework import serializers
from django.contrib.auth import get_user_model
from coderr_app.models import Review

User = get_user_model()


class ReviewListSerializer(serializers.ModelSerializer):
    """
    Serializer to present the needed informations about Reviews
    """
    class Meta:
        model = Review
        fields = [
            "id",
            "business_user",
            "reviewer",
            "rating",
            "description",
            "created_at",
            "updated_at",

        ]


class ReviewCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new business user reviews.

    - Ensures the target user has a 'business' profile type.
    - Prevents users from reviewing themselves.
    - Enforces one review per reviewer-business pair.
    - Automatically assigns the authenticated user as the reviewer.
    - Used for POST /api/reviews/ endpoint.
    """

    class Meta:
        model = Review
        fields = ["business_user", "rating", "description"]

    def validate_business_user(self, value):

        if not hasattr(value, "profile") or getattr(value.profile, "user_type", None) != "business":
            raise serializers.ValidationError(
                "Target user is not a business profile.")
        return value

    def validate(self, attrs):
        reviewer = self.context["request"].user
        business_user = attrs.get("business_user")

        if business_user and reviewer and business_user.id == reviewer.id:
            raise serializers.ValidationError(
                {"business_user": "You cannot review yourself."})

        if business_user and Review.objects.filter(business_user=business_user, reviewer=reviewer).exists():
            raise serializers.ValidationError(
                "You have already reviewed this business user.")
        return attrs

    def create(self, validated_data):
        reviewer = validated_data.pop("reviewer", None)

        return Review.objects.create(reviewer=reviewer, **validated_data)


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing reviews.

    - Allows editing of `rating` and `description` fields only.
    - Rejects requests containing any other fields.
    - Ensures at least one editable field is provided.
    - Used for PATCH /api/reviews/{id}/ endpoint.
    """

    class Meta:
        model = Review
        fields = ["rating", "description"]

    def validate(self, attrs):

        allowed = {"rating", "description"}
        extra = set(self.initial_data.keys()) - allowed
        if extra:
            raise serializers.ValidationError(
                "Only 'rating' and 'description' may be updated.")
        if not any(k in attrs for k in allowed):
            raise serializers.ValidationError(
                "Provide at least one of: 'rating' or 'description'.")
        return attrs

    def update(self, instance, validated_data):
        validated_data.pop("reviewer", None)
        return super().update(instance, validated_data)
