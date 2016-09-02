from django.contrib import admin

from coding.models import (
        Sample, AssignmentTag, CodingAssignment, CodingAssignmentActivity)


class SampleAdmin(admin.ModelAdmin):
    list_display = ("id",  "study", "name", "creator", "create_date")
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

    raw_id_fields = ("piece",)

admin.site.register(CodingAssignment, CodingAssignmentAdmin)


class CodingAssignmentActivityAdmin(admin.ModelAdmin):
    search_fields = (
            "assignment__piece__id",
            "assignment__piece__title",
            "actor__name",
            )

    list_display = ("assignment", "action_time", "actor", "action", "state")
    list_filter = ("actor", "action", "state")

    date_hierarchy = "action_time"

    raw_id_fields = ("assignment",)

admin.site.register(CodingAssignmentActivity, CodingAssignmentActivityAdmin)
