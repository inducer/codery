from django.shortcuts import render
from pieces.models import Study

from django.contrib.auth.decorators import (
        permission_required)

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

import django.forms as forms

import sys


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
            log_lines = []
            try:
                import_ln_html(
                        log_lines,
                        form.cleaned_data["studies"],
                        request.FILES["html_file"],
                        create_date=datetime.now(),
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
