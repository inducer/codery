from django.contrib import admin

from coding.models import Sample, CodingAssignment


class SampleAdmin(admin.ModelAdmin):
    filter_horizontal = ("pieces",)

admin.site.register(Sample, SampleAdmin)


class CodingAssignmentAdmin(admin.ModelAdmin):
    list_filter = ("coder", "sample", "state")
    list_display = ("piece", "coder", "sample", "state", "creation_time")

    search_fields = ('piece__title', 'sample__name')

admin.site.register(CodingAssignment, CodingAssignmentAdmin)
