from django.conf.urls import url, include
from django.contrib import admin
from rest_framework.authtoken.views import obtain_auth_token
from django.views.generic.base import TemplateView
from data import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include('data.urls')),
    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),
    url(r'^api-auth-token/', obtain_auth_token),
    url(r'^auth/authorize/$', views.authorize, name='auth-authorize'),
    url(r'^auth/code_callback$', views.authorize_callback, name='auth-callback'),
    url(r'^auth/unconfigured/$', TemplateView.as_view(template_name='gcb_web_auth/unconfigured.html'), name='auth-unconfigured'),
]
