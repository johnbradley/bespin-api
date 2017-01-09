from data import api
from django.conf.urls import url, include
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'dds-projects', api.DDSProjectsViewSet, 'dds-projects')
router.register(r'dds-project-contents', api.DDSProjectContentsViewSet, 'dds-project-contents')
router.register(r'workflows', api.WorkflowsViewSet, 'workflow')
router.register(r'workflow-versions', api.WorkflowVersionsViewSet, 'workflowversion')
router.register(r'jobs', api.JobsViewSet, 'job')
router.register(r'job-input-files', api.JobInputFileViewSet, 'jobinputfile')
router.register(r'dds-job-input-files', api.DDSJobInputFileViewSet, 'ddsjobinputfile')
router.register(r'url-job-input-files', api.URLJobInputFileViewSet, 'urljobinputfile')
router.register(r'dds-endpoints', api.DDSEndpointViewSet, 'ddsendpoint')
router.register(r'dds-user-credentials', api.DDSUserCredViewSet, 'ddsusercredential')
router.register(r'job-errors', api.JobErrorViewSet, 'joberror')
router.register(r'job-output-dirs', api.JobOutputDirViewSet, 'joboutputdir')

# Routes that require admin user
router.register(r'admin/jobs', api.AdminJobsViewSet, 'admin_job')
router.register(r'admin/job-input-files', api.AdminJobInputFileViewSet, 'admin_jobinputfile')
router.register(r'admin/dds-user-credentials', api.AdminDDSUserCredentialsViewSet, 'admin_ddsusercredentials')
router.register(r'admin/job-errors', api.AdminJobErrorViewSet, 'admin_joberror')

urlpatterns = [
    url(r'^', include(router.urls)),
]

