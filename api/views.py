from rest_framework import viewsets, generics, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.db.models import Q, Count, Avg
from django.http import HttpResponse
import pandas as pd
import json

from .models import CustomUser, Report, ReportData
# from .models import COUNTY_CHOICES, SUBLOCATION_CHOICES

from .serializers import (
    LoginSerializer, ReportSerializer, ReportDataSerializer, 
    UserSerializer, UserCreateSerializer
)
from .permissions import IsAgent, IsSupervisor, IsManager


from django.views.decorators.csrf import ensure_csrf_cookie

########sar###############

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def login_page(request):
    """
    Handle both GET (show login page) and POST (process login)
    """
    if request.method == 'GET':
        print("GET request to login page")
        return render(request, 'login.html')
    
    elif request.method == 'POST':
        print("POST request to login")
        print("Request data:", request.data)
        
        serializer = LoginSerializer(data=request.data)
        print("Serializer created")
        
        if serializer.is_valid():
            print("Serializer is valid")
            user = serializer.validated_data['user']
            print(f"User: {user.username}, Role: {user.role}")
            login(request, user)
            
            # Return redirect URL based on user role
            if user.role == 'agent':
                return Response({'redirect': 'api/dashboard/agent/'})
            elif user.role == 'supervisor':
                return Response({'redirect': 'api/dashboard/supervisor/'})
            elif user.role == 'manager':
                return Response({'redirect': 'api/dashboard/manager/'})
            else:
                return Response({'error': 'Unknown user role'}, status=400)
        else:
            print("Serializer errors:", serializer.errors)
        
        # If login fails
        return Response(serializer.errors, status=400)

@api_view(['POST'])
def custom_logout(request):
    logout(request)
    return Response({'message': 'Logged out successfully'})        
########### end ###########

# Dashboard views
def agent_dashboard(request):
    return render(request, 'agent_dashboard.html')

def supervisor_dashboard(request):
    return render(request, 'supervisor_dashboard.html')

def manager_dashboard(request):
    return render(request, "manager_dashboard.html", {
        "county_choices": CustomUser.COUNTY_CHOICES,
        "sublocation_choices": CustomUser.SUBLOCATION_CHOICES,
    })

from .models import CustomUser

@api_view(['GET'])
def get_counties(request):
    return Response([{"value": v, "label": l} for v, l in CustomUser.COUNTY_CHOICES])

@api_view(['GET'])
def get_sublocations(request):
    return Response([{"value": v, "label": l} for v, l in CustomUser.SUBLOCATION_CHOICES])

# API Viewsets
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsManager]
    
    def get_queryset(self):
        return CustomUser.objects.filter(is_active=True)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'])
    def agents(self, request):
        agents = CustomUser.objects.filter(role='agent', is_active=True)
        serializer = self.get_serializer(agents, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def supervisors(self, request):
        supervisors = CustomUser.objects.filter(role='supervisor', is_active=True)
        serializer = self.get_serializer(supervisors, many=True)
        return Response(serializer.data)

class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'agent':
            return Report.objects.filter(assigned_to=user)
        elif user.role == 'supervisor':
            return Report.objects.filter(county=user.county)
        elif user.role == 'manager':
            return Report.objects.all()
        return Report.objects.none()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class ReportDataViewSet(viewsets.ModelViewSet):
    serializer_class = ReportDataSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        report_id = self.request.query_params.get('report_id')
        queryset = ReportData.objects.all()
        
        if report_id:
            queryset = queryset.filter(report_id=report_id)
            
        if user.role == 'agent':
            return queryset.filter(report__assigned_to=user)
        elif user.role == 'supervisor':
            return queryset.filter(report__county=user.county)
        elif user.role == 'manager':
            return queryset
        return ReportData.objects.none()
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create report data entries"""
        data_list = request.data.get('entries', [])
        report_id = request.data.get('report_id')
        
        try:
            report = Report.objects.get(id=report_id)
            created_entries = []
            
            for data in data_list:
                serializer = self.get_serializer(data=data)
                if serializer.is_valid():
                    serializer.save(report=report)
                    created_entries.append(serializer.data)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(created_entries, status=status.HTTP_201_CREATED)
            
        except Report.DoesNotExist:
            return Response(
                {'error': 'Report not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def export_excel(self, request):
        """Export report data to Excel"""
        report_id = request.query_params.get('report_id')
        queryset = self.get_queryset()
        
        if report_id:
            queryset = queryset.filter(report_id=report_id)
        
        # Convert to DataFrame
        data = list(queryset.values(
            'entry_number', 'customer_name', 'customer_phone', 'location',
            'service_type', 'priority', 'status', 'agent_feedback',
            'supervisor_feedback', 'created_at'
        ))
        
        df = pd.DataFrame(data)
        
        # Create HTTP response with Excel file
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="report_data.xlsx"'
        
        df.to_excel(response, index=False, engine='openpyxl')
        return response

# Statistics and analytics
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsManager])
def manager_statistics(request):
    """Get statistics for manager dashboard"""
    
    # User statistics
    total_agents = CustomUser.objects.filter(role='agent', is_active=True).count()
    total_supervisors = CustomUser.objects.filter(role='supervisor', is_active=True).count()
    
    # Report statistics
    total_reports = Report.objects.count()
    completed_reports = Report.objects.filter(status='completed').count()
    pending_reports = Report.objects.filter(status='pending').count()
    
    # County-wise distribution
    county_stats = Report.objects.values('county').annotate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        active_rate=Avg('active_rate')
    )
    
    # Recent activities
    recent_reports = Report.objects.order_by('-created_at')[:5]
    recent_users = CustomUser.objects.filter(
        role__in=['agent', 'supervisor']
    ).order_by('-date_joined')[:5]
    
    return Response({
        'user_stats': {
            'total_agents': total_agents,
            'total_supervisors': total_supervisors,
        },
        'report_stats': {
            'total_reports': total_reports,
            'completed_reports': completed_reports,
            'pending_reports': pending_reports,
            'completion_rate': (completed_reports / total_reports * 100) if total_reports > 0 else 0,
        },
        'county_stats': list(county_stats),
        'recent_reports': ReportSerializer(recent_reports, many=True).data,
        'recent_users': UserSerializer(recent_users, many=True).data,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def debug_urls(request):
    """Debug view to show all available URLs"""
    from django.urls import get_resolver
    from django.http import JsonResponse
    
    def extract_urls(patterns, prefix=''):
        urls = []
        for pattern in patterns:
            if hasattr(pattern, 'url_patterns'):
                # This is an include pattern
                urls.extend(extract_urls(pattern.url_patterns, prefix + str(pattern.pattern)))
            else:
                # This is a regular pattern
                url_info = {
                    'pattern': prefix + str(pattern.pattern),
                    'name': getattr(pattern, 'name', 'No name'),
                }
                urls.append(url_info)
        return urls
    
    all_urls = extract_urls(get_resolver().url_patterns)
    return JsonResponse(all_urls, safe=False)