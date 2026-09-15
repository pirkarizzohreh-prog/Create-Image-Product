from django.contrib import admin

from .models import PipelineSettings, PromptTemplate, StorageSettings

admin.site.register(PipelineSettings)
admin.site.register(PromptTemplate)
admin.site.register(StorageSettings)
