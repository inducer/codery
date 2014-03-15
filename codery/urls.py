from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from django.views.generic import TemplateView

urlpatterns = patterns('',
    # Examples:
    (r'^$', TemplateView.as_view(template_name='welcome.html')),
    # url(r'^blog/', include('blog.urls')),

    (r'^accounts/login/$',
        'django.contrib.auth.views.login',
        {'template_name': 'login.html'}),

    url(r'^admin/', include(admin.site.urls)),

    ('^piece/(?P<id>[0-9]+)/$', 'pieces.views.view_piece'),
)
