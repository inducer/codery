# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('coding', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pieces', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='CodingAssignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('coder', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field='id')),
                ('piece', models.ForeignKey(to='pieces.Piece', to_field='id')),
                ('sample', models.ForeignKey(to='coding.Sample', to_field='id')),
                ('results', models.TextField(null=True, blank=True)),
                ('notes', models.TextField(null=True, blank=True)),
                ('state', models.CharField(max_length=10, choices=[(b'NS', b'Not started'), (b'ST', b'Started'), (b'FI', b'Finished')])),
                ('latest_state_time', models.DateTimeField(default=datetime.datetime.now)),
                ('latest_coding_form_url', models.URLField(null=True, blank=True)),
                ('creation_time', models.DateTimeField(default=datetime.datetime.now)),
                ('creator', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field='id')),
            ],
            options={
                'permissions': ((b'assign_to_coders', b'Can assign work to coders'),),
            },
            bases=(models.Model,),
        ),
    ]
