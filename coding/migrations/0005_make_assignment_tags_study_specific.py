# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import coding.models


class Migration(migrations.Migration):

    dependencies = [
        ('coding', '0004_make_datetime_default_tz_aware'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignmenttag',
            name='study',
            field=models.ForeignKey(to='pieces.Study', default=coding.models.grab_some_study, to_field='id'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='codingassignment',
            name='tags',
            field=models.ManyToManyField(to='coding.AssignmentTag', verbose_name=b'assignment tag'),
        ),
        migrations.AlterField(
            model_name='assignmenttag',
            name='name',
            field=models.CharField(help_text=b'Recommended format is lower-case-with-hyphens. Do not use spaces.', unique=True, max_length=100),
        ),
    ]
