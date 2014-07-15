# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pieces', '0008_piecetag_shown_to_coders'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='venue',
            options={'ordering': [b'name']},
        ),
        migrations.AddField(
            model_name='piece',
            name='publication_type',
            field=models.CharField(max_length=200, null=True),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='venue',
            name='publication_type',
        ),
    ]
