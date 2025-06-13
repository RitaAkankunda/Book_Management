from django.shortcuts import render
from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django_filters.rest_framework import DjangoFilterBackend
from .permissions import IsAdmin, IsModerator
from .serializers import (
    UserSerializer, 
    UserUpdateSerializer, 
    ChangePasswordSerializer,
    ResetPasswordEmailSerializer, 
    ResetPasswordConfirmSerializer,
    LoginSerializer
)

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """
    Register a new user
    POST /api/users/register/
    
    Note: By default, new users are registered with 'USER' role.
    Only admins can create users with 'ADMIN' or 'MODERATOR' roles.
    """
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        # If user is not admin, force role to be 'USER'
        if not (self.request.user and self.request.user.is_authenticated and self.request.user.role == 'ADMIN'):
            serializer.validated_data['role'] = 'USER'
        serializer.save()


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update user profile
    GET /api/users/profile/ - Get own profile
    GET /api/users/profile/{id}/ - Get other user's profile (admin only)
    PUT /api/users/profile/ - Update own profile
    PATCH /api/users/profile/ - Partially update own profile
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer

    def get_object(self):
        # If user_id is provided in URL and user is admin, get that user
        user_id = self.kwargs.get('user_id')
        if user_id and self.request.user.role == 'ADMIN':
            return User.objects.get(id=user_id)
        # Otherwise, get own profile
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class ChangePasswordView(generics.UpdateAPIView):
    """
    Change user password
    PUT /api/users/change-password/
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check old password
        user = self.get_object()
        if not user.check_password(serializer.data.get("old_password")):
            return Response(
                {"old_password": ["Wrong password."]}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password
        user.set_password(serializer.data.get("new_password"))
        user.save()
        return Response({"message": "Password updated successfully"})


class LogoutView(APIView):
    """
    Logout user by blacklisting their refresh token
    POST /api/users/logout/
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Successfully logged out."})
        except Exception:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(generics.GenericAPIView):
    """
    Request password reset email
    POST /api/users/password-reset/
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = ResetPasswordEmailSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Generate password reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Create password reset link
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
          # Send email
        send_mail(
            subject="Password Reset Request",
            message=f"Click the following link to reset your password: {reset_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        response_data = {
            "message": "Password reset email has been sent."
        }
        
        # In development, include the token and UID for testing
        if settings.DEBUG:
            response_data.update({
                "debug_info": {
                    "uid": uid,
                    "token": token,
                }
            })
        
        return Response(response_data, status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    Confirm password reset with token
    POST /api/users/password-reset-confirm/{uidb64}/{token}/
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = ResetPasswordConfirmSerializer
    
    def post(self, request, uidb64, token):
        try:
            # Decode the user ID
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            
            # Validate token from URL
            if not default_token_generator.check_token(user, token):
                return Response(
                    {"error": "Invalid or expired reset link."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Validate password in request body
            serializer = ResetPasswordConfirmSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Set new password
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response(
                {"message": "Password has been reset successfully."},
                status=status.HTTP_200_OK
            )
            
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"error": "Invalid reset link"},
                status=status.HTTP_400_BAD_REQUEST
            )


class LoginView(TokenObtainPairView):
    """
    Login user and return JWT token
    POST /api/users/login/
    """
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        token = serializer.validated_data
        
        return Response({
            'access': token['access'],
            'refresh': token['refresh'],
            'user': UserSerializer(user).data
        })


class UserListView(generics.ListAPIView):
    """
    List all users (admin only)
    GET /api/users/
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'date_joined']
    ordering = ['-date_joined']  # Default ordering
