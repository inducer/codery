from django.shortcuts import render, get_object_or_404
from pieces.models import Piece, Keyword, Study

from django.contrib.auth.decorators import (
        login_required,
        permission_required)

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout

import django.forms as forms

import re
import sys


@login_required
def view_piece(request, id):
    piece = get_object_or_404(Piece, pk=id)

    paragraphs = piece.content.split("\n")

    keywords = [kw.word for kw in Keyword.objects.filter(study=piece.study)]
    keyword_res = [re.compile(re.escape(word), re.IGNORECASE)
            for word in keywords]

    def add_highlights(text):
        def add_highight(t):
            return '<span style="color:red; font-weight:bold;">%s</span>' % t.group(0)

        for kwre in keyword_res:
            text, _ = kwre.subn(add_highight, text)

        return text

    content = "\n".join(
            "<p>%s</p>" % add_highlights(paragraph)
            for paragraph in paragraphs)

    return render(request, "pieces/piece.html", dict(piece=piece, content=content))



class ImportLNForm(forms.Form):
    study = forms.ModelChoiceField(queryset=Study.objects, required=True)
    html_file = forms.FileField()

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-2"
        self.helper.field_class = "col-lg-8"

        self.helper.add_input(Submit("submit", "Submit", css_class="col-lg-offset-2"))
        super(ImportLNForm, self).__init__(*args, **kwargs)


@permission_required("pieces.bulk_import")
def import_ln_html(request):
    if request.method == "POST":
        form = ImportLNForm(request.POST, request.FILES)
        if form.is_valid():
            from pieces.lexis import import_ln_html

            was_successful = True
            try:
                log_lines = import_ln_html(
                        form.cleaned_data["study"],
                        request.FILES["html_file"],
                        )
                log = "\n".join(log_lines)
            except Exception, e:
                was_successful = False
                from traceback import format_exception
                log = "".join(format_exception(*sys.exc_info()))

            return render(request, 'pieces/import-result.html', {
                "log": log,
                "was_successful": was_successful,
                })
    else:
        form = ImportLNForm() # An unbound form

    return render(request, 'pieces/import-ln.html', {
        "form": form,
    })

