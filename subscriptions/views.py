from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from subscriptions.models import (
    SubscriptionType, Resource, FarmerSubscription, 
    FarmerSubscriptionResource, Payment, SubscriptionStatus, ResourceType
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
                farmer=farmer,
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
    
    def get_queryset(self):
        user = self.request.user
        queryset = FarmerSubscription.objects.all()
        
        # Admins can see all subscriptions
        if user.is_staff or user.is_superuser:
            return queryset.prefetch_related('resources__resource')
            
        # Farmers can only see their own subscriptions
        if hasattr(user, 'farmer_profile'):
            return queryset.filter(
                farmer=user.farmer_profile
            ).prefetch_related('resources__resource')
            
        return queryset.none()
        
    def get_serializer_class(self):
        if self.action == 'list':
            return FarmerSubscriptionListSerializer
        elif self.action == 'retrieve':
            return FarmerSubscriptionDetailSerializer
        elif self.action == 'create':
            return FarmerSubscriptionCreateSerializer
        return FarmerSubscriptionListSerializer
        
    def perform_create(self, serializer):
        # The create logic is handled in the serializer
        return super().perform_create(serializer)
    
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
    def upgrade(self, request, pk=None):
        """Upgrade to a higher subscription tier."""
        subscription = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            new_subscription = serializer.save(subscription=subscription)
            return Response(
                FarmerSubscriptionDetailSerializer(new_subscription).data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
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
    """
    API endpoint for managing resources within a subscription.
    """
    serializer_class = FarmerSubscriptionResourceSerializer
    permission_classes = [permissions.IsAuthenticated, IsSubscriptionOwner]
    
    def get_queryset(self):
        subscription_id = self.kwargs.get('subscription_pk')
        return FarmerSubscriptionResource.objects.filter(
            farmer_subscription_id=subscription_id
        ).select_related('resource')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['subscription'] = get_object_or_404(
            FarmerSubscription,
            pk=self.kwargs.get('subscription_pk')
        )
        return context
    
    def perform_create(self, serializer):
        subscription = get_object_or_404(
            FarmerSubscription,
            pk=self.kwargs.get('subscription_pk')
        )
        serializer.save(farmer_subscription=subscription)

class PaymentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing payments.
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Payment.objects.all()
        
        # Admins can see all payments
        if user.is_staff or user.is_superuser:
            return queryset
            
        # Farmers can only see their own payments
        if hasattr(user, 'farmer_profile'):
            return queryset.filter(
                farmer_subscription__farmer=user.farmer_profile
            )
            
        return queryset.none()

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
                farmer=farmer,
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
            return qs
        if hasattr(user, 'farmer_profile'):
            return qs.filter(farmer=user.farmer_profile)
        return qs.none()

    def perform_create(self, serializer):
        farmer = getattr(self.request.user, 'farmer_profile', None)
        serializer.save(farmer=farmer)

class FarmerSubscriptionResourceViewSet(viewsets.ModelViewSet):
    queryset = FarmerSubscriptionResource.objects.all()
    serializer_class = FarmerSubscriptionResourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_staff or getattr(user, 'is_superuser', False) or getattr(user, 'role', '').upper() == 'ADMINISTRATOR':
            return qs
        if hasattr(user, 'farmer_profile'):
            return qs.filter(farmer_subscription__farmer=user.farmer_profile)
        return qs.none()

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_staff or getattr(user, 'is_superuser', False) or getattr(user, 'role', '').upper() == 'ADMINISTRATOR':
            return qs
        if hasattr(user, 'farmer_profile'):
            return qs.filter(farmer_subscription__farmer=user.farmer_profile)
        return qs.none()
