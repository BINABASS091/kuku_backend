from rest_framework import serializers
from accounts.models import User, Farmer

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']

class FarmerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Farmer
        fields = ['id', 'user', 'full_name', 'address', 'email', 'phone', 'created_date']
        read_only_fields = ['id', 'created_date']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8,
        error_messages={
            'min_length': 'Password must be at least 8 characters long.',
            'blank': 'Password cannot be blank.',
        }
    )
    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'Email is required.',
            'invalid': 'Enter a valid email address.',
            'blank': 'Email cannot be blank.',
        }
    )
    first_name = serializers.CharField(
        required=True,
        error_messages={
            'required': 'First name is required.',
            'blank': 'First name cannot be blank.',
        }
    )
    last_name = serializers.CharField(
        required=True,
        error_messages={
            'required': 'Last name is required.',
            'blank': 'Last name cannot be blank.',
        }
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'role']
        extra_kwargs = {
            'username': {
                'error_messages': {
                    'required': 'Username is required.',
                    'blank': 'Username cannot be blank.',
                    'invalid': 'Enter a valid username.',
                }
            },
            'role': {
                'error_messages': {
                    'invalid_choice': 'Invalid role. Must be one of: ADMIN, FARMER, ACCOUNTANT, EXPERT.',
                }
            },
        }
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('A user with that username already exists.')
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with that email already exists.')
        return value.lower()
    
    def validate(self, data):
        """
        Object-level validation.
        """
        # Log the incoming data for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f'User registration data: {data}')
        
        # Ensure role is valid
        if 'role' in data and data['role'] not in dict(User.role_choices).keys():
            logger.error(f'Invalid role: {data["role"]}. Must be one of: {list(User.role_choices.keys())}')
            raise serializers.ValidationError({
                'role': f'Invalid role. Must be one of: {", ".join(User.role_choices.keys())}'
            })
            
        return data
    
    def create(self, validated_data):
        try:
            # Log the validated data
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'Creating user with validated data: {validated_data}')
            
            # Create the user
            user = User.objects.create_user(**validated_data)
            logger.info(f'Successfully created user: {user.username} (ID: {user.id})')
            
            return user
        except Exception as e:
            # Log the full error for debugging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f'Error creating user: {str(e)}')
            logger.error(f'Traceback: {traceback.format_exc()}')
            
            # Check for common validation errors
            if 'username' in str(e) and 'already exists' in str(e):
                raise serializers.ValidationError({'email': 'A user with this email already exists.'})
            elif 'email' in str(e) and 'already exists' in str(e):
                raise serializers.ValidationError({'email': 'A user with this email already exists.'})
                
            raise serializers.ValidationError('Error creating user. Please try again.')
