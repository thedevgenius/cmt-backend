# serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # Specify the fields the user is allowed to update
        fields = ['full_name', 'email'] 
        extra_kwargs = {
            'full_name': {'required': False},
            'email': {'required': False},
        }

    def validate_email(self, value):
        """Ensure the email is unique if it's being updated."""
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use by another account.")
        return value

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # List the exact fields you want to expose to the frontend
        # Assuming you are using 'phone' and 'full_name' based on previous code
        fields = ['id', 'phone', 'full_name', 'email', 'is_active', 'date_joined']
        
        # We set these as read-only just as a safety measure
        read_only_fields = ['id', 'phone', 'is_active', 'date_joined']

class RequestOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15, min_length=12)

class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15, min_length=10)
    otp = serializers.CharField(min_length=4, max_length=6)