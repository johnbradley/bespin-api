from django.contrib import admin
from models import *

admin.site.register(DDSEndpoint)
admin.site.register(DDSUserCredential)
admin.site.register(Workflow)
admin.site.register(WorkflowVersion)
admin.site.register(Job)
admin.site.register(JobOutputDir)
admin.site.register(JobInputFile)
admin.site.register(DDSJobInputFile)
admin.site.register(URLJobInputFile)
admin.site.register(JobError)
admin.site.register(LandoConnection)
