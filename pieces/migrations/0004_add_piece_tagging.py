# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('pieces', '0003_piece_studies'),
    ]

    operations = [
        migrations.CreateModel(
            name='PieceTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('create_date', models.DateTimeField(default=datetime.datetime.now)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='piece',
            name='tags',
            field=models.ManyToManyField(to='pieces.PieceTag'),
            preserve_default=True,
        ),
    ]
