from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from django.db import transaction, IntegrityError
from coderr_app.models import Profile

User = get_user_model()


class RegistrationSerializer(serializers.Serializer):
    """
    Handles user registration and profile creation. 

    This Serializer validates registration data, ensures unique usernames and emails, and 
    creates both a new User and associated Profile instance within an atomic transaction.

    Validation: 
        -Ensures both password fields match. 
        -Checks for existing usernames or emails.

    Methods: 
        -create(validated_data):
            Creates a new user and related profile in one atomic operation.
    """

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    repeated_password = serializers.CharField(write_only=True, min_length=8)
    type = serializers.ChoiceField(
        choices=[('customer', 'Customer'), ('business', 'Business')])

    def validate(self, attrs):
        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError(
                "repeated_password: Passwords do not match.")
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError(
                "username: Username is already taken.")
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError(
                "email: Email is already registered.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user_type = validated_data.pop('type')
        validated_data.pop('repeated_password')

        user = User.objects.create_user(username=validated_data['username'],
                                        email=validated_data['email'],
                                        password=validated_data['password'],)
        Profile.objects.create(user=user, user_type=user_type)
        return user


class LoginSerializer(serializers.Serializer):
    """
    Authenticates a user using username and password credentials.

    Validation:
        -Verifies that the provided credentials are valid.
        -Attaches the authenticated user to the validated data.
    """

    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        user = authenticate(
            username=attrs['username'], password=attrs['password'])
        if user is None:
            raise serializers.ValidationError("Invalid username or password.")
        attrs['user'] = user
        return attrs
