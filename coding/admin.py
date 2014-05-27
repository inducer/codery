from django.contrib import admin

from coding.models import (
        Sample, AssignmentTag, CodingAssignment)


class SampleAdmin(admin.ModelAdmin):
    filter_horizontal = ("pieces",)

admin.site.register(Sample, SampleAdmin)


class AssignmentTagAdmin(admin.ModelAdmin):
    list_filter = ("study",)
    list_display = ("name",  "study",)

admin.site.register(AssignmentTag, AssignmentTagAdmin)


class CodingAssignmentAdmin(admin.ModelAdmin):
    list_filter = ("coder", "tags", "piece__tags", "sample", "state")
    list_display = (
            "piece",  "coder",
            "sample", "state", "creation_time")

    search_fields = ("piece__id", "piece__title", "sample__name")

    filter_horizontal = ("tags",)


admin.site.register(CodingAssignment, CodingAssignmentAdmin)
