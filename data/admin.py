from django.contrib import admin
from models import *

admin.site.register(DDSApplicationCredential)
admin.site.register(DDSUserCredential)
admin.site.register(DDSResource)
admin.site.register(Workflow)
admin.site.register(WorkflowVersion)
admin.site.register(Job)
admin.site.register(JobParam)
admin.site.register(JobParamDDSFile)
