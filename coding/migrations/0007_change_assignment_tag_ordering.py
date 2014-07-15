# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coding', '0006_fix_assignment_tag_uniqueness'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='assignmenttag',
            options={'ordering': (b'study', b'name')},
        ),
    ]
