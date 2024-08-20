from rest_framework import serializers
from .models import CustomUser, Transaction, Notification, TopUpRequest, Canteen, FoodCategory, Food, Order, FeaturedFood
from django.utils import timezone
import pytz


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm password")

    class Meta:
        model = CustomUser
        fields = ['phone_number', 'email', 'first_name', 'last_name', 'password', 'password2', 'balance']

    def validate(self, data):
        # Check if passwords match
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords must match."})

        # Validate phone number or email (at least one must be provided)
        if not data.get('phone_number') and not data.get('email'):
            raise serializers.ValidationError({"non_field_errors": "Either phone number or email must be provided."})

        return data

    def create(self, validated_data):
        # Extract the password and remove it from validated data
        password = validated_data.pop('password')

        # Remove 'password2' from validated_data
        validated_data.pop('password2', None)

        # Create user with the remaining fields
        user = CustomUser.objects.create_user(**validated_data, password=password)
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(max_length=15, required=False)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        if not data.get('email') and not data.get('phone_number'):
            raise serializers.ValidationError("Either email or phone number must be provided.")
        if not data.get('password'):
            raise serializers.ValidationError("Password must be provided.")
        return data


class BalanceSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = CustomUser
        fields = ['balance']


class TransferSerializer(serializers.Serializer):
    recipient_phone_number = serializers.CharField(max_length=15)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class PasswordVerificationSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True)

class UserVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(max_length=15, required=False)
    password = serializers.CharField(write_only=True, required=True)  # Add password field

    def validate(self, data):
        if not data.get('email') and not data.get('phone_number'):
            raise serializers.ValidationError("Either email or phone number must be provided.")
        return data

class TransactionSerializer(serializers.ModelSerializer):
    sender = serializers.ReadOnlyField(source='sender.email')
    recipient = serializers.ReadOnlyField(source='recipient.email')
    date = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ['sender', 'recipient', 'amount', 'date']

    def get_date(self, obj):
        # Convert to Asia/Manila timezone
        local_tz = pytz.timezone('Asia/Manila')
        utc_date = obj.date
        local_date = utc_date.astimezone(local_tz)
        # Format date as 'YYYY-MM-DD h:mm AM/PM'
        return local_date.strftime('%Y-%m-%d %I:%M %p')

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'created_at']


class TopUpRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = TopUpRequest
        fields = ['user_first_name', 'amount', 'is_approved', 'created_at']
        read_only_fields = ['user_first_name', 'user', 'is_approved', 'created_at']

    def create(self, validated_data):
        # Only `amount` will be validated and used to create a new instance
        top_up_request = TopUpRequest.objects.create(**validated_data)
        return top_up_request


class UserDetailsSerializer(serializers.ModelSerializer):
    bmi = serializers.ReadOnlyField()

    class Meta:
        model = CustomUser
        fields = ['phone_number', 'email', 'first_name', 'last_name', 'balance', 'height', 'weight', 'bmi', 'is_active', 'is_staff', 'is_superuser', 'date_joined']


class UpdateHeightWeightSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['height', 'weight']

# Food System
class CanteenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Canteen
        fields = ['id', 'name', 'description']

class FoodCategorySerializer(serializers.ModelSerializer):
    canteen = CanteenSerializer()

    class Meta:
        model = FoodCategory
        fields = ['id', 'name', 'canteen']

class FoodSerializer(serializers.ModelSerializer):
    category = FoodCategorySerializer()
    canteen = serializers.SerializerMethodField()
    vendor = serializers.StringRelatedField()  # Assuming you want to show vendor's username
    vendor_phone_number = serializers.CharField(source='vendor.phone_number', read_only=True)

    class Meta:
        model = Food
        fields = ['id', 'name', 'description', 'price', 'category', 'canteen', 'vendor', 'vendor_phone_number']

    def get_canteen(self, obj):
        return CanteenSerializer(obj.category.canteen).data

class FeaturedFoodSerializer(serializers.ModelSerializer):
    food = FoodSerializer()

    class Meta:
        model = FeaturedFood
        fields = ['food']


class OrderSerializer(serializers.ModelSerializer):
    food = serializers.PrimaryKeyRelatedField(queryset=Food.objects.all())
    user = serializers.StringRelatedField()  # Or you can use a nested user serializer
    user_phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    vendor = serializers.StringRelatedField(allow_null=True)
    vendor_phone_number = serializers.CharField(source='vendor.phone_number', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'user_phone_number', 'food', 'quantity', 'total_price', 'created_at', 'vendor', 'vendor_phone_number', 'is_paid']
        read_only_fields = ['user', 'total_price', 'created_at', 'vendor']

    def validate(self, data):
        user = self.context['request'].user
        existing_order = Order.objects.filter(user=user, is_paid=False).first()
        if existing_order:
            raise serializers.ValidationError(
                "You have an existing unpaid order. Please pay for it before placing a new order.")
        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['food'] = FoodSerializer(instance.food).data
        return representation
