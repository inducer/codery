# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('pieces', '0005_add_initial_tag'),
    ]

    operations = [
        migrations.AlterField(
            model_name='piecetostudyassociation',
            name='create_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='piecetag',
            name='name',
            field=models.CharField(help_text=b'Recommended format is lower-case-with-hyphens. Do not use spaces.', unique=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='piece',
            name='create_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='piecetag',
            name='create_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
