from django.shortcuts import render, get_object_or_404
from pieces.models import Study, Piece, PieceTag, AUTOMATIC_PIECE_TAGS

from django.contrib.auth.decorators import (
        permission_required)

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

import django.forms as forms

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
                Submit("submit", "Submit", css_class="col-lg-offset-2"))
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
