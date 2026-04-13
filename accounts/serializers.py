from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, Role


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'password', 'confirm_password']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        # Auto-assign Customer role
        customer_role, _ = Role.objects.get_or_create(name=Role.CUSTOMER)
        user = CustomUser.objects.create_user(
            **validated_data,
            role=customer_role
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("Account is disabled.")
        data['user'] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    role = serializers.StringRelatedField()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'is_editable', 'created_at']
        read_only_fields = ['id', 'email', 'role', 'created_at']
        
        
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name']

    def validate(self, data):
        user = self.context['request'].user
        if not user.is_editable:
            raise serializers.ValidationError(
                "You are not allowed to edit profile. Contact admin."
            )
        return data


class ToggleEditableSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['is_editable']