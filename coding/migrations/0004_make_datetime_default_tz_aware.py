# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('coding', '0003_add_assignment_tagging'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignmenttag',
            name='create_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='codingassignment',
            name='latest_state_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='codingassignment',
            name='creation_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='sample',
            name='create_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
