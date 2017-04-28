from django.conf.urls import url, include
from django.contrib import admin
from rest_framework.authtoken.views import obtain_auth_token
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include('data.urls')),
    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),
    url(r'^api-auth-token/', obtain_auth_token),
    url(r'^auth/', include('gcb_web_auth.urls')),
    url(r'^accounts/login/$', auth_views.login, {'template_name': 'gcb_web_auth/login.html'}, name='login'),
    url(r'^accounts/logout/$', auth_views.logout, {'template_name': 'gcb_web_auth/logged_out.html'}, name='logout'),
    url(r'^accounts/login-local/$', auth_views.login, {'template_name': 'gcb_web_auth/login-local.html'},
        name='login-local'),
    # Redirect / to /accounts/login
    url(r'^$', RedirectView.as_view(pattern_name='auth-home', permanent=False)),
]
