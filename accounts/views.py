from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken      
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken  
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os

from .models import CustomUser, Role
from .serializers import (
    RegisterSerializer, LoginSerializer, UserProfileSerializer,
    ChangePasswordSerializer, UpdateProfileSerializer, ToggleEditableSerializer
)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)
            return Response({
                'message': 'Account created successfully.',
                'user': UserProfileSerializer(user).data,
                'tokens': tokens
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = get_tokens_for_user(user)
            return Response({
                'message': 'Login successful.',
                'user': UserProfileSerializer(user).data,
                'tokens': tokens
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Blacklist refresh token
            refresh_token = request.data.get('refresh')
            if refresh_token:
                refresh = RefreshToken(refresh_token)
                refresh.blacklist()

            # Blacklist access token too
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                access_token = auth_header.split(' ')[1]
                token = AccessToken(access_token)
                # Add to outstanding tokens then blacklist
                outstanding_token, _ = OutstandingToken.objects.get_or_create(
                    jti=token['jti'],
                    defaults={
                        'user': request.user,
                        'token': access_token,
                        'expires_at': token.current_time + token.lifetime,
                    }
                )
                BlacklistedToken.objects.get_or_create(token=outstanding_token)

            return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        try:
            # Verify the Google token
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                os.getenv('GOOGLE_CLIENT_ID')
            )
            email = idinfo['email']
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            google_id = idinfo['sub']

            # Get or create user
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'google_id': google_id,
                }
            )
            if created:
                customer_role, _ = Role.objects.get_or_create(name=Role.CUSTOMER)
                user.role = customer_role
                user.set_unusable_password()
                user.save()

            tokens = get_tokens_for_user(user)
            return Response({
                'message': 'Google login successful.',
                'user': UserProfileSerializer(user).data,
                'tokens': tokens,
                'created': created
            }, status=status.HTTP_200_OK)

        except ValueError:
            return Response({'error': 'Invalid Google token.'}, status=status.HTTP_400_BAD_REQUEST)


class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role and request.user.role.name != Role.ADMIN:
            return Response({'error': 'Admin access only.'}, status=status.HTTP_403_FORBIDDEN)
        users = CustomUser.objects.filter(role__name=Role.CUSTOMER)
        return Response({
            'total_customers': users.count(),
            'customers': UserProfileSerializer(users, many=True).data
        })


class CustomerDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role and request.user.role.name != Role.CUSTOMER:
            return Response({'error': 'Customer access only.'}, status=status.HTTP_403_FORBIDDEN)
        return Response({
            'message': f'Welcome, {request.user.full_name}!',
            'profile': UserProfileSerializer(request.user).data
        })
        
        

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'error': 'Old password is incorrect.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password changed successfully.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        print(f"User {user.email} is_editable: {user.is_editable}")  # Debugging line
        if not user.is_editable:
            return Response(
                {'error': 'Profile editing is disabled. Contact admin to enable it.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = UpdateProfileSerializer(
            user, data=request.data, partial=True, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully.',
                'user': UserProfileSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ToggleEditableView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, user_id):
        # Only admins can toggle this
        if request.user.role.name != Role.ADMIN:
            return Response(
                {'error': 'Admin access only.'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            customer = CustomUser.objects.get(id=user_id, role__name=Role.CUSTOMER)
            customer.is_editable = not customer.is_editable
            customer.save()
            return Response({
                'message': f'is_editable set to {customer.is_editable} for {customer.email}',
                'is_editable': customer.is_editable
            })
        except CustomUser.DoesNotExist:
            return Response({'error': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        
class DeleteCustomerView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id):
        if request.user.role.name != Role.ADMIN:
            return Response(
                {'error': 'Admin access only.'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            customer = CustomUser.objects.get(id=user_id, role__name=Role.CUSTOMER)
            customer.delete()
            return Response({'message': 'Customer deleted successfully.'}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Customer not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        
class DeleteOwnAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        if user.role.name != Role.CUSTOMER:
            return Response(
                {'error': 'Only customers can delete their own account.'},
                status=status.HTTP_403_FORBIDDEN
            )
        user.delete()
        return Response({'message': 'Account deleted successfully.'}, status=status.HTTP_200_OK)