# -*- coding: utf-8 -*-

from django.test import TestCase
from wikipendium.wiki.models import Article, ArticleContent, User
from wikipendium.wiki.forms import NewArticleForm
from django.core.exceptions import ValidationError
import datetime


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)


class ArticleTest(TestCase):

    def setUp(self):
        self.u1 = User(username='u1')
        self.u2 = User(username='u2')
        self.u1.save()
        self.u2.save()
        self.article1 = Article(slug=u'TDT4100')
        self.article1.save()
        self.article2 = Article(slug=u'TIØ4258')
        self.article2.save()
        self.ac1 = ArticleContent(article=self.article1,
                                  updated=datetime.datetime(2012, 1, 1))
        self.ac2 = ArticleContent(article=self.article1,
                                  updated=datetime.datetime(2013, 1, 1),
                                  title='per')
        self.ac3 = ArticleContent(article=self.article2,
                                  updated=datetime.datetime(2001, 3, 7))
        self.ac4 = ArticleContent(article=self.article2,
                                  updated=datetime.datetime(2001, 3, 8),
                                  lang='nb')
        self.ac1.edited_by = self.u1
        self.ac2.edited_by = self.u2
        self.ac3.edited_by = self.u1
        self.ac4.edited_by = self.u2
        self.ac1.save()
        self.ac2.save()
        self.ac3.save()
        self.ac4.save()

    def test_slug_should_uppercase_when_saved(self):
        article = Article()
        article.slug = u'lowercase'
        article.save()
        self.assertEqual(article.slug, u'LOWERCASE')

    def test_slug_should_strip_whitespace_when_saved(self):
        article = Article()
        article.slug = u'   PADDED\v\t \n'
        article.save()
        self.assertEqual(article.slug, u'PADDED')

    def test_slug_cannot_contain_slashes(self):
        article = Article()
        article.slug = u'TDT/4100'
        try:
            article.save()
            self.assertEqual(1, 2)  # this should not be reached
        except ValidationError:
            self.assertEqual(1, 1)  # correct error was raised

    def test_get_contributors(self):
        self.assertEquals(self.article1.get_contributors(),
                          set([self.u1, self.u2]))

    def test_get_newest_content(self):
        self.assertEquals(self.article1.get_newest_content(), self.ac2)

    def test_get_available_languages(self):
        self.assertEquals(self.article1.get_available_languages(),
                          [('English', self.ac2)])
        result = self.article2.get_available_languages()
        expected_result = [('English', self.ac3),
                           ('Norwegian', self.ac4)]
        self.assertEquals(expected_result, result)

    def test_get_absolute_url(self):
        self.assertEquals(self.article1.get_absolute_url(), '/TDT4100_per')

    def test_get_all_article_content(self):
        result = Article.get_all_article_content()
        expected_result = [[self.ac2], [self.ac3, self.ac4]]
        self.assertEquals(expected_result, result)

    def test_get_all_newest_contents(self):
        result = Article.get_all_newest_contents()
        expected_result = [self.ac2, self.ac4]
        self.assertEquals(expected_result, result)

    def test_get_all_newest_contents_all_languages(self):
        result = Article.get_all_newest_contents_all_languages()
        expected_result = [self.ac4, self.ac3, self.ac2]
        self.assertEquals(expected_result, result)

    def test___unicode__(self):
        self.assertEquals(u'TIØ4258', unicode(self.article2))
        self.assertEquals(unicode, type(unicode(self.article2)))

    def test_get_sorted_contents(self):
        result = list(self.article1.get_sorted_contents())
        expected_result = [self.ac2, self.ac1]
        self.assertEquals(expected_result, result)

        result = list(self.article2.get_sorted_contents())
        expected_result = [self.ac3]
        self.assertEquals(expected_result, result)

        result = list(self.article2.get_sorted_contents(lang='nb'))
        expected_result = [self.ac4]
        self.assertEquals(expected_result, result)

    def test_get_available_language_codes(self):
        result = self.article2.get_available_language_codes()
        expected_result = ['en', 'nb']
        self.assertEquals(expected_result, result)

    def test_get_slug(self):
        self.assertEquals(u'TIØ4258', self.article2.get_slug())


class ArticleContentTest(TestCase):

    def setUp(self):
        self.article1 = Article(slug=u'TDT4100')
        self.article1.save()
        self.ac1 = ArticleContent(article=self.article1,
                                  updated=datetime.datetime(2012, 1, 1),
                                  title='Cooking and baking',
                                  lang='fr',
                                  content='# Title')
        self.ac2 = ArticleContent(article=self.article1,
                                  updated=datetime.datetime(2014, 1, 1),
                                  title='Cooking and baking',
                                  lang='fr')
        self.ac1.save()
        self.ac2.save()

    def test_title_cannot_contain_slashes(self):
        ac = ArticleContent()
        ac.title = 'asdf/sdfi'
        ac.article = self.article1
        with self.assertRaises(ValidationError):
            ac.save()

    def test_get_full_title(self):
        self.assertEquals('TDT4100: Cooking and baking',
                          self.ac1.get_full_title())

    def test_get_last_descendant(self):
        self.assertEquals(self.ac2,
                          self.ac1.get_last_descendant())

    def test_get_absolute_url(self):
        self.assertEquals('/TDT4100_Cooking_and_baking/fr/',
                          self.ac1.get_absolute_url())

    def test_get_edit_url(self):
        self.assertEquals('/TDT4100_Cooking_and_baking/fr/edit/',
                          self.ac1.get_edit_url())

    def test_get_add_language_url(self):
        self.assertEquals('/TDT4100/add_language/',
                          self.ac1.get_add_language_url())

    def test_get_history_url(self):
        self.assertEquals('/TDT4100_Cooking_and_baking/fr/history/',
                          self.ac1.get_history_url())

    def test_get_history_single_url(self):
        self.assertEquals('/TDT4100_Cooking_and_baking/fr/history/%s/' % (
                          self.ac1.pk), self.ac1.get_history_single_url())

    def test_get_html_content(self):
        self.assertTrue('<h1>' in self.ac1.get_html_content()['html'])

    def test___unicode__(self):
        self.assertEquals(u'[1] Cooking and baking',
                          unicode(self.ac1))

    def test_line_endings(self):
        form = NewArticleForm({
            'slug': u'lineendings',
            'title': u'New article',
            'lang': u'en',
            'content': u'Test\r\nnext line.',
        })
        self.assertTrue(form.is_valid())
        ac = form.save(commit=False)
        self.assertEquals(u'Test\nnext line.',
                          ac.content)
