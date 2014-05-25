from django.contrib import admin

from coding.models import (
        Sample, AssignmentTag, CodingAssignment)


class SampleAdmin(admin.ModelAdmin):
    filter_horizontal = ("pieces",)

admin.site.register(Sample, SampleAdmin)


admin.site.register(AssignmentTag)


class CodingAssignmentAdmin(admin.ModelAdmin):
    list_filter = ("coder", "sample", "state")
    list_display = (
            "piece",  "coder",
            "sample", "state", "creation_time")

    search_fields = ("piece__id", "piece__title", "sample__name")


admin.site.register(CodingAssignment, CodingAssignmentAdmin)
