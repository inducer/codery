# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pieces', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sample',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('study', models.ForeignKey(to='pieces.Study', to_field='id', on_delete=models.CASCADE)),
                ('name', models.CharField(max_length=200)),
                ('notes', models.TextField(null=True, blank=True)),
                ('create_date', models.DateTimeField(default=datetime.datetime.now)),
                ('creator', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field='id', on_delete=models.CASCADE)),
                ('pieces', models.ManyToManyField(to='pieces.Piece')),
            ],
            options={
                'permissions': ((b'create_sample', b'Can create sample'),),
            },
            bases=(models.Model,),
        ),
    ]
