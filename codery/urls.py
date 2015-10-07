from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from django.views.generic import TemplateView
import pieces.views
import pieces.search
import coding.views
import codery.views
import django.contrib.auth.views


urlpatterns = patterns('',
    # Examples:
    (r'^$', TemplateView.as_view(template_name='welcome.html')),
    # url(r'^blog/', include('blog.urls')),

    (r'^accounts/login/$', codery.views.login,),
    (r'^accounts/logout/$',
        django.contrib.auth.views.logout,
        {'template_name': 'logged_out.html'}),

    url(r'^admin/', include(admin.site.urls)),

    ('^piece/(?P<id>[0-9]+)/$', pieces.views.show_piece),
    ('^piece/import-ln-html/$', pieces.views.import_ln_html),
    ('^piece/import-csv/$', pieces.views.import_csv),
    ('^piece/search/$', pieces.search.view_search_form),
    ('^piece/search/large/$', pieces.search.view_large_search_form),

    ('^coding/create-sample/$', coding.views.create_sample),
    ('^coding/assign/$', coding.views.assign_to_coders),
    ('^coding/assignments/$', coding.views.view_assignments),
    ('^coding/assignment/(?P<id>[0-9]+)/$', coding.views.view_assignment),
    ('^coding/assignments/by-tag/$', coding.views.list_assignment_tags),
    ('^coding/assignments/by-tag/(?P<tag_id>[0-9]+)/$',
        coding.views.view_assignments_by_tag),
)
