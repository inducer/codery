from django.shortcuts import render, get_object_or_404
from pieces.models import Piece, Keyword, Study

from django.contrib.auth.decorators import (
        login_required,
        permission_required)

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

import django.forms as forms

import re
import sys


class Highlighter:
    def __init__(self, study):
        keywords = [kw.word for kw in Keyword.objects.filter(study=study)]
        self.keyword_res = [re.compile(re.escape(word), re.IGNORECASE)
                for word in keywords]

    def __call__(self, text):
        def add_highight(t):
            return '<span style="color:red; font-weight:bold;">%s</span>' \
                    % t.group(0)

        for kwre in self.keyword_res:
            text, _ = kwre.subn(add_highight, text)

        return text


@login_required
def view_piece(request, id):
    # TODO Delete me
    piece = get_object_or_404(Piece, pk=id)

    paragraphs = piece.content.split("\n")

    highlighter = Highlighter(piece.study)

    content = "\n".join(
            "<p>%s</p>" % highlighter(paragraph)
            for paragraph in paragraphs)

    return render(request, "pieces/piece.html", dict(piece=piece, content=content))


# {{{ lexis nexis import

class ImportLNForm(forms.Form):
    studies = forms.ModelMultipleChoiceField(
            queryset=Study.objects, required=True)
    html_file = forms.FileField()

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
    if request.method == "POST":
        form = ImportLNForm(request.POST, request.FILES)
        if form.is_valid():
            from pieces.lexis import import_ln_html

            was_successful = True
            from datetime import datetime
            try:
                log_lines = import_ln_html(
                        form.cleaned_data["studies"],
                        request.FILES["html_file"],
                        create_date=datetime.now(),
                        creator=request.user,
                        )
                log = "\n".join(log_lines)
            except Exception:
                was_successful = False
                from traceback import format_exception
                log = "".join(format_exception(*sys.exc_info()))

            return render(request, 'bulk-result.html', {
                "process_description": "Import Result",
                "log": log,
                "status": "Import successful."
                    if was_successful
                    else "Import failed. See above for error. "
                    "No changes have been made to the database.",
                "was_successful": was_successful,
                })
    else:
        form = ImportLNForm()  # An unbound form

    return render(request, 'generic-form.html', {
        "form": form,
        "form_description": "Import LexisNexis HTML",
    })

# }}}
