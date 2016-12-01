from data import api
from django.conf.urls import url, include
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'projects', api.ProjectsViewSet, 'project')
router.register(r'workflows', api.WorkflowsViewSet, 'workflow')
router.register(r'workflow-versions', api.WorkflowVersionsViewSet, 'workflowversion')
router.register(r'jobs', api.JobsViewSet, 'job')
router.register(r'job-params', api.JobParamsViewSet, 'jobparam')
router.register(r'job-params-ddsfile', api.JobParamDDSFilesViewSet, 'jobparamddsfile')
router.register(r'dds-app-credentials', api.DDSAppCredViewSet, 'ddsapplicationcredential')
router.register(r'dds-user-credentials', api.DDSUserCredViewSet, 'ddsusercredential')

urlpatterns = [
    url(r'^', include(router.urls)),
]