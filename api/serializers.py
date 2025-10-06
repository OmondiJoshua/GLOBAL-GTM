from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, Report, ReportData

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    data['user'] = user
                else:
                    raise serializers.ValidationError('User account is disabled.')
            else:
                raise serializers.ValidationError('Unable to log in with provided credentials.')
        else:
            raise serializers.ValidationError('Must include "username" and "password".')

        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'role', 'county', 'sublocation', 'phone_number', 
            'employee_id', 'is_active', 'date_joined'
        ]
        read_only_fields = ['employee_id', 'date_joined']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'role', 'county', 'sublocation', 'phone_number', 
            'password', 'employee_id'
        ]
        read_only_fields = ['employee_id']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }

    def create(self, validated_data):
        # Remove password from validated_data if present
        password = validated_data.pop('password', None)
        
        # Create user instance
        user = CustomUser.objects.create_user(**validated_data)
        
        # If password is provided, set it, otherwise it will be set to employee_id in the model's save method
        if password:
            user.set_password(password)
            user.save()
        
        return user

class ReportDataSerializer(serializers.ModelSerializer):
    report_title = serializers.CharField(source='report.title', read_only=True)
    county = serializers.CharField(source='report.county', read_only=True)
    sublocation = serializers.CharField(source='report.sublocation', read_only=True)
    
    class Meta:
        model = ReportData
        fields = [
            'id', 'report', 'report_title', 'entry_number', 'customer_name', 
            'customer_phone', 'location', 'service_type', 'priority', 
            'status', 'is_active', 'agent_feedback', 'supervisor_feedback',
            'county', 'sublocation', 'created_at', 'updated_at'
        ]
        read_only_fields = ['entry_number', 'is_active', 'created_at', 'updated_at']

class ReportSerializer(serializers.ModelSerializer):
    data_rows = ReportDataSerializer(many=True, read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'title', 'description', 'status', 'county', 'sublocation',
            'assigned_to', 'assigned_to_name', 'created_by', 'created_by_name',
            'total_entries', 'active_rate', 'completion_rate', 'manager_feedback',
            'created_at', 'updated_at', 'data_rows'
        ]
        read_only_fields = [
            'created_by', 'created_by_name', 'total_entries', 
            'active_rate', 'completion_rate', 'created_at', 'updated_at'
        ]

class ReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            'id', 'title', 'description', 'status', 'county', 'sublocation',
            'assigned_to', 'manager_feedback'
        ]

# Statistics serializers
class CountyStatsSerializer(serializers.Serializer):
    county = serializers.CharField()
    total = serializers.IntegerField()
    completed = serializers.IntegerField()
    active_rate = serializers.FloatField()

class UserStatsSerializer(serializers.Serializer):
    total_agents = serializers.IntegerField()
    total_supervisors = serializers.IntegerField()

class ReportStatsSerializer(serializers.Serializer):
    total_reports = serializers.IntegerField()
    completed_reports = serializers.IntegerField()
    pending_reports = serializers.IntegerField()
    completion_rate = serializers.FloatField()

class ManagerStatisticsSerializer(serializers.Serializer):
    user_stats = UserStatsSerializer()
    report_stats = ReportStatsSerializer()
    county_stats = CountyStatsSerializer(many=True)
    recent_reports = ReportSerializer(many=True)
    recent_users = UserSerializer(many=True)