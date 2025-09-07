from django.shortcuts import render
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from accounts.models import User, Farmer
from accounts.serializers import UserSerializer, FarmerSerializer, UserCreateSerializer
from config.permissions import IsAdminOrReadOnly

# Create your views here.

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            # Allow unauthenticated users to self-register
            return [permissions.AllowAny()]
        if self.action in ['list', 'retrieve', 'update', 'partial_update', 'destroy']:
            # Admin-only for management operations
            return [permissions.IsAuthenticated(), IsAdminOrReadOnly()]
        # Default authenticated
        permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class FarmerViewSet(viewsets.ModelViewSet):
    queryset = Farmer.objects.all()
    serializer_class = FarmerSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        """Set the user to the currently authenticated user when creating a new farmer."""
        if not hasattr(self.request.user, 'farmer_profile'):
            serializer.save(user=self.request.user)
        else:
            raise serializers.ValidationError({"error": "User already has a farmer profile"})
    
    @action(detail=False, methods=['get'])
    def my_farm(self, request):
        """Get current farmer's farm information"""
        if hasattr(request.user, 'farmer_profile'):
            farmer = request.user.farmer_profile
            serializer = self.get_serializer(farmer)
            return Response(serializer.data)
        return Response({'error': 'User is not a farmer'}, status=status.HTTP_400_BAD_REQUEST)
