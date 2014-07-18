# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coding', '0008_codingassignmentactivity'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='codingassignmentactivity',
            options={'ordering': (b'-action_time',), 'verbose_name_plural': b'coding assignment activities'},
        ),
    ]
