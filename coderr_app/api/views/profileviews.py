from rest_framework import generics, status, permissions
from django.shortcuts import get_object_or_404
from coderr_app.models import Profile
from ..serializers import ProfileSerializer, BusinessProfileListSerializer, CustomerProfileListSerializer
from rest_framework.response import Response
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
