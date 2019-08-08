from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

from django.views.generic import TemplateView
import pieces.views
import pieces.search
import coding.views
import codery.views
import django.contrib.auth.views


urlpatterns = [
    # Examples:
    url(r'^$', TemplateView.as_view(template_name='welcome.html'),
        name="codery-home"),

    url(r'^accounts/login/$', codery.views.login,
        name="codery-login"),
    url(r'^accounts/logout/$',
        django.contrib.auth.views.LogoutView.as_view(),
        {'template_name': 'logged_out.html'},
        name="codery-logout"),

    url(r'^admin/', admin.site.urls),

    url('^piece/(?P<id>[0-9]+)/$', pieces.views.show_piece,
        name="pieces-import_csv"),
    url('^piece/import-ln-html/$', pieces.views.import_ln_html,
        name="pieces-import_ln_html"),
    url('^piece/import-csv/$', pieces.views.import_csv,
        name="pieces-import_csv"),
    url('^piece/search/$', pieces.search.view_search_form,
        name="pieces-view_search_form"),
    url('^piece/search/large/$', pieces.search.view_large_search_form,
        name="pieces-view_large_search_form"),
    url('^piece/check-completeness/$', pieces.search.view_check_completeness,
        name="pieces-view_check_completeness"),

    url('^coding/create-sample/$', coding.views.create_sample,
        name="coding-create_sample"),
    url('^coding/assign/$', coding.views.assign_to_coders,
        name="coding-assign_to_coders"),
    url('^coding/assignments/$', coding.views.view_assignments,
        name="coding-view_assignments"),
    url('^coding/assignment/(?P<id>[0-9]+)/$', coding.views.view_assignment,
        name="coding-view_assignment"),
    url('^coding/assignments/by-tag/$', coding.views.list_assignment_tags,
        name="coding-list_assignment_tags"),
    url('^coding/assignments/by-tag/(?P<tag_id>[0-9]+)/$',
        coding.views.view_assignments_by_tag,
        name="coding-view_assignments_by_tag"),
    ]
