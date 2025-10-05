from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from .serializers import RegistrationSerializer, LoginSerializer


class RegistrationView(APIView):
    """
    Handles user registration and token creation.

    Methods:
        -Validates incoming registration data.
        -Creates a new user and associated profile.
        -Generates an authentication token for the user.
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
        except Exception:
            return Response({"detail": " Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'token': token.key,
            'username': user.username,
            'email': user.email,
            'user_id': user.id
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    Handles user authentication and token retrieval. 

    Methods:
        -post(request):
            -Validates provided credentials(username and password).
            -Autheticates the user and returns an existing or new auth token.
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.validated_data['user']
            token, _ = Token.objects.get_or_create(user=user)
        except Exception:
            return Response({"detail": " Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({
            'token': token.key,
            'username': user.username,
            'email': user.email,
            'user_id': user.id
        }, status=status.HTTP_200_OK)
