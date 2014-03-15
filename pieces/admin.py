from django.contrib import admin

from pieces.models import Piece, Venue, Study, Keyword

class PieceAdmin(admin.ModelAdmin):
    list_filter = ('venue',)
    search_fields = ('title', 'content')
    date_hierarchy = "load_date"

    save_on_top = True

admin.site.register(Piece, PieceAdmin)


class KeywordInline(admin.StackedInline):
    model = Keyword
    extra = 10

class StudyAdmin(admin.ModelAdmin):
    inlines = [KeywordInline]

admin.site.register(Study, StudyAdmin)

admin.site.register(Venue)
