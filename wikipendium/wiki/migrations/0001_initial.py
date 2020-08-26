# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(unique=True, max_length=256)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ArticleContent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField()),
                ('title', models.CharField(max_length=1024)),
                ('lang', models.CharField(default=b'en', max_length=2)),
                ('updated', models.DateTimeField()),
                ('article', models.ForeignKey(to='wikipendium__wiki.Article')),
                ('child', models.ForeignKey(related_name='child_ac', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='wikipendium__wiki.ArticleContent', null=True)),
                ('edited_by', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('parent', models.ForeignKey(related_name='parent_ac', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='wikipendium__wiki.ArticleContent', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
