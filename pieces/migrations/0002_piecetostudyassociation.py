# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pieces', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PieceToStudyAssociation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('study', models.ForeignKey(to='pieces.Study', to_field='id')),
                ('piece', models.ForeignKey(to='pieces.Piece', to_field='id')),
                ('create_date', models.DateTimeField(default=datetime.datetime.now)),
                ('creator', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field='id')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
