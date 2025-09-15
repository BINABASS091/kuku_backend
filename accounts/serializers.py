from rest_framework import serializers
from accounts.models import User, Farmer

class UserSerializer(serializers.ModelSerializer):
    # Allow admin to optionally set a new password on update
    password = serializers.CharField(write_only=True, required=False, allow_blank=False, min_length=8)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'role',
            'is_active', 'is_staff', 'is_superuser', 'date_joined', 'password'
        ]
        read_only_fields = ['id', 'date_joined']

    def create(self, validated_data):
        # Extract password if present
        password = validated_data.pop('password', None)
        if not password:
            raise serializers.ValidationError({'password': 'Password is required for new users.'})
        
        # Create user instance
        user = User.objects.create(**validated_data)
        # Set password properly (this hashes it)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        # Extract password if present
        password = validated_data.pop('password', None)
        # Standard update for other fields
        user = super().update(instance, validated_data)
        # Apply password change securely
        if password:
            user.set_password(password)
            user.save(update_fields=['password'])
        return user

class FarmerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    phone_number = serializers.CharField(source='phone', read_only=True)
    city = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    zip_code = serializers.SerializerMethodField()
    date_of_birth = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    experience_years = serializers.SerializerMethodField()
    farm_size = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()
    subscription_status = serializers.SerializerMethodField()
    total_farms = serializers.SerializerMethodField()
    total_batches = serializers.SerializerMethodField()
    
    class Meta:
        model = Farmer
        fields = [
            'farmerID', 'user', 'farmerName', 'address', 'email', 'phone', 'phone_number',
            'city', 'state', 'country', 'zip_code', 'date_of_birth', 'gender',
            'experience_years', 'farm_size', 'is_verified', 'subscription_status',
            'total_farms', 'total_batches', 'created_date'
        ]
        read_only_fields = ['farmerID', 'created_date']
    
    def get_city(self, obj):
        # Extract city from address or return None
        return None

    def get_state(self, obj):
        # Extract state from address or return None
        return None

    def get_country(self, obj):
        # Return default country
        return "Tanzania"
    
    def get_zip_code(self, obj):
        # Return None if zip code is not available
        return None
    
    def get_date_of_birth(self, obj):
        # Return default date of birth
        return "1990-01-01"
    
    def get_gender(self, obj):
        # Return default gender
        return "M"
    
    def get_experience_years(self, obj):
        # Calculate experience based on created date or return default
        from datetime import date
        if obj.created_date:
            years = (date.today() - obj.created_date).days // 365
            return max(years, 1)
        return 1
    
    def get_farm_size(self, obj):
        """Get total farm size for this farmer"""
        try:
            # Since farmSize is a CharField, we need to handle it differently
            farms = obj.farms.all()
            if not farms:
                return "0"
            
            # Try to extract numeric values from size strings
            total_numeric = 0
            size_parts = []
            
            for farm in farms:
                if hasattr(farm, 'farmSize') and farm.farmSize:
                    size_str = str(farm.farmSize).strip()
                    # Try to extract numbers from the size string
                    import re
                    numbers = re.findall(r'\d+\.?\d*', size_str)
                    if numbers:
                        total_numeric += float(numbers[0])
                    size_parts.append(size_str)
            
            # Return both numeric total and concatenated sizes
            if total_numeric > 0:
                return f"{total_numeric} (from: {', '.join(size_parts)})"
            else:
                return ', '.join(size_parts) if size_parts else "Unknown"
                
        except Exception as e:
            return "Error calculating size"
    
    def get_is_verified(self, obj):
        # Return verification status (default to True for existing farmers)
        return True
    
    def get_subscription_status(self, obj):
        # Get current subscription status
        try:
            if hasattr(obj, 'subscriptions') and obj.subscriptions.exists():
                latest_subscription = obj.subscriptions.filter(status='ACTIVE').first()
                if latest_subscription and hasattr(latest_subscription, 'subscription_typeID'):
                    return latest_subscription.subscription_typeID.name if latest_subscription.subscription_typeID else "Basic"
            return "Basic"
        except Exception as e:
            return "Basic"
    
    def get_total_farms(self, obj):
        # Count total farms for this farmer
        try:
            if hasattr(obj, 'farms'):
                return obj.farms.count()
            return 0
        except:
            return 0
    
    def get_total_batches(self, obj):
        # Count total batches across all farms for this farmer
        try:
            total = 0
            if hasattr(obj, 'farms'):
                for farm in obj.farms.all():
                    if hasattr(farm, 'batches'):
                        total += farm.batches.count()
            return total
        except:
            return 0

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
