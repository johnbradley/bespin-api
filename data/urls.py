from data import api
from django.conf.urls import url, include
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'projects', api.ProjectsViewSet, 'project')

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),
]