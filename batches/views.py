from django.shortcuts import render
from rest_framework import viewsets, permissions
from batches.models import Batch, ActivitySchedule, BatchActivity
from batches.serializers import (
    BatchSerializer, ActivityScheduleSerializer, BatchActivitySerializer
)

# Create your views here.

class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = [permissions.IsAuthenticated]

class ActivityScheduleViewSet(viewsets.ModelViewSet):
    queryset = ActivitySchedule.objects.all()
    serializer_class = ActivityScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

class BatchActivityViewSet(viewsets.ModelViewSet):
    queryset = BatchActivity.objects.all()
    serializer_class = BatchActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
