from django.forms import ModelForm, ValidationError
import django.forms as forms
from django.core.exceptions import ObjectDoesNotExist
from wikipendium.wiki.models import Article, ArticleContent
from wikipendium.wiki.merge3 import MergeError, merge
from wikipendium.wiki.langcodes import LANGUAGE_NAMES
from re import match


class ArticleForm(ModelForm):
    slug = forms.CharField(label='')
    language_list = sorted(LANGUAGE_NAMES.items(), key=lambda x: x[1])
    choices = [('', '')] + language_list
    lang = forms.ChoiceField(label='', choices=choices)
    title = forms.CharField(label='')
    content = forms.CharField(
        label='', widget=forms.Textarea(), required=False)

    class Meta:
        model = ArticleContent
        fields = ('lang', 'title', 'content')

    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)

        if hasattr(self.instance, 'article'):
            slug = self.instance.article.slug
            self.fields['slug'].widget.attrs['value'] = slug

        self.fields['slug'].widget.attrs['placeholder'] = 'Course code'
        self.fields['lang'].widget.attrs = {
            'class': 'select_chosen',
            'data-placeholder': 'Language'
        }

        self.fields['title'].widget.attrs['placeholder'] = 'Course title'
        self.fields.keyOrder = ['slug',
                                'lang',
                                'title',
                                'content',
                                ]

    def clean(self):
        super(ArticleForm, self).clean()
        self.cleaned_data['content'] = (self.cleaned_data.get('content', '')
                                        .replace('\r\n', '\n')
                                        .replace('\r', '\n'))
        return self.cleaned_data


class NewArticleForm(ArticleForm):
    def __init__(self, *args, **kwargs):
        super(NewArticleForm, self).__init__(*args, **kwargs)

    def clean_slug(self):
        if not match('^[' + Article.slug_regex + ']+$',
                     self.cleaned_data['slug']):
            raise ValidationError('Course codes must be alphanumeric.')
        try:
            Article.objects.get(slug=self.cleaned_data['slug'].upper())
            raise ValidationError('This course code is already in use.')
        except ObjectDoesNotExist:
            pass
        return self.cleaned_data['slug']


class AddLanguageArticleForm(ArticleForm):
    def __init__(self, article, *args, **kwargs):
        lang = kwargs.pop('lang') if 'lang' in kwargs else None

        super(AddLanguageArticleForm, self).__init__(*args, **kwargs)

        self.fields['slug'].widget.attrs['value'] = article.slug
        self.fields['slug'].widget.attrs['readonly'] = True

        existing_langs = (
            article.get_available_language_codes()
        )
        filtered_choices = [x for x in self.fields['lang'].choices
                            if x[0] not in existing_langs]
        self.fields['lang'].choices = filtered_choices
        if lang:
            self.fields['lang'].initial = lang


class EditArticleForm(ArticleForm):
    parent_id = forms.IntegerField(label='', widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(EditArticleForm, self).__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields['parent_id'].widget.attrs['value'] = self.instance.pk

        self.fields['slug'].widget.attrs['readonly'] = True

        self.fields['lang'].widget = forms.TextInput(attrs={
            'readonly': True
        })

        self.fields.keyOrder.append('parent_id')

    def clean(self):
        super(EditArticleForm, self).clean()
        self.merge_contents_if_needed()
        return self.cleaned_data

    def merge_contents_if_needed(self):
        parent_id = self.cleaned_data['parent_id']
        article = None
        articleContent = None
        slug = self.cleaned_data['slug']
        lang = self.cleaned_data['lang']
        try:
            article = Article.objects.get(slug=slug)
        except:
            article = Article(slug=slug)

        articleContent = article.get_newest_content(lang)
        if articleContent is None:
            articleContent = ArticleContent(article=article, lang=lang)

        if parent_id and parent_id != articleContent.pk:
            parent = ArticleContent.objects.get(id=parent_id)
            a = parent
            b = articleContent
            ancestors = set()
            commonAncestor = None
            while True:
                if a and a.pk in ancestors:
                    commonAncestor = a
                    break
                if b and b.pk in ancestors:
                    commonAncestor = b
                    break
                ancestors.add(a.pk)
                ancestors.add(b.pk)
                a = a.parent
                b = b.parent
                if a and a.parent is None and b and b.parent is None:
                    break

            try:
                merged = merge(self.cleaned_data['content'],
                               commonAncestor.content, articleContent.content)
                self.cleaned_data['content'] = merged
            except MergeError as e:
                raise ValidationError('Merge conflict.',
                                      params={'diff': e.diff})

        return True
