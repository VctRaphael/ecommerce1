from django.test import TestCase

class WsgiCoverageTest(TestCase):
    def test_wsgi_import(self):
        import ecommerce.wsgi
        self.assertTrue(hasattr(ecommerce.wsgi, "application"))

class AsgiCoverageTest(TestCase):
    def test_asgi_import(self):
        import ecommerce.asgi
        self.assertTrue(hasattr(ecommerce.asgi, "application"))

class UrlsCoverageTest(TestCase):
    def test_urls_import(self):
        import ecommerce.urls
        self.assertTrue(hasattr(ecommerce.urls, "urlpatterns"))