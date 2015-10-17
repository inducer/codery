from django.shortcuts import render, get_object_or_404
from django.utils.translation import (
        ugettext_lazy as _, pgettext_lazy, string_concat)
from django.contrib import messages  # noqa
from django.db import transaction

import django.forms as forms

from pieces.models import (
        Venue, Study, Piece, PieceTag, AUTOMATIC_PIECE_TAGS,
        PieceToStudyAssociation)

from django.contrib.auth.decorators import (
        permission_required)

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

import sys


def show_piece(request, id):
    piece = get_object_or_404(Piece, pk=id)
    paragraphs = piece.content.split("\n")

    content = "\n".join(
            "<p>%s</p>" % paragraph
            for paragraph in paragraphs)

    from json import loads
    extra_data = loads(piece.extra_data_json)
    assert isinstance(extra_data, dict)

    extra_data = sorted(extra_data.iteritems())

    return render(request, 'pieces/piece.html', {
        "piece": piece,
        "extra_data": extra_data,
        "content": content,
        "may_see_non_coder_tags": request.user.has_perm("may_see_non_coder_tags"),
        })


# {{{ lexis nexis import

class ImportLNForm(forms.Form):
    studies = forms.ModelMultipleChoiceField(
            queryset=Study.objects, required=True)
    tags = forms.ModelMultipleChoiceField(
            queryset=PieceTag.objects
            .exclude(name__in=AUTOMATIC_PIECE_TAGS)
            .order_by("name"),
            required=False,
            help_text="Select piece tags (if any) to apply to newly "
            "imported pieces.")
    html_file = forms.FileField()
    repair_content = forms.BooleanField(required=False,
            help_text="Check this box if a previous import of the same HTML "
            "went wrong (perhaps due to an import issue in Codery). "
            "For each piece to be imported, Codery will find all "
            "existing pieces that match the metadata "
            "of the newly imported piece and replace their content with "
            "the one from the new import. The old piece's metadata stays untouched, "
            "and its ID as well as its association with studies and samples stays "
            "the same. If this box is checked, the 'tags' and 'studies' boxes above "
            "are not considered at all.")

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-2"
        self.helper.field_class = "col-lg-8"

        self.helper.add_input(
                Submit("submit", "Submit"))
        super(ImportLNForm, self).__init__(*args, **kwargs)


@permission_required("pieces.bulk_import")
def import_ln_html(request):
    from django.utils.timezone import now

    if request.method == "POST":
        form = ImportLNForm(request.POST, request.FILES)
        if form.is_valid():
            from pieces.lexis import import_ln_html

            was_successful = True
            log_lines = []
            try:
                data = form.cleaned_data
                import_ln_html(
                        log_lines,
                        studies=data["studies"],
                        html_file=request.FILES["html_file"],
                        tags=data["tags"],
                        repair_content=data["repair_content"],
                        create_date=now(),
                        creator=request.user,
                        )
                log = "\n".join(log_lines)
            except Exception:
                was_successful = False
                from traceback import format_exception
                log = "\n".join(log_lines) + "".join(
                        format_exception(*sys.exc_info()))

            return render(request, 'bulk-result.html', {
                "process_description": "Import Result",
                "log": log,
                "status": (
                    "Import successful."
                    if was_successful
                    else "Import failed. See above for error. "
                    "No changes have been made to the database."),
                "was_successful": was_successful,
                })
    else:
        form = ImportLNForm()  # An unbound form

    return render(request, 'generic-form.html', {
        "form": form,
        "form_description": "Import LexisNexis HTML",
    })

# }}}


# {{{ csv import

class CSVImportForm(forms.Form):
    venue = forms.ModelChoiceField(
            queryset=Venue.objects, required=True)
    studies = forms.ModelMultipleChoiceField(
            queryset=Study.objects, required=True)
    tags = forms.ModelMultipleChoiceField(
            queryset=PieceTag.objects
            .exclude(name__in=AUTOMATIC_PIECE_TAGS)
            .order_by("name"),
            required=False,
            help_text="Select piece tags (if any) to apply to newly "
            "imported pieces.")
    file = forms.FileField(
            label=_("File"),
            help_text="CSV file with header row")

    title_column = forms.IntegerField(
            help_text=_("1-based column index for a title"),
            min_value=1, required=False)
    content_column = forms.IntegerField(
            help_text=_("1-based column index for content"),
            min_value=1)
    url_column = forms.IntegerField(
            help_text=_("1-based column index for a URL"),
            min_value=1, required=False)
    byline_column = forms.IntegerField(
            help_text=_("1-based column index for the byline"),
            min_value=1, required=False)

    def __init__(self, *args, **kwargs):
        super(CSVImportForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-2"
        self.helper.field_class = "col-lg-8"

        self.helper.add_input(Submit("preview", _("Preview")))
        self.helper.add_input(Submit("import", _("Import")))


def smart_truncate(content, length=100, suffix='...'):
    if len(content) <= length:
        return content
    else:
        return content[:length].rsplit(' ', 1)[0]+suffix


def csv_to_pieces(
        log_lines, file_contents,
        venue,
        title_column, content_column, url_column, byline_column,
        creator, create_date):
    result = []

    csv_data = file_contents.read()
    import re
    new_line_re = re.compile("\n\r?|\r\n?")
    csv_lines = new_line_re.split(csv_data)

    import csv

    used_columns = [
        title_column, content_column, url_column, byline_column]
    used_columns = [col-1 for col in used_columns if col is not None]

    reader = csv.reader(csv_lines)
    header = None

    import re
    url_regex = re.compile(
        'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|'
        '(?:%[0-9a-fA-F][0-9a-fA-F]))+')

    def get_idx(row, index):
        index -= 1
        if index >= len(row):
            return None
        return row[index]

    for i, row in enumerate(reader):
        if header is None:
            header = row
            continue

        row = [col.decode("utf-8", errors="replace")
                for col in row]

        piece = Piece()

        piece.content = get_idx(row, content_column)
        if not piece.content:
            log_lines.append("Piece %d had no content. Skipping." % (i+1))
            continue

        if title_column is not None:
            piece.title = get_idx(row, title_column)
        else:
            piece.title = smart_truncate(piece.content, 60)

        piece.venue = venue

        if url_column is not None:
            piece.url = get_idx(row, url_column)

        if not piece.url:
            url_match = url_regex.search(piece.content)
            if url_match:
                piece.url = url_match.group(0)

        if byline_column is not None:
            piece.byline = row.get_idx(row, byline_column)

        extra_data = {}
        for icol, (col, header_col) in enumerate(zip(row, header)):
            if icol in used_columns:
                continue

            extra_data[header_col] = col

        from json import dumps
        piece.extra_data_json = dumps(extra_data)

        piece.creator = creator
        piece.create_date = create_date

        result.append(piece)

    return result


@permission_required("pieces.bulk_import")
@transaction.atomic
def import_csv(request):
    from django.utils.timezone import now

    form_text = ""

    log_lines = []
    now_datetime = now()

    if request.method == "POST":
        form = CSVImportForm(request.POST, request.FILES)

        is_import = "import" in request.POST
        if form.is_valid():
            try:
                pieces = csv_to_pieces(
                        log_lines=log_lines,
                        file_contents=request.FILES["file"],
                        venue=form.cleaned_data["venue"],
                        title_column=form.cleaned_data["title_column"],
                        content_column=form.cleaned_data["content_column"],
                        url_column=form.cleaned_data["url_column"],
                        byline_column=form.cleaned_data["byline_column"],
                        creator=request.user, create_date=now_datetime)
            except Exception as e:
                messages.add_message(request, messages.ERROR,
                        string_concat(
                            pgettext_lazy("Start of Error message",
                                "Error"),
                            ": %(err_type)s %(err_str)s")
                        % {
                            "err_type": type(e).__name__,
                            "err_str": str(e)})
            else:
                messages.add_message(request, messages.INFO,
                        _("%(total)d pieces found.")
                        % {'total': len(pieces)})

                from django.template.loader import render_to_string

                if is_import:
                    for piece in pieces:
                        piece.save()
                        piece.tags = form.cleaned_data["tags"]
                        piece.save()

                        for study in form.cleaned_data["studies"]:
                            pts = PieceToStudyAssociation()
                            pts.study = study
                            pts.piece = piece
                            pts.create_date = now_datetime
                            pts.creator = request.user
                            pts.save()

                    form_text = render_to_string(
                            "pieces/piece-import-preview.html", {
                                "pieces": pieces,
                                "log_lines": log_lines,
                                })
                    messages.add_message(request, messages.SUCCESS,
                            _("%d pieces imported.") % len(pieces))
                else:
                    form_text = render_to_string(
                            "pieces/piece-import-preview.html", {
                                "pieces": pieces,
                                "log_lines": log_lines,
                                })

    else:
        form = CSVImportForm()

    return render(request, 'generic-form.html', {
        "form": form,
        "doc": form_text,
        "form_description": "Import CSV",
    })

# }}}


# vim: foldmethod=marker
