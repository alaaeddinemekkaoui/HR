"""
JWT Authentication Views and API Endpoints
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from apps.employees.models import Employee


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer to include user information"""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser
        
        # Add groups/roles
        token['groups'] = list(user.groups.values_list('name', flat=True))
        
        # Add employee info if available
        try:
            employee = user.employee_profile
            token['employee_id'] = employee.employee_id
            token['employee_name'] = employee.full_name
            token['direction'] = employee.direction.name if employee.direction else None
        except (Employee.DoesNotExist, AttributeError):
            pass
        
        return token
    
    def validate(self, attrs):
        # Allow login with email or username
        username_or_email = attrs.get('username')
        password = attrs.get('password')
        
        # Try to find user by email first
        user = None
        if '@' in username_or_email:
            try:
                user = User.objects.get(email=username_or_email)
                username = user.username
            except User.DoesNotExist:
                pass
        else:
            username = username_or_email
        
        # Authenticate
        user = authenticate(username=username, password=password)
        
        if user is None:
            from rest_framework_simplejwt.exceptions import AuthenticationFailed
            raise AuthenticationFailed('No active account found with the given credentials')
        
        # Check if user is active
        if not user.is_active:
            from rest_framework_simplejwt.exceptions import AuthenticationFailed
            raise AuthenticationFailed('User account is disabled')
        
        # Generate tokens
        refresh = self.get_token(user)
        
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'groups': list(user.groups.values_list('name', flat=True)),
            }
        }
        
        # Add employee info
        try:
            employee = user.employee_profile
            data['user']['employee'] = {
                'id': employee.id,
                'employee_id': employee.employee_id,
                'full_name': employee.full_name,
                'email': employee.email,
                'direction': employee.direction.name if employee.direction else None,
                'division': employee.division.name if employee.division else None,
                'service': employee.service.name if employee.service else None,
                'position': employee.position.name if employee.position else None,
                'grade': employee.grade.name if employee.grade else None,
            }
        except (Employee.DoesNotExist, AttributeError):
            data['user']['employee'] = None
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token obtain view with enhanced user data"""
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]  # Allow unauthenticated access to get tokens


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user (admin only in production)
    For demo purposes - should be restricted
    """
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    
    if not username or not email or not password:
        return Response(
            {'error': 'Username, email, and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user exists
    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Username already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'Email already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )
    
    # Generate tokens
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'message': 'User created successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        },
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """
    Logout user by blacklisting their refresh token
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """
    Get current authenticated user information
    """
    user = request.user
    
    data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'groups': list(user.groups.values_list('name', flat=True)),
        'permissions': list(user.user_permissions.values_list('codename', flat=True)),
    }
    
    # Add employee info
    try:
        employee = user.employee_profile
        data['employee'] = {
            'id': employee.id,
            'employee_id': employee.employee_id,
            'full_name': employee.full_name,
            'email': employee.email,
            'phone': employee.phone,
            'direction': employee.direction.name if employee.direction else None,
            'division': employee.division.name if employee.division else None,
            'service': employee.service.name if employee.service else None,
            'departement': employee.departement.name if employee.departement else None,
            'position': employee.position.name if employee.position else None,
            'grade': employee.grade.name if employee.grade else None,
            'status': employee.status,
        }
    except (Employee.DoesNotExist, AttributeError):
        data['employee'] = None
    
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change user password
    """
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    
    if not old_password or not new_password:
        return Response(
            {'error': 'Both old and new passwords are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify old password
    if not user.check_password(old_password):
        return Response(
            {'error': 'Old password is incorrect'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
