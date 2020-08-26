# -*- coding: utf8 -*-

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import datetime
from wikipendium.wiki.langcodes import LANGUAGE_NAMES
from markdown import Markdown
from markdown.extensions.toc import TocExtension
from .markdown_extra.markdown_wikitables import WikiTableExtension
from .markdown_extra.nofollow import NofollowExtension
from .markdown_extra.marginnotes import MarginNotesExtension
from wikipendium.cache.decorators import cache_model_method
from re import sub
from taggit.managers import TaggableManager


class Article(models.Model):
    tags = TaggableManager()
    slug = models.SlugField(max_length=256, unique=True)
    slug_regex = ur'A-Za-z0-9æøåÆØÅ\-'

    @staticmethod
    def get_all_contents(time_from, time_to):
        return ArticleContent.objects.filter(updated__gte=time_to - time_from)

    @staticmethod
    def get_all_article_content():
        articles = Article.objects.all()

        all_newest_in_all_languages = [
            [a.get_newest_content(lang)
                for lang in a.get_available_language_codes()]
            for a in articles]

        return all_newest_in_all_languages

    @staticmethod
    def get_all_newest_contents():
        all_newest_in_all_languages = Article.get_all_article_content()

        all_newest_reduced_to_one_ac_per_article_regardless_of_language = map(
            lambda x: sorted(x, key=lambda ac: ac.updated)[-1],
            filter(lambda x: x, all_newest_in_all_languages))

        alphabetically_sorted = sorted(
            all_newest_reduced_to_one_ac_per_article_regardless_of_language,
            key=lambda ac: ac.article.slug)
        return alphabetically_sorted

    @staticmethod
    def get_all_newest_contents_all_languages():
        all_newest_in_all_languages = Article.get_all_article_content()

        flattened_list = [article
                          for sublist in all_newest_in_all_languages
                          for article in sublist]
        sorted_by_last_updated = sorted(flattened_list,
                                        key=lambda ac: ac.updated,
                                        reverse=True)

        return sorted_by_last_updated

    def __unicode__(self):
        return self.slug

    def save(self, *args, **kwargs):
        self.slug = self.slug.upper().strip()
        self.clean()
        super(Article, self).save(*args, **kwargs)

    def clean(self):
        if '/' in self.slug:
            raise ValidationError('Course code cannot contain slashes')

    def get_contributors(self, lang='en'):
        filtered = ArticleContent.objects.filter(article=self, lang=lang)
        return set([ac.edited_by for ac in filtered])

    def get_newest_content(self, lang='en'):
        return ArticleContent.objects.filter(
            article=self, lang=lang
        ).order_by('-updated').select_related('article', 'edited_by').first()

    def get_sorted_contents(self, lang='en'):
        return ArticleContent.objects.filter(
            article=self, lang=lang
        ).order_by('-updated').select_related('article', 'edited_by')

    def get_available_language_codes(self):
        codes = ArticleContent.objects.filter(
            article=self
        ).distinct().values_list('lang', flat=True)
        return list(codes)

    def get_available_languages(self, current=None):
        codes = self.get_available_language_codes()
        if current and current.lang is not None and current.lang in codes:
            codes.remove(current.lang)
        if codes:
            return zip(map(lambda key: LANGUAGE_NAMES[key], codes),
                       map(self.get_newest_content, codes))

    def get_absolute_url(self, lang='en'):
        newest_content = self.get_newest_content(lang)
        if newest_content is not None:
            return newest_content.get_absolute_url()
        return '/' + self.slug + '/' + lang + '/edit/'

    def get_slug(self):
        return self.slug.upper()


class ArticleContent(models.Model):
    article = models.ForeignKey('Article')
    content = models.TextField()
    title = models.CharField(max_length=1024)
    lang = models.CharField(max_length=2, default='en')
    updated = models.DateTimeField()
    edited_by = models.ForeignKey(User, blank=True,
                                  null=True, on_delete=models.SET_NULL)
    parent = models.ForeignKey('ArticleContent', related_name='parent_ac',
                               null=True, blank=True,
                               on_delete=models.SET_NULL)
    child = models.ForeignKey('ArticleContent', related_name='child_ac',
                              null=True, blank=True, on_delete=models.SET_NULL)

    def clean(self):
        if '/' in self.title:
            raise ValidationError('Title cannot contain slashes')

    def get_contributors(self):
        filtered = ArticleContent.objects.filter(
            article=self.article,
            lang=self.lang,
            updated__lte=self.updated
        ).select_related('edited_by')
        return set([ac.edited_by for ac in filtered])

    def get_full_title(self):
        return self.article.slug + ': ' + self.title

    def get_last_descendant(self):
        return self.article.get_newest_content(lang=self.lang)

    def get_absolute_url(self):
        lang = ''
        if self.lang != 'en':
            lang = '/' + self.lang + '/'
        return ('/' +
                self.article.slug + '_' +
                sub('[^'+Article.slug_regex+'_]', '',
                    self.title.replace(' ', '_')) +
                lang
                )

    def get_edit_url(self):
        return (self.get_absolute_url() + '/edit/').replace('//', '/')

    def get_add_language_url(self):
        return '/' + self.article.slug + '/add_language/'

    def get_history_url(self):
        return (self.get_absolute_url() + '/history/').replace('//', '/')

    def get_history_single_url(self):
        return self.get_history_url() + str(self.pk)+'/'

    @cache_model_method
    def get_html_content(self):
        wikitables = WikiTableExtension()
        nofollow = NofollowExtension()
        margin_notes = MarginNotesExtension()
        toc = TocExtension([('title', 'Table of Contents')])

        md = Markdown(
            extensions=[
                toc,
                'outline',
                'mathjax',
                wikitables,
                nofollow,
                'def_list',
                margin_notes,
            ],
            output_format='html5',
            safe_mode='escape'
        )
        markdowned_text = md.convert(self.content)
        article = {
            'html': markdowned_text,
            'toc': getattr(md, 'toc', None),
        }
        return article

    def save(self, change_updated_time=True, *args, **kwargs):
        if change_updated_time:
            self.updated = datetime.datetime.now()
        self.clean()
        super(ArticleContent, self).save(*args, **kwargs)

    def __unicode__(self):
        return '[' + str(self.pk) + '] ' + self.title
