"""Dashboard API views for statistics and admin overview."""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Sum
from accounts.models import User, Farmer
from farms.models import Farm, Device
from batches.models import Batch
from subscriptions.models import FarmerSubscription, Payment
from datetime import datetime, timedelta
from decimal import Decimal


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics for admin overview."""
    
    # Calculate current month for revenue calculation
    current_month = datetime.now().replace(day=1)
    
    # Basic counts
    total_users = User.objects.count()
    total_farmers = Farmer.objects.count()
    active_farms = Farm.objects.count()
    total_devices = Device.objects.count()
    
    # Active subscriptions (assuming status field exists)
    active_subscriptions = FarmerSubscription.objects.filter(
        end_date__gte=datetime.now().date()
    ).count()
    
    # Monthly revenue calculation
    monthly_payments = Payment.objects.filter(
        payment_date__gte=current_month
    ).aggregate(total=Sum('amount'))
    
    monthly_revenue = float(monthly_payments['total'] or 0)
    
    # System health (placeholder - can be enhanced with actual health checks)
    system_health = 95
    
    # Pending tasks (placeholder - can be enhanced with actual task system)
    pending_tasks = 0
    
    stats = {
        'totalUsers': total_users,
        'totalFarmers': total_farmers,
        'activeFarms': active_farms,
        'totalDevices': total_devices,
        'activeSubscriptions': active_subscriptions,
        'monthlyRevenue': monthly_revenue,
        'systemHealth': system_health,
        'pendingTasks': pending_tasks,
    }
    
    return Response(stats, status=status.HTTP_200_OK)