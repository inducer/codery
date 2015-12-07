# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import coding.models


class Migration(migrations.Migration):

    dependencies = [
        ('coding', '0009_change_coding_activity_ordering'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignmenttag',
            name='study',
            field=models.ForeignKey(related_name='assignment_tags', default=coding.models.grab_some_study, to='pieces.Study', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='codingassignment',
            name='coder',
            field=models.ForeignKey(related_name='coding_assignments', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='codingassignment',
            name='piece',
            field=models.ForeignKey(related_name='coding_assignments', to='pieces.Piece', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='codingassignment',
            name='tags',
            field=models.ManyToManyField(related_name='assignments', verbose_name=b'assignment tag', to='coding.AssignmentTag'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='codingassignmentactivity',
            name='assignment',
            field=models.ForeignKey(related_name='activities', to='coding.CodingAssignment', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sample',
            name='pieces',
            field=models.ManyToManyField(related_name='samples', to='pieces.Piece'),
            preserve_default=True,
        ),
    ]
