# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pieces', '0009_move_publication_type_to_piece'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='piecetag',
            options={'permissions': (('tag_by_search', 'Can assign piece tags to search result'), ('may_see_non_coder_tags', 'May see non-coder tags'))},
        ),
    ]
