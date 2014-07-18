from django.db import models

from django.contrib.auth.models import User
from pieces.models import Study, Piece
from django.utils.timezone import now


class Sample(models.Model):
    study = models.ForeignKey(Study)
    name = models.CharField(max_length=200)

    notes = models.TextField(null=True, blank=True)

    create_date = models.DateTimeField(default=now)
    creator = models.ForeignKey(User)

    pieces = models.ManyToManyField(Piece)

    def __unicode__(self):
        return u"%s (%d pieces, %s)" % (self.name, self.pieces.count(), self.study)

    class Meta:
        permissions = (
                ("create_sample", "Can create sample"),
                )


class assignment_states:
    not_started = "NS"
    started = "ST"
    finished = "FI"


STATE_CHOICES = (
        (assignment_states.not_started, "Not started"),
        (assignment_states.started, "Started"),
        (assignment_states.finished, "Finished"),
        )


def grab_some_study():
    for s in Study.objects.all():
        return s.id

    # no study
    return None


class AssignmentTag(models.Model):
    name = models.CharField(max_length=100,
            help_text="Recommended format is lower-case-with-hyphens. "
            "Do not use spaces.")
    create_date = models.DateTimeField(default=now)
    study = models.ForeignKey(
            Study, null=False,
            default=grab_some_study)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.study.name)

    class Meta:
        unique_together = (("name", "study"),)
        ordering = ('study', 'name')


class CodingAssignment(models.Model):
    coder = models.ForeignKey(User, related_name="coding_assignments")
    piece = models.ForeignKey(Piece)
    sample = models.ForeignKey(Sample)

    results = models.TextField(null=True, blank=True)

    notes = models.TextField(null=True, blank=True)

    state = models.CharField(max_length=10,
            choices=STATE_CHOICES)
    latest_state_time = models.DateTimeField(default=now)

    latest_coding_form_url = models.URLField(null=True, blank=True)

    creation_time = models.DateTimeField(default=now)
    creator = models.ForeignKey(User)

    tags = models.ManyToManyField(AssignmentTag,
            verbose_name="assignment tag")

    def get_absolute_url(self):
        return "/coding/assignment/%d/" % self.id

    def __unicode__(self):
        return u"%s -> %s (%s)" % (self.piece, self.coder, self.sample.name)

    class Meta:
        permissions = (
                ("assign_to_coders", "Can assign work to coders"),
                )


# {{{ assignment activity tracking

class assignment_actions:
    view = "view"
    modify = "modify"

ACTION_CHOICES = (
        (assignment_actions.view, "View"),
        (assignment_actions.modify, "Modify"),
        )


class CodingAssignmentActivity(models.Model):
    assignment = models.ForeignKey(CodingAssignment, related_name="activities")

    action_time = models.DateTimeField(default=now, db_index=True)
    actor = models.ForeignKey(User, db_index=True)

    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    state = models.CharField(max_length=10,
            choices=STATE_CHOICES)

    class Meta:
        verbose_name_plural = "coding assignment activities"
        ordering = ("-action_time",)

# }}}
