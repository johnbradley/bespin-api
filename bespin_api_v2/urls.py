from data import api as data_api
from bespin_api_v2 import api
from django.conf.urls import url, include
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'workflows', data_api.WorkflowsViewSet, 'workflow')
router.register(r'workflow-versions', api.WorkflowVersionsViewSet, 'workflowversion')
router.register(r'workflow-configurations', api.WorkflowConfigurationViewSet, 'workflowconfigurations')
router.register(r'vm-strategies', api.VMStrategyViewSet, 'vmstrategies')
router.register(r'jobs', api.JobsViewSet, 'job')
router.register(r'job-file-stage-groups', data_api.JobFileStageGroupViewSet, 'jobfilestagegroup')
router.register(r'dds-job-input-files', data_api.DDSJobInputFileViewSet, 'ddsjobinputfile')
router.register(r'url-job-input-files', data_api.URLJobInputFileViewSet, 'urljobinputfile')
router.register(r'dds-endpoints', data_api.DDSEndpointViewSet, 'ddsendpoint')
router.register(r'dds-user-credentials', data_api.DDSUserCredViewSet, 'ddsusercredential')

router.register(r'admin/workflows', api.AdminWorkflowViewSet, 'admin_workflow')
router.register(r'admin/workflow-versions', api.AdminWorkflowVersionViewSet, 'admin_workflowversion')
router.register(r'admin/workflow-configurations', api.AdminWorkflowConfigurationViewSet, 'admin_workflowconfiguration')

urlpatterns = [
    url(r'^', include(router.urls)),
]
