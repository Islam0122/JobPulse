from rest_framework import serializers
from .models import (
    User,
    Stack,
    WorkFormat,
    EmploymentType
)


class StackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stack
        fields = ["id", "name"]

class WorkFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkFormat
        fields = ["id", "code", "title"]

class EmploymentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmploymentType
        fields = ["id", "code", "title"]

class UserReadSerializer(serializers.ModelSerializer):
    stack = StackSerializer(many=True, read_only=True)
    work_formats = WorkFormatSerializer(many=True, read_only=True)
    employment_types = EmploymentTypeSerializer(many=True, read_only=True)

    level_label = serializers.CharField(
        source="get_level_display",
        read_only=True
    )

    notify_mode_label = serializers.CharField(
        source="get_notify_mode_display",
        read_only=True
    )

    class Meta:
        model = User
        fields = [
            "telegram_id",
            "username",
            "role",
            "level",
            "level_label",
            "stack",
            "work_formats",
            "employment_types",
            "location",
            "salary_from",
            "currency",
            "notify_mode",
            "notify_mode_label",
            "is_active",
            "is_profile_completed",
            "created_at",
            "updated_at",
        ]

class UserWriteSerializer(serializers.ModelSerializer):
    stack_ids = serializers.PrimaryKeyRelatedField(
        queryset=Stack.objects.all(),
        many=True,
        write_only=True,
        required=False
    )

    work_format_ids = serializers.PrimaryKeyRelatedField(
        queryset=WorkFormat.objects.all(),
        many=True,
        write_only=True,
        required=False
    )

    employment_type_ids = serializers.PrimaryKeyRelatedField(
        queryset=EmploymentType.objects.all(),
        many=True,
        write_only=True,
        required=False
    )

    class Meta:
        model = User
        fields = [
            "telegram_id",
            "username",
            "role",
            "level",
            "stack_ids",
            "work_format_ids",
            "employment_type_ids",
            "location",
            "salary_from",
            "currency",
            "notify_mode",
        ]
    def create(self, validated_data):
        stack = validated_data.pop("stack_ids", [])
        work_formats = validated_data.pop("work_format_ids", [])
        employment_types = validated_data.pop("employment_type_ids", [])

        user = User.objects.create(**validated_data)

        user.stack.set(stack)
        user.work_formats.set(work_formats)
        user.employment_types.set(employment_types)

        return user
    def update(self, instance, validated_data):
        stack = validated_data.pop("stack_ids", None)
        work_formats = validated_data.pop("work_format_ids", None)
        employment_types = validated_data.pop("employment_type_ids", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if stack is not None:
            instance.stack.set(stack)

        if work_formats is not None:
            instance.work_formats.set(work_formats)

        if employment_types is not None:
            instance.employment_types.set(employment_types)

        instance.save()
        return instance


    def validate_stack_ids(self, value):
        if len(value) > 7:
            raise serializers.ValidationError(
                "Maximum 7 technologies allowed"
            )
        return value

    def validate_salary_from(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Salary must be positive")
        return value
