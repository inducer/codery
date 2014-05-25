from django.shortcuts import render
import re
import sys

import django.forms as forms
from django.http import HttpResponseForbidden

from django.contrib.auth.models import User

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

#import sys
from pieces.models import PieceTag, Keyword, Study, PieceToStudyAssociation
from coding.models import (
        Sample, CodingAssignment, assignment_states, STATE_CHOICES,
        AssignmentTag)


from django.contrib.auth.decorators import (
        login_required,
        permission_required)

from django.db import transaction


# {{{ sample creation

class CreateSampleForm(forms.Form):
    study = forms.ModelChoiceField(
            queryset=Study.objects, required=True)
    tags = forms.ModelMultipleChoiceField(
            queryset=PieceTag.objects,
            required=False,
            help_text="Select piece tags (if any) which will constrain the "
            "set of pieces being sampled. Each piece is required to have "
            "all selected tags.")
    month = forms.IntegerField(required=False)
    year = forms.IntegerField(required=False)
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


@transaction.atomic
def create_sample_backend(study, tags, name, sample_size, create_date,
        year, month, creator, log_lines):
    queryset = PieceToStudyAssociation.objects.filter(study=study)
    if year is not None:
        queryset = queryset.filter(piece__pub_date__year=year)
    if month is not None:
        queryset = queryset.filter(piece__pub_date__month=month)

    tag_id_set = set(tag.id for tag in tags)

    pieces = [pts.piece for pts in queryset.prefetch_related('piece__tags')
            if tag_id_set <= set(tag.id for tag in pts.piece.tags.all())]

    if sample_size > len(pieces):
        raise RuntimeError("not enough pieces for sample")

    log_lines.append("%d pieces in urn" % len(pieces))

    from random import sample
    selected = sample(pieces, sample_size)

    log_lines.append("%d pieces sampled" % len(selected))

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

            from django.utils.timezone import now
            create_sample_backend(
                    study=form.cleaned_data["study"],
                    tags=form.cleaned_data["tags"],
                    name=form.cleaned_data["name"],
                    sample_size=form.cleaned_data["sample_size"],
                    month=form.cleaned_data["month"],
                    year=form.cleaned_data["year"],
                    create_date=now(),
                    creator=request.user,
                    log_lines=log_lines)

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
    limit_to_unassigned = forms.BooleanField(required=False)
    shuffle_pieces_before_assigning = forms.BooleanField(required=False)
    assign_each_piece_n_times = forms.IntegerField(required=True, initial=1)
    max_assignments_per_piece = forms.IntegerField(required=False)
    coders = forms.ModelMultipleChoiceField(User.objects, required=True)
    max_pieces_per_coder = forms.IntegerField(required=False,
            help_text="(does not count previously assigned pieces)")

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-2"
        self.helper.field_class = "col-lg-8"

        self.helper.add_input(
                Submit("submit", "Submit", css_class="col-lg-offset-2"))
        super(AssignToCodersForm, self).__init__(*args, **kwargs)


def trim_docstring(docstring):
    # from http://legacy.python.org/dev/peps/pep-0257/
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxint
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxint:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)


@transaction.atomic
def assign_to_coders_backend(sample,
        limit_to_unassigned,
        shuffle_pieces_before_assigning,
        assign_each_piece_n_times,
        max_assignments_per_piece,
        coders, max_pieces_per_coder,
        creation_time, creator):
    """Assignment to coders currently uses the following algorithm:

    #. Get a list of all pieces in the sample.
    #. If "shuffle pieces before assigning" is checked, shuffle the list of pieces
    #. Make a numbering of "target coders" for this assignment, determine a
       coder whose "turn" it is.
    #. For each piece in the list of pieces, do the following:

       #. If "limit to unassigned" is checked, and the piece is assigned to
          someone, continue to the next piece.
       #. Find how often this piece has already been assigned as
          ``n_piece_assignments``.
       #. Determine number of new assignments *n* for this piece as::

              n = min(
                  max_assignments_per_piece-n_piece_assignments,
                  assign_each_piece_n_times))

       #. Do the following *n* times:

          #. Try to assign the piece to the coder whose 'turn' it is.
          #. If that coder already has this article assigned, go
             round-robin among coders until someone does not have the article
             assigned to them.
          #. If no-one is found, skip this piece.
          #. Advance the "turn", taking into account ``pieces_per_coder``.
             If all coders have reached their ``pieces_per_coder`` (in this
             assignment round), stop.
    """
    log_lines = []

    coder_idx_to_count = {}

    num_coders = len(coders)

    pieces = sample.pieces.all()
    if shuffle_pieces_before_assigning:
        pieces = list(pieces)
        from random import shuffle
        shuffle(pieces)

    quit_flag = False

    coder_idx = 0
    for piece in pieces:
        piece_identifier = "'%d: %s'" % (piece.id, unicode(piece)[:20])
        n_piece_assignments = CodingAssignment.objects.filter(
                sample=sample, piece=piece).count()
        if (limit_to_unassigned and n_piece_assignments):
            log_lines.append("%s already assigned to someone, skipping."
                    % piece_identifier)
            continue

        assign_times = assign_each_piece_n_times

        if max_assignments_per_piece is not None:
            max_assign_times = assign_times = max(
                    0,
                    max_assignments_per_piece
                    - n_piece_assignments)

            assign_times = min(
                    max_assign_times,
                    assign_times)

        if assign_times == 0:
            log_lines.append("Piece '%s' has reached max assignment count, skipping."
                    % piece_identifier)
            continue

        for i_assignment in xrange(assign_times):

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
                log_lines.append("Piece '%s' already assigned "
                        "to all coders, skipping." % piece_identifier)
                break

            assmt = CodingAssignment()
            assmt.coder = coders[local_coder_idx]
            assmt.piece = piece
            assmt.sample = sample
            assmt.state = assignment_states.not_started
            assmt.latest_state_time = creation_time
            assmt.creation_time = creation_time
            assmt.creator = creator
            assmt.save()

            coder_idx_to_count[local_coder_idx] = \
                    coder_idx_to_count.get(local_coder_idx, 0) + 1

            # {{{ advance coder turn

            find_coder_tries = 0
            while find_coder_tries < num_coders:
                coder_idx = (coder_idx + 1) % num_coders
                if (
                        max_pieces_per_coder is None
                        or coder_idx_to_count.get(coder_idx, 0)
                        < max_pieces_per_coder):
                    break
                find_coder_tries += 1

            if find_coder_tries >= num_coders:
                log_lines.append("All coders have reached their item limit, "
                        "stopping.")
                quit_flag = True
                break

            # }}}

        if quit_flag:
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

            from django.utils.timezone import now
            log_lines = assign_to_coders_backend(
                    form.cleaned_data["sample"],
                    limit_to_unassigned=
                    form.cleaned_data["limit_to_unassigned"],
                    shuffle_pieces_before_assigning=
                    form.cleaned_data["shuffle_pieces_before_assigning"],
                    assign_each_piece_n_times=
                    form.cleaned_data["assign_each_piece_n_times"],
                    max_assignments_per_piece=
                    form.cleaned_data["max_assignments_per_piece"],
                    coders=form.cleaned_data["coders"],
                    max_pieces_per_coder=form.cleaned_data["max_pieces_per_coder"],
                    creation_time=now(),
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

    from docutils.core import publish_string
    return render(request, 'generic-form.html', {
        "doc": publish_string(
            trim_docstring(assign_to_coders_backend.__doc__),
            writer_name="html"),
        "form": form,
        "form_description": "Assign work to coders",
    })

# }}}


# {{{ view assignments

@login_required
def view_assignments(request):
    started = (
            CodingAssignment.objects
            .filter(state=assignment_states.started, coder=request.user)
            .order_by('sample', 'piece__title')
            )
    not_started = (
            CodingAssignment.objects
            .filter(state=assignment_states.not_started, coder=request.user)
            .order_by('sample', 'piece__title')
            )
    finished = (
            CodingAssignment.objects
            .filter(state=assignment_states.finished, coder=request.user)
            .order_by('sample', 'piece__title')
            )

    return render(request, 'coding/assignments.html', {
        "started": started,
        "not_started": not_started,
        "finished": finished,
        "nothing_here": not (started or not_started or finished),
    })

# }}}


# {{{ view assignment

class AssignmentUpdateForm(forms.Form):
    state = forms.ChoiceField(choices=STATE_CHOICES)

    tags = forms.ModelMultipleChoiceField(
            queryset=AssignmentTag.objects,
            required=False,
            help_text="Select tags (if any) to apply to this "
            "coding assignment.")
    latest_coding_form_url = forms.URLField(required=False,
            help_text="This field is intended to hold the "
            "'resume filling out this form' link that UIUC FormBuilder "
            "likes to email around. If you fill out this field, this URL "
            "will be available as a clickable link above when you come back.")
    notes = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-2"
        self.helper.field_class = "col-lg-8"

        self.helper.add_input(
                Submit("submit", "Update", css_class="col-lg-offset-2"))
        super(AssignmentUpdateForm, self).__init__(*args, **kwargs)


class Highlighter:
    def __init__(self, study):
        self.study = study

    def __call__(self, text):
        def add_highight(t):
            return '<span style="color:%s; font-weight:bold;">%s</span>' \
                    % (kw.color, t.group(0))

        for kw in Keyword.objects.filter(study=self.study):
            kwre = re.compile(kw.get_re(), re.IGNORECASE)
            text, _ = kwre.subn(add_highight, text)

        return text


@login_required
def view_assignment(request, id):
    assignment = CodingAssignment.objects.get(id=id)

    if assignment.coder != request.user:
        return HttpResponseForbidden(
                "Not your assignment.", content_type="text/plain")

    if request.method == "POST":
        form = AssignmentUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            assignment.latest_coding_form_url = \
                    form.cleaned_data["latest_coding_form_url"]
            assignment.state = \
                    form.cleaned_data["state"]
            assignment.tags = \
                    form.cleaned_data["tags"]
            assignment.notes = \
                    form.cleaned_data["notes"]
            from django.utils.timezone import now
            assignment.latest_state_time = now()
            assignment.save()
    else:
        form = AssignmentUpdateForm({
            "state": assignment.state,
            "tags": assignment.tags.all(),
            "latest_coding_form_url": assignment.latest_coding_form_url,
            "notes": assignment.notes,
            })

    piece = assignment.piece
    paragraphs = piece.content.split("\n")

    highlighter = Highlighter(assignment.sample.study)

    content = "\n".join(
            "<p>%s</p>" % highlighter(paragraph)
            for paragraph in paragraphs)

    return render(request, 'coding/assignment.html', {
        "assignment": assignment,
        "piece": assignment.piece,
        "content": content,
        "form": form,
    })

# }}}

# vim: foldmethod=marker
