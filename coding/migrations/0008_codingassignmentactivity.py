# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('coding', '0007_change_assignment_tag_ordering'),
    ]

    operations = [
        migrations.CreateModel(
            name='CodingAssignmentActivity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action_time', models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ('action', models.CharField(max_length=10, choices=[(b'view', b'View'), (b'modify', b'Modify')])),
                ('state', models.CharField(max_length=10, choices=[(b'NS', b'Not started'), (b'ST', b'Started'), (b'FI', b'Finished')])),
                ('actor', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('assignment', models.ForeignKey(to='coding.CodingAssignment', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': (b'action_time',),
                'verbose_name_plural': b'coding assignment activities',
            },
            bases=(models.Model,),
        ),
    ]
