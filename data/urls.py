from . import views
from django.conf.urls import url
from django.views.generic import RedirectView

urlpatterns = [
    url(r'^$', RedirectView.as_view(pattern_name='browse_projects')),
    url(r'^browse_projects/$', views.browse_projects, name='browse_projects'),
    url(r'^pick_resource/$', views.pick_resource, name='pick_resource'),
]