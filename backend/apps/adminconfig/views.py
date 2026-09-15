from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsAdmin

from .models import PipelineSettings, PromptTemplate, StorageSettings
from .serializers import PipelineSettingsSerializer, PromptTemplateSerializer, StorageSettingsSerializer


class PipelineSettingsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response(PipelineSettingsSerializer(PipelineSettings.get_active()).data)

    def put(self, request):
        obj = PipelineSettings.get_active()
        serializer = PipelineSettingsSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(is_active=True)
        return Response(serializer.data)


class PromptTemplateViewSet(viewsets.ModelViewSet):
    queryset = PromptTemplate.objects.all()
    serializer_class = PromptTemplateSerializer
    permission_classes = [IsAdmin]


class StorageSettingsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response(StorageSettingsSerializer(StorageSettings.get_active()).data)

    def put(self, request):
        obj = StorageSettings.get_active()
        serializer = StorageSettingsSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(is_active=True)
        return Response(serializer.data)
