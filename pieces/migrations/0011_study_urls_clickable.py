# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pieces', '0010_auto_20141123_1239'),
    ]

    operations = [
        migrations.AddField(
            model_name='study',
            name='urls_clickable',
            field=models.BooleanField(default=False),
        ),
    ]
