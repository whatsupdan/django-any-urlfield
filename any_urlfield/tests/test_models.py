from __future__ import unicode_literals

from any_urlfield.models import AnyUrlValue
from any_urlfield.registry import UrlTypeRegistry
from any_urlfield.tests import PageModel, RegPageModel, UrlModel
from django.test import TestCase

try:
    from django.utils import six
    unicode = six.text_type
except ImportError:
    pass  # Python 2, Django 1.3


class AnyUrlTests(TestCase):
    maxDiff = None

    def test_registry(self):
        """
        Test the basic registry setup.
        """
        reg = UrlTypeRegistry()
        self.assertIsNotNone(reg['http'])
        self.assertIsNotNone(reg['https'])

    def test_from_model(self):
        """
        Basic test of ``from_model``.
        """
        page2 = RegPageModel.objects.create(pk=1, slug='foo2')
        v = AnyUrlValue.from_model(page2)

        self.assertEqual(v.url_type.prefix, 'any_urlfield.regpagemodel')   # app_label.modelname
        self.assertEqual(v.type_value, page2.id)
        self.assertEqual(v.to_db_value(), 'any_urlfield.regpagemodel://1')

    def test_from_db_value(self):
        """
        Basic test of ``from_db_value``.
        """
        reg = UrlTypeRegistry()

        v = AnyUrlValue.from_db_value("http://www.example.com/", reg)
        self.assertEqual(v.type_prefix, 'http')
        self.assertEqual(v.type_value, "http://www.example.com/")
        self.assertEqual(unicode(v), "http://www.example.com/")

    def test_from_db_value_https(self):
        """
        Make sure other URLs are properly serialized.
        """
        reg = UrlTypeRegistry()

        v = AnyUrlValue.from_db_value("https://www.example.com/", reg)
        self.assertEqual(v.type_prefix, 'http')   # http is the constant for external URL types
        self.assertEqual(v.type_value, "https://www.example.com/")
        self.assertEqual(unicode(v), "https://www.example.com/")

    def test_from_db_value_ftps(self):
        """
        Make sure other URLs are properly serialized.
        """
        reg = UrlTypeRegistry()

        v = AnyUrlValue.from_db_value("ftps://www.example.com/", reg)
        self.assertEqual(v.type_prefix, 'http')   # http is the constant for external URL types
        self.assertEqual(v.type_value, "ftps://www.example.com/")
        self.assertEqual(unicode(v), "ftps://www.example.com/")

    def test_from_db_value_mailto(self):
        """
        Test constructing the value from ID.
        """
        reg = UrlTypeRegistry()

        v = AnyUrlValue.from_db_value("mailto://test@example.com", reg)
        self.assertEqual(v.type_prefix, 'http')   # http is the constant for external URL types
        self.assertEqual(v.type_value, "mailto://test@example.com")
        self.assertEqual(unicode(v), "mailto://test@example.com")

    def test_valid_db_id(self):
        """
        Make sure ID values are properly stored and serialized.
        """
        reg = UrlTypeRegistry()
        urltype = reg.register(PageModel)

        page = PageModel.objects.create(slug='foo')
        v = AnyUrlValue(urltype.prefix, page.id, reg)

        # Database state
        self.assertTrue(page.id)
        self.assertEqual(urltype.prefix, 'any_urlfield.pagemodel')   # app_label.modelname
        self.assertEqual(v.type_prefix, urltype.prefix)
        self.assertEqual(v.type_value, page.id)
        self.assertEqual(v.to_db_value(), 'any_urlfield.pagemodel://1')

        # Frontend
        self.assertEqual(unicode(v), "/foo/")          # fetches model and returns get_absolute_url()

        # Programmer API's
        self.assertIs(v.get_model(), PageModel)
        self.assertEqual(v.get_object(), page)
        self.assertTrue(v.exists())

    def test_invalid_db_id(self):
        """
        Make sure invalid ID's are properly handled and recognized.
        """
        reg = UrlTypeRegistry()
        urltype = reg.register(PageModel)
        v = AnyUrlValue(urltype.prefix, 999999, reg)

        # Database state
        self.assertEqual(v.type_value, 999999)
        self.assertEqual(v.to_db_value(), 'any_urlfield.pagemodel://999999')

        # Frontend
        from any_urlfield.models.values import logger
        logger.warning("NOTE: The following statement will cause a log to output")
        self.assertEqual(unicode(v), "#DoesNotExist")       # Avoids frontend errors

        # Programmer API's
        self.assertIs(v.get_model(), PageModel)
        self.assertRaises(PageModel.DoesNotExist, lambda: v.get_object())
        self.assertFalse(v.exists())

    def test_bool_empty(self):
        """
        Make sure empty value is treated as false.
        """
        x = AnyUrlValue.from_db_value('')
        self.assertFalse(1 if x else 0)
        self.assertFalse(x.exists())

    def test_db_empty_pre_save(self):
        """
        Make sure saving empty values works.
        """
        obj = UrlModel()
        obj.save()
        self.assertTrue(obj.pk)

    def test_db_pre_save(self):
        """
        Make sure saving works
        """
        obj = UrlModel(url=AnyUrlValue.from_db_value('http://www.example.org/'))
        obj.save()
        self.assertTrue(obj.pk)
