# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pieces', '0006_make_datetime_default_tz_aware'),
    ]

    operations = [
        migrations.AlterField(
            model_name='piece',
            name='tags',
            field=models.ManyToManyField(to='pieces.PieceTag', verbose_name=b'piece tag'),
        ),
    ]
