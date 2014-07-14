# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pieces', '0007_add_verbose_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='piecetag',
            name='shown_to_coders',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
