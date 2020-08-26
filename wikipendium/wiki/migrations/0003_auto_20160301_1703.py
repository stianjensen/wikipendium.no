# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def uppercase_all_article_slugs(apps, schema_editor):
    Article = apps.get_model("wikipendium__wiki", "Article")
    articles = Article.objects.all()
    for article in articles:
        if article.slug:
            article.slug = article.slug.upper()
            article.save()


class Migration(migrations.Migration):

    dependencies = [
        ('wikipendium__wiki', '0002_article_tags'),
    ]

    operations = [
        migrations.RunPython(uppercase_all_article_slugs),
    ]
