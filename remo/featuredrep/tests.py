from django.core.urlresolvers import reverse
from django.test.client import Client
from nose.tools import eq_
from test_utils import TestCase

from models import FeaturedRep


class ViewsTest(TestCase):
    fixtures = ['demo_users.json', 'demo_featured.json']

    def setUp(self):
        """ Setup Tests """
        self.c = Client()
        self.c.login(username="admin", password="passwd")

    def test_list_featured(self):
        """ Test featuredrep_list_featured view """
        response = self.c.get(reverse('featuredrep_list_featured'),
                              follow=True)
        self.assertTemplateUsed(response, 'featuredrep_list.html')

    def test_add_featured(self):
        """ Test featuredrep_add_featured view """
        response = self.c.post(reverse('featuredrep_add_featured'),
                               {'user': 5, 'text': 'Testing'}, follow=True)
        self.assertTemplateUsed(response, 'featuredrep_list.html')
        eq_(FeaturedRep.objects.count(), 2)
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')

    def test_edit_featured(self):
        """ Test featuredrep_edit_featured view """
        response = self.c.post(reverse('featuredrep_edit_featured', args=[1]),
                               {'user': 5, 'text': 'Foo'}, follow=True,)
        self.assertTemplateUsed(response, 'featuredrep_list.html')
        eq_(FeaturedRep.objects.count(), 1)
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')
        u = FeaturedRep.objects.all()[0]
        eq_(u.text, 'Foo')

    def test_delete_featured(self):
        """ Test featuredrep_delete_featured view """
        response = self.c.post(reverse('featuredrep_delete_featured',
                                       args=[1]), follow=True)
        self.assertTemplateUsed(response, 'featuredrep_list.html')
        eq_(FeaturedRep.objects.count(), 0)
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')
