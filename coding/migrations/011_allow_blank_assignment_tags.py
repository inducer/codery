# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coding', '0010_auto_20141123_1239'),
    ]

    operations = [
        migrations.AlterField(
            model_name='codingassignment',
            name='tags',
            field=models.ManyToManyField(related_name='assignments', verbose_name=b'assignment tag', to='coding.AssignmentTag', blank=True),
            preserve_default=True,
        ),
    ]
