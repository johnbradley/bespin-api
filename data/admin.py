from django.contrib import admin
from models import *


class CreateOnlyWorkflowVersionAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('workflow', 'object_name', 'version', 'url')
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(DDSEndpoint)
admin.site.register(DDSUserCredential)
admin.site.register(Workflow)
admin.site.register(WorkflowVersion, CreateOnlyWorkflowVersionAdmin)
admin.site.register(Job)
admin.site.register(JobOutputDir)
admin.site.register(JobInputFile)
admin.site.register(DDSJobInputFile)
admin.site.register(URLJobInputFile)
admin.site.register(JobError)
admin.site.register(LandoConnection)
admin.site.register(JobQuestion)
admin.site.register(JobAnswer)
admin.site.register(JobStringAnswer)
admin.site.register(JobDDSFileAnswer)
admin.site.register(JobQuestionnaire)
admin.site.register(JobAnswerSet)
admin.site.register(JobDDSOutputDirectoryAnswer)
