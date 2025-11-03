from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Document, Pricing, Order


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'created_at']


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            'id', 'user', 'original_name', 'file_path', 'size',
            'file_type', 'status', 'uploaded_at', 'analysis_result',
            'proxy_document_id', 'external_metadata'
        ]
        read_only_fields = ['user', 'uploaded_at', 'analysis_result']


class PricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pricing
        fields = ['id', 'service_name', 'description', 'price_per_unit', 'unit_type', 'is_active']


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'user', 'document', 'pricing', 'total_price', 'status', 'created_at']
        read_only_fields = ['user', 'total_price', 'status', 'created_at']

    def validate_document(self, value):
        if value.user != self.context['request'].user:
            raise serializers.ValidationError("You can only use your own documents")
        return value