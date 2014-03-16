from django.shortcuts import render

import django.forms as forms

from django.contrib.auth.models import User

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

#import sys
from pieces.models import Keyword, Study, PieceToStudyAssociation
from coding.models import Sample, CodingAssignment

from django.contrib.auth.decorators import (
        login_required,
        permission_required)

from django.db import transaction


# {{{ sample creation

class CreateSampleForm(forms.Form):
    study = forms.ModelChoiceField(
            queryset=Study.objects, required=True)
    name = forms.CharField(min_length=1)
    sample_size = forms.IntegerField(required=True)

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-2"
        self.helper.field_class = "col-lg-8"

        self.helper.add_input(
                Submit("submit", "Submit", css_class="col-lg-offset-2"))
        super(CreateSampleForm, self).__init__(*args, **kwargs)

    def clean(self):
        study = self.cleaned_data.get("study")
        sample_size = self.cleaned_data.get("sample_size")

        if study and sample_size:
            piece_count = PieceToStudyAssociation.objects \
                    .filter(study=study).count()

            if sample_size > piece_count:
                raise forms.ValidationError(
                        "Cannot sample more pieces than are present in study.")

        return self.cleaned_data


@transaction.atomic
def create_sample_backend(study, name, sample_size, create_date, creator):
    pieces = [pts.piece
            for pts in PieceToStudyAssociation.objects.filter(study=study)]

    from random import sample
    selected = sample(pieces, sample_size)

    new_sample = Sample()
    new_sample.study = study
    new_sample.name = name
    new_sample.create_date = create_date
    new_sample.creator = creator
    new_sample.save()

    new_sample.pieces.add(*selected)
    new_sample.save()


@permission_required("coding.create_sample")
def create_sample(request):
    if request.method == "POST":
        form = CreateSampleForm(request.POST, request.FILES)
        if form.is_valid():
            log_lines = []

            from datetime import datetime
            create_sample_backend(
                    form.cleaned_data["study"],
                    form.cleaned_data["name"],
                    form.cleaned_data["sample_size"],
                    create_date=datetime.now(),
                    creator=request.user)

            return render(request, 'bulk-result.html', {
                "process_description": "Sample Creation Result",
                "log": "\n".join(log_lines),
                "status": "Sample created.",
                "was_successful": True,
                })
    else:
        form = CreateSampleForm()  # An unbound form

    return render(request, 'generic-form.html', {
        "form": form,
        "form_description": "Create Sample",
    })

# }}}


# {{{ assign to coders

class AssignToCodersForm(forms.Form):
    sample = forms.ModelChoiceField(
            queryset=Sample.objects, required=True)
    assign_only_unassigned_pieces = forms.BooleanField(required=False)
    coders = forms.ModelMultipleChoiceField(User.objects, required=True)
    pieces_per_coder = forms.IntegerField(required=True)

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-2"
        self.helper.field_class = "col-lg-8"

        self.helper.add_input(
                Submit("submit", "Submit", css_class="col-lg-offset-2"))
        super(AssignToCodersForm, self).__init__(*args, **kwargs)


@transaction.atomic
def assign_to_coders_backend(sample, assign_only_unassigned_pieces,
        coders, pieces_per_coder, creation_time, creator):
    log_lines = []

    coder_idx_to_count = {}

    num_coders = len(coders)

    coder_idx = 0
    for piece in sample.pieces.all():
        if (assign_only_unassigned_pieces
                and CodingAssignment.objects.filter(
                    sample=sample, piece=piece).count()):
            log_lines.append("Piece '%d: %s' already assigned to someone, skipping."
                    % (piece.id, unicode(piece)[:20]))
            continue

        local_coder_idx = coder_idx
        assignment_tries = 0

        # was this piece already assigned to this coder? (if so, try next)
        # Note that, in its desperation, this may assign a few more items
        # to a coder than are technically allowed by their limit.
        while (
                CodingAssignment.objects.filter(
                    sample=sample, piece=piece,
                    coder=coders[local_coder_idx]).count()
                and assignment_tries < num_coders):
            local_coder_idx = (local_coder_idx + 1) % num_coders
            assignment_tries += 1

        if assignment_tries >= num_coders:
            log_lines.append("Piece '%d: %s' already assigned "
                    "to all coders, skipping." % (piece.id, unicode(piece)[:20]))
            continue

        assmt = CodingAssignment()
        assmt.coder = coders[local_coder_idx]
        assmt.piece = piece
        assmt.sample = sample
        assmt.state = "NS"
        assmt.latest_state_time = creation_time
        assmt.creation_time = creation_time
        assmt.creator = creator
        assmt.save()

        coder_idx_to_count[local_coder_idx] = \
                coder_idx_to_count.get(local_coder_idx, 0) + 1

        find_coder_tries = 0
        while find_coder_tries < num_coders:
            coder_idx = (coder_idx + 1) % num_coders
            if coder_idx_to_count.get(coder_idx, 0) < pieces_per_coder:
                break
            find_coder_tries += 1

        if find_coder_tries >= num_coders:
            log_lines.append("All coders have reached their item limit, "
                    "stopping.")
            break

    for coder_idx, coder in enumerate(coders):
        log_lines.append("%s: %d new items assigned"
                % (coder, coder_idx_to_count.get(coder_idx, 0)))

    return log_lines


@permission_required("coding.assign_to_coders")
def assign_to_coders(request):
    if request.method == "POST":
        form = AssignToCodersForm(request.POST, request.FILES)
        if form.is_valid():
            log_lines = []

            from datetime import datetime
            log_lines = assign_to_coders_backend(
                    form.cleaned_data["sample"],
                    form.cleaned_data["assign_only_unassigned_pieces"],
                    form.cleaned_data["coders"],
                    form.cleaned_data["pieces_per_coder"],
                    creation_time=datetime.now(),
                    creator=request.user)

            was_successful = True
            return render(request, 'bulk-result.html', {
                "process_description": "Coding Assignment Creation Result",
                "log": "\n".join(log_lines),
                "status": "Coding assignments created"
                    if was_successful
                    else "Coding assignment creation failed. "
                    "No changes made to database.",
                "was_successful": was_successful,
                })
    else:
        form = AssignToCodersForm()

    return render(request, 'generic-form.html', {
        "form": form,
        "form_description": "Assign work to coders",
    })

# }}}

# vim: foldmethod=marker
