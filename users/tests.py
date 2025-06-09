from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class AuthenticationErrorHandlingTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.registration_url = reverse('users:register')
        self.login_url = reverse('users:login')
        self.profile_url = reverse('users:profile')
        self.change_password_url = reverse('users:change_password')

    def test_registration_validation_errors(self):
        """Test registration with invalid data"""
        invalid_data = {
            'username': 'test',
            'email': 'invalid-email',
            'password': 'short',
            'password2': 'different',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(self.registration_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json().get('success'))
        self.assertIn('errors', response.json())

    def test_login_with_invalid_credentials(self):
        """Test login with wrong credentials"""
        invalid_credentials = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        response = self.client.post(self.login_url, invalid_credentials)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.json().get('success'))
        self.assertIn('errors', response.json())

    def test_profile_without_authentication(self):
        """Test accessing profile without authentication"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.json().get('success'))
        self.assertIn('errors', response.json())

    def test_change_password_with_wrong_password(self):
        """Test changing password with wrong old password"""
        # First, authenticate the user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        invalid_data = {
            'old_password': 'wrongpass',
            'new_password': 'newpass123',
            'new_password2': 'newpass123'
        }
        response = self.client.put(self.change_password_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json().get('success'))
        self.assertIn('errors', response.json())
