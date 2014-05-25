# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pieces', '0002_piecetostudyassociation'),
    ]

    operations = [
        migrations.AddField(
            model_name='piece',
            name='studies',
            field=models.ManyToManyField(to='pieces.Study', through='pieces.PieceToStudyAssociation'),
            preserve_default=True,
        ),
    ]
