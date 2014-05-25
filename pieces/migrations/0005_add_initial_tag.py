# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations  # noqa


def add_initial_tag(apps, schema_editor):
    # We can't import the PieceTag model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    PieceTag = apps.get_model("pieces", "PieceTag")
    Piece = apps.get_model("pieces", "Piece")

    initial_tag = PieceTag()
    initial_tag.name = "created-before-tagging"
    initial_tag.save()

    for piece in Piece.objects.all():
        piece.tags = [initial_tag]
        piece.save()


class Migration(migrations.Migration):
    dependencies = [
        ('pieces', '0004_add_piece_tagging'),
    ]

    operations = [
            migrations.RunPython(add_initial_tag),
    ]
