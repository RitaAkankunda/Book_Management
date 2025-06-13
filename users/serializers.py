from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User  # Import User directly from models

class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True,
        required=False,  # Not required for GET requests
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=False)  # Not required for GET requests
    role = serializers.ChoiceField(
        choices=[('ADMIN', 'Admin'), ('MODERATOR', 'Moderator'), ('USER', 'User')],
        default='USER'
    )
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password2', 'email', 'first_name', 
                 'last_name', 'full_name', 'role', 'date_joined', 'last_login')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'password': {'write_only': True},
            'password2': {'write_only': True},
        }
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    def to_representation(self, instance):
        """Customize the output based on the request method"""
        ret = super().to_representation(instance)
        if self.context.get('request') and self.context['request'].method == 'GET':
            # Remove password fields from GET requests
            ret.pop('password', None)
            ret.pop('password2', None)
        return ret

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        # Remove password2 from the data
        validated_data.pop('password2')
        
        # Create user with remaining data
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role=validated_data['role']
        )
        
        # Set the password
        user.set_password(validated_data['password'])
        user.save()
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 
                 'bio', 'date_of_birth', 'profile_picture')
        read_only_fields = ('id', 'username', 'role')  # These fields cannot be changed via profile update


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs


class ResetPasswordEmailSerializer(serializers.Serializer):
    """Serializer for requesting a password reset email"""
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        # Check if user exists with this email
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value


class ResetPasswordConfirmSerializer(serializers.Serializer):
    """Serializer for confirming a password reset"""
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs

class LoginSerializer(TokenObtainPairSerializer):
    """Custom login serializer that adds user information to the token response"""
    def validate(self, attrs):
        data = super().validate(attrs)
        # Add custom claims
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name
        }
        return data
