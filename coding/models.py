from django.db import models

from django.contrib.auth.models import User
from pieces.models import Study, Piece
from datetime import datetime


class Sample(models.Model):
    study = models.ForeignKey(Study)
    name = models.CharField(max_length=200)

    notes = models.TextField(null=True, blank=True)

    create_date = models.DateTimeField(default=datetime.now)
    creator = models.ForeignKey(User)

    pieces = models.ManyToManyField(Piece)


class CodingAssignment(models.Model):
    coder = models.ForeignKey(User)
    piece = models.ForeignKey(Piece)

    state = models.CharField(max_length=10,
            choices=[
                ("NS", "Not started"),
                ("ST", "Started"),
                ("FI", "Finished"),
                ])

    results = models.TextField(null=True, blank=True)

    notes = models.TextField(null=True, blank=True)

    latest_coding_form_url = models.URLField(null=True, blank=True)

    create_date = models.DateTimeField(default=datetime.now)
    creator = models.ForeignKey(User)

