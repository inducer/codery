# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coding', '0005_make_assignment_tags_study_specific'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignmenttag',
            name='name',
            field=models.CharField(help_text=b'Recommended format is lower-case-with-hyphens. Do not use spaces.', max_length=100),
        ),
        migrations.AlterUniqueTogether(
            name='assignmenttag',
            unique_together=set([(b'name', b'study')]),
        ),
    ]
