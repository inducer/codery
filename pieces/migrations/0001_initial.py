# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Venue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('publication_type', models.CharField(max_length=200, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Study',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('start_date', models.DateField(null=True, blank=True)),
                ('end_date', models.DateField(null=True, blank=True)),
                ('coding_tool_url', models.URLField(null=True, blank=True)),
            ],
            options={
                'verbose_name_plural': b'studies',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Keyword',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('study', models.ForeignKey(to='pieces.Study', to_field='id')),
                ('rule', models.CharField(help_text=b"The 'Substring' rule matches any occurrence of the pattern anywhere. For example, 'flu' would match 'influence'.\nThe 'Word' rule matches only entire words.\nThe 'Word wildcard' rule matches entire words against a pattern with * (any number of characters, including zero) and ? (single character) wildcards. For example, '*at' would match 'cat' and 'brat', but not 'dedication'.\nRegular expressions allow very general matching. Search the Internt for 'python re' to learn more.", max_length=20, choices=[(b'sub', b'Substring'), (b'word', b'Word'), (b'word_wildcard', b'Word with wildcards'), (b'regex', b'Regular expression')])),
                ('pattern', models.CharField(max_length=1000)),
                ('color', models.CharField(max_length=50, choices=[(b'red', b'Red'), (b'green', b'Green'), (b'blue', b'Blue'), (b'cyan', b'Cyan'), (b'magenta', b'Magenta'), (b'black', b'Black')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Piece',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=1000, blank=True)),
                ('content', models.TextField(blank=True)),
                ('notes', models.TextField(null=True, blank=True)),
                ('venue', models.ForeignKey(to='pieces.Venue', to_field='id')),
                ('pub_date', models.DateField(null=True, blank=True)),
                ('pub_date_unparsed', models.CharField(max_length=1000, null=True, blank=True)),
                ('source_load_date', models.DateField(null=True, blank=True)),
                ('byline', models.CharField(max_length=1000, null=True, blank=True)),
                ('url', models.URLField(null=True, blank=True)),
                ('create_date', models.DateTimeField(default=datetime.datetime.now)),
                ('creator', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field='id')),
                ('extra_data_json', models.TextField(null=True, blank=True)),
            ],
            options={
                'ordering': [b'-pub_date', b'title'],
                'permissions': ((b'bulk_import', b'Can import pieces in bulk'),),
            },
            bases=(models.Model,),
        ),
    ]
