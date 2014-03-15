from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from django.views.generic import TemplateView

urlpatterns = patterns('',
    # Examples:
    (r'^$', TemplateView.as_view(template_name='welcome.html')),
    # url(r'^blog/', include('blog.urls')),

    (r'^accounts/login/$', 'codery.views.login',),
    (r'^accounts/logout/$',
        'django.contrib.auth.views.logout',
        {'template_name': 'logged_out.html'}),

    url(r'^admin/', include(admin.site.urls)),

    ('^piece/(?P<id>[0-9]+)/$', 'pieces.views.view_piece'),
    ('^piece/import-ln-html/$', 'pieces.views.import_ln_html'),
)
