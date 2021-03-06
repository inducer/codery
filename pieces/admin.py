from django.contrib import admin

from pieces.models import (
        PieceTag,
        Piece, Venue, Study, Keyword,
        PieceToStudyAssociation)


# {{{ studies

class KeywordInline(admin.TabularInline):
    model = Keyword
    extra = 10


class StudyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "start_date")

    date_hierarchy = "start_date"

    inlines = [KeywordInline]

admin.site.register(Study, StudyAdmin)

# }}}


# {{{ pieces

admin.site.register(PieceTag)


class PieceToStudyInline(admin.StackedInline):
    model = PieceToStudyAssociation
    extra = 2


class PieceAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "venue", "pub_date", "create_date")
    list_filter = ("tags", "studies", "publication_type", "samples", "venue")
    list_display_links = ("id", "title")

    search_fields = ('title', 'content', 'id')
    date_hierarchy = "pub_date"

    filter_horizontal = ("tags",)

    save_on_top = True

    inlines = [PieceToStudyInline]

admin.site.register(Piece, PieceAdmin)

# }}}


class VenueAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    list_display_links = ("id", "name")

    search_fields = ("name", "id")

admin.site.register(Venue, VenueAdmin)

# vim: foldmethod=marker
