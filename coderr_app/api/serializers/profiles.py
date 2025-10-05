from rest_framework import serializers
from django.contrib.auth import get_user_model
from coderr_app.models import Profile


User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profiles combining user and profile data.

    - Includes user-related fields (username, email, first/last name) and profile-specific fields (location, tel, description, etc.).
    - Ensures image URLs are returned as absolute paths.
    - Replaces null/None values with empty strings for cleaner frontend handling.
    - Validates unique email addresses before saving.
    - Handles nested updates for both User and Profile models.
    """

    user = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", required=False)
    first_name = serializers.CharField(
        source="user.first_name", required=False, allow_blank=True)
    last_name = serializers.CharField(
        source="user.last_name",  required=False, allow_blank=True)
    type = serializers.CharField(source="user_type", read_only=True)
    file = serializers.ImageField(required=False, allow_null=True)
    location = serializers.CharField(required=False, allow_blank=True)
    tel = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    working_hours = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Profile
        fields = [
            "user", "username",
            "first_name", "last_name",
            "file",
            "location", "tel", "description", "working_hours",
            "type", "email", "created_at",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.file:
            req = self.context.get("request")
            url = instance.file.url
            data["file"] = req.build_absolute_uri(url) if req else url
        else:
            data["file"] = ""

        for k in ["first_name", "last_name", "location", "tel", "description", "working_hours"]:
            data[k] = data.get(k) or ""
        return data

    def validate(self, attrs):
        user_data = attrs.get("user", {})
        new_email = user_data.get("email")
        if new_email:
            qs = User.objects.filter(email=new_email)
            if self.instance:
                qs = qs.exclude(pk=self.instance.user_id)
            if qs.exists():
                raise serializers.ValidationError(
                    {"email": "This email is already in use."})
        return attrs

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        if "first_name" in user_data:
            instance.user.first_name = user_data["first_name"] or ""
        if "last_name" in user_data:
            instance.user.last_name = user_data["last_name"] or ""
        if "email" in user_data:
            instance.user.email = user_data["email"]
        instance.user.save()

        for attr in ["location", "tel", "description", "working_hours"]:
            if attr in validated_data:
                setattr(instance, attr, validated_data[attr] or "")

        if "file" in validated_data:
            instance.file = validated_data["file"]
        instance.save()
        return instance


class BusinessProfileListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing business user profiles.

    - Returns basic public information about business profiles.
    - Ensures non-null fields by replacing None with empty strings.
    - Includes user identification and profile contact details.
    - Provides the image filename if available.
    """

    user = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(
        source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name",  read_only=True)
    type = serializers.CharField(source="user_type", read_only=True)
    file = serializers.ImageField(read_only=True)

    class Meta:
        model = Profile
        fields = [
            "user", "username",
            "first_name", "last_name",
            "file",
            "location", "tel", "description", "working_hours",
            "type",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["file"] = instance.file.name if instance.file else ""
        for key in ["first_name", "last_name", "location", "tel", "description", "working_hours"]:
            if data.get(key) in (None,):
                data[key] = ""
        return data


class CustomerProfileListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing customer user profiles.

    - Provides public information about customer accounts.
    - Includes user identity fields, profile image, and upload timestamp.
    - Replaces None values with empty strings for consistent API responses.
    - Returns image filename if available.
    """

    user = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(
        source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name",  read_only=True)
    type = serializers.CharField(source="user_type", read_only=True)
    file = serializers.ImageField(read_only=True)
    uploaded_at = serializers.DateTimeField(
        source="created_at", read_only=True)

    class Meta:
        model = Profile
        fields = [
            "user", "username",
            "first_name", "last_name",
            "file",
            "uploaded_at",
            "type",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["file"] = instance.file.name if instance.file else ""
        for key in ["first_name", "last_name", "location", "tel", "description", "working_hours"]:
            if key in data and data.get(key) in (None,):
                data[key] = ""
        return data
