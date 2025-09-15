from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status, mixins, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from subscriptions.models import (
    SubscriptionType, Resource, FarmerSubscription,
    FarmerSubscriptionResource, Payment, SubscriptionStatus
)
from subscriptions.serializers import (
    SubscriptionTypeSerializer, ResourceSerializer,
    FarmerSubscriptionListSerializer, FarmerSubscriptionDetailSerializer,
    FarmerSubscriptionCreateSerializer, FarmerSubscriptionResourceSerializer,
    PaymentSerializer, SubscriptionUpgradeSerializer
)
from config.permissions import IsAdminOrReadOnly, IsFarmerOrAdmin, IsSubscriptionOwner
from .services import SubscriptionService
from .utils import get_available_resources, get_subscription_utilization

class SubscriptionTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for viewing subscription types."""
    queryset = SubscriptionType.objects.all().order_by('tier')
    serializer_class = SubscriptionTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

class ResourceViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for viewing resources."""
    queryset = Resource.objects.filter(status=True).order_by('resource_type', 'name')
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['resource_type', 'category', 'is_basic']
    search_fields = ['name', 'description']

    @action(detail=False, methods=['get'])
    def my_resources(self, request):
        """Return resources available to the current farmer based on their subscription."""
        user = request.user
        if not hasattr(user, 'farmer_profile'):
            return Response(
                {'detail': 'User is not a farmer'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        farmer = user.farmer_profile
        try:
            subscription = FarmerSubscription.objects.get(
                farmerID=farmer,
                status=SubscriptionStatus.ACTIVE,
                end_date__gte=timezone.now().date()
            )
            resources = get_available_resources(subscription)
            page = self.paginate_queryset(resources)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
                
            serializer = self.get_serializer(resources, many=True)
            return Response(serializer.data)
            
        except FarmerSubscription.DoesNotExist:
            # Return only basic resources if no active subscription
            resources = Resource.objects.filter(is_basic=True, status=True)
            serializer = self.get_serializer(resources, many=True)
            return Response(serializer.data)

class FarmerSubscriptionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    """
    API endpoint for managing farmer subscriptions.
    """
    permission_classes = [permissions.IsAuthenticated, IsFarmerOrAdmin]
    lookup_field = 'farmerSubscriptionID'
    
    def get_queryset(self):
        user = self.request.user
        queryset = FarmerSubscription.objects.all()

        # Admins can see all subscriptions
        if user.is_staff or user.is_superuser:
            return queryset.prefetch_related('resources__resourceID')

        # Farmers can only see their own subscriptions
        if hasattr(user, 'farmer_profile'):
            return queryset.filter(
                farmerID=user.farmer_profile
            ).prefetch_related('resources__resourceID')

        return queryset.none()
        
    def get_serializer_class(self):
        if self.action == 'list':
            return FarmerSubscriptionListSerializer
        elif self.action == 'retrieve':
            return FarmerSubscriptionDetailSerializer
        elif self.action == 'create':
            return FarmerSubscriptionCreateSerializer
        elif self.action == 'upgrade':
            return SubscriptionUpgradeSerializer
        return FarmerSubscriptionListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if getattr(self, 'action', None) == 'upgrade':
            lookup_key = self.lookup_field or 'pk'
            if lookup_key in self.kwargs:
                try:
                    context['subscription'] = self.get_object()
                except Exception:
                    print('DEBUG upgrade context: failed to resolve subscription with kwargs', self.kwargs)
        return context
        
    def perform_create(self, serializer):
        # The create logic is handled in the serializer
        return super().perform_create(serializer)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subscription = serializer.save()
        detail = FarmerSubscriptionDetailSerializer(subscription, context={'request': request})
        headers = self.get_success_headers(detail.data)
        return Response(detail.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=True, methods=['get'])
    def resources(self, request, pk=None):
        """Get all resources available for this subscription."""
        subscription = self.get_object()
        resources = get_available_resources(subscription)
        serializer = ResourceSerializer(resources, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def utilization(self, request, pk=None):
        """Get resource utilization for this subscription."""
        subscription = self.get_object()
        return Response(get_subscription_utilization(subscription))
    
    @action(detail=True, methods=['post'], serializer_class=SubscriptionUpgradeSerializer)
    def upgrade(self, request, farmerSubscriptionID=None):  # farmerSubscriptionID matches lookup_field
        """Upgrade to a higher subscription tier (direct service path)."""
        subscription = self.get_object()
        new_type_id = request.data.get('new_subscription_type_id')
        if not new_type_id:
            return Response({'detail': 'new_subscription_type_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            new_subscription = SubscriptionService.upgrade_subscription(subscription, new_type_id)
        except ValidationError as ve:
            return Response({'detail': str(ve.detail if hasattr(ve, 'detail') else ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:  # pragma: no cover
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        data = FarmerSubscriptionDetailSerializer(new_subscription).data
        return Response(data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a subscription (set to cancel at the end of the billing period)."""
        subscription = self.get_object()
        
        if subscription.status != SubscriptionStatus.ACTIVE:
            return Response(
                {'detail': 'Only active subscriptions can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        subscription.auto_renew = False
        subscription.save()
        
        return Response(
            {'detail': 'Subscription will be cancelled at the end of the billing period'},
            status=status.HTTP_200_OK
        )

class FarmerSubscriptionResourceViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    # Provide base queryset so router/action introspection works for all methods (including POST)
    queryset = FarmerSubscriptionResource.objects.all()
    serializer_class = FarmerSubscriptionResourceSerializer
    permission_classes = [permissions.IsAuthenticated, IsSubscriptionOwner]
    # Explicitly declare allowed methods to avoid 405 if Django/DRF infers incorrectly
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        # NestedSimpleRouter builds kwarg name as <lookup>_<parent_lookup_field>
        # Parent lookup name: 'subscription'; parent lookup_field on viewset: farmerSubscriptionID
        subscription_id = (
            self.kwargs.get('subscription_farmerSubscriptionID') or  # correct key from router
            self.kwargs.get('subscription_farmersubscriptionID') or   # legacy/mistyped fallback
            self.kwargs.get('subscription_pk')  # generic fallback
        )
        return FarmerSubscriptionResource.objects.filter(
            farmerSubscriptionID_id=subscription_id
        ).select_related('resourceID')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        subscription_id = (
            self.kwargs.get('subscription_farmerSubscriptionID') or
            self.kwargs.get('subscription_farmersubscriptionID') or
            self.kwargs.get('subscription_pk')
        )
        context['subscription'] = get_object_or_404(
            FarmerSubscription,
            pk=subscription_id
        )
        return context

    def perform_create(self, serializer):
        subscription_id = (
            self.kwargs.get('subscription_farmerSubscriptionID') or
            self.kwargs.get('subscription_farmersubscriptionID') or
            self.kwargs.get('subscription_pk')
        )
        subscription = get_object_or_404(
            FarmerSubscription,
            pk=subscription_id
        )
        serializer.save(farmerSubscriptionID=subscription)

    def create(self, request, *args, **kwargs):  # explicit for clarity (should be provided by mixin)
        return super().create(request, *args, **kwargs)

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset
        if user.is_staff or user.is_superuser:
            return qs
        if hasattr(user, 'farmer_profile'):
            return qs.filter(farmerSubscriptionID__farmerID=user.farmer_profile)
        return qs.none()

class SubscriptionStatusView(APIView):
    """
    API endpoint to check the current user's subscription status.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if not hasattr(request.user, 'farmer_profile'):
            return Response(
                {'detail': 'User is not a farmer'}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        farmer = request.user.farmer_profile
        
        try:
            subscription = FarmerSubscription.objects.get(
                farmerID=farmer,
                status=SubscriptionStatus.ACTIVE,
                end_date__gte=timezone.now().date()
            )
            
            serializer = FarmerSubscriptionDetailSerializer(subscription)
            return Response({
                'has_active_subscription': True,
                'subscription': serializer.data,
                'utilization': get_subscription_utilization(subscription)
            })
            
        except FarmerSubscription.DoesNotExist:
            return Response({
                'has_active_subscription': False,
                'message': 'No active subscription found',
                'available_subscriptions': SubscriptionTypeSerializer(
                    SubscriptionType.objects.all().order_by('tier'),
                    many=True
                ).data
            })

    def perform_create(self, serializer):
        farmer = getattr(self.request.user, 'farmer_profile', None)
        serializer.save(farmerID=farmer)


class SubscriptionStatsView(APIView):
    """
    API endpoint to get subscription statistics.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Calculate subscription statistics
        from django.db.models import Count, Sum, Avg, DecimalField
        from django.db.models.functions import Coalesce
        from decimal import Decimal
        
        stats = {
            'total_subscriptions': FarmerSubscription.objects.count(),
            'active_subscriptions': FarmerSubscription.objects.filter(
                status=SubscriptionStatus.ACTIVE
            ).count(),
            'pending_subscriptions': FarmerSubscription.objects.filter(
                status=SubscriptionStatus.PENDING
            ).count(),
            'cancelled_subscriptions': FarmerSubscription.objects.filter(
                status=SubscriptionStatus.CANCELLED
            ).count(),
            'total_revenue': float(Payment.objects.filter(
                status='COMPLETED'
            ).aggregate(
                total=Coalesce(Sum('amount'), Decimal('0'), output_field=DecimalField())
            )['total']),
            'subscription_type_breakdown': list(
                SubscriptionType.objects.annotate(
                    subscription_count=Count('farmer_subscriptions')
                ).values('name', 'tier', 'subscription_count')
            ),
            'monthly_revenue': float(Payment.objects.filter(
                status='COMPLETED',
                payment_date__year=timezone.now().year,
                payment_date__month=timezone.now().month
            ).aggregate(
                total=Coalesce(Sum('amount'), Decimal('0'), output_field=DecimalField())
            )['total'])
        }
        
        return Response(stats)


class BillingReportsView(APIView):
    """
    API endpoint to get billing reports.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        period = request.query_params.get('period', 'current_month')
        
        from django.db.models import Count, Sum, Avg, DecimalField
        from django.db.models.functions import Coalesce
        from decimal import Decimal
        from datetime import datetime, timedelta
        
        # Calculate date range based on period
        now = timezone.now()
        if period == 'current_month':
            start_date = now.replace(day=1).date()
            end_date = now.date()
        elif period == 'last_month':
            first_day_this_month = now.replace(day=1)
            last_month = first_day_this_month - timedelta(days=1)
            start_date = last_month.replace(day=1).date()
            end_date = last_month.date()
        elif period == 'current_year':
            start_date = now.replace(month=1, day=1).date()
            end_date = now.date()
        else:
            start_date = now.replace(day=1).date()
            end_date = now.date()
        
        # Calculate billing report data
        payments_in_period = Payment.objects.filter(
            payment_date__gte=start_date,
            payment_date__lte=end_date,
            status='COMPLETED'
        )
        
        total_revenue = payments_in_period.aggregate(
            total=Coalesce(Sum('amount'), Decimal('0'), output_field=DecimalField())
        )['total']
        
        subscription_revenue = payments_in_period.filter(
            farmerSubscriptionID__isnull=False
        ).aggregate(
            total=Coalesce(Sum('amount'), Decimal('0'), output_field=DecimalField())
        )['total']
        
        active_subscriptions = FarmerSubscription.objects.filter(
            status=SubscriptionStatus.ACTIVE,
            start_date__lte=end_date
        ).count()
        
        new_subscriptions = FarmerSubscription.objects.filter(
            start_date__gte=start_date,
            start_date__lte=end_date
        ).count()
        
        cancelled_subscriptions = FarmerSubscription.objects.filter(
            status=SubscriptionStatus.CANCELLED,
            end_date__gte=start_date,
            end_date__lte=end_date
        ).count()
        
        avg_subscription_value = FarmerSubscription.objects.filter(
            start_date__gte=start_date,
            start_date__lte=end_date
        ).aggregate(
            avg_value=Coalesce(Avg('subscription_typeID__cost'), Decimal('0'), output_field=DecimalField())
        )['avg_value']
        
        report = {
            'period': period,
            'period_label': f"{start_date.strftime('%B %Y')}" if period == 'current_month' else period.replace('_', ' ').title(),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_revenue': float(total_revenue),
            'subscription_revenue': float(subscription_revenue),
            'payment_revenue': float(total_revenue - subscription_revenue),
            'active_subscriptions': active_subscriptions,
            'new_subscriptions': new_subscriptions,
            'cancelled_subscriptions': cancelled_subscriptions,
            'average_subscription_value': float(avg_subscription_value or 0),
            'revenue_growth': 0.0,  # Can be calculated by comparing with previous period
            'subscription_growth': 0.0,  # Can be calculated by comparing with previous period
        }
        
        return Response(report)


## Removed duplicate FarmerSubscriptionResourceViewSet and PaymentViewSet definitions (now consolidated above)
