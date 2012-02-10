from nose.tools import eq_
from test_utils import TestCase
from django.test.client import Client

from models import FeaturedRep

class ViewsTest(TestCase):
    fixtures = ['demo_users.json',
                'demo_featured.json']

    def setUp(self):
        self.c = Client()
        self.c.login(username="admin", password="passwd")


    def test_list_featured(self):
        # Missing comment
        response = self.c.get('/featured/', follow=True)
        self.assertTemplateUsed(response, 'featuredrep_list.html')


    def test_add_featured(self):
        # Missing comment
        response = self.c.post('/featured/add/',
                               {'user':5, 'text':'Testing'},
                               follow=True)
                               # follow should be two spaces in, under the u
                               # in 'user'
        self.assertTemplateUsed(response, 'featuredrep_list.html')
        eq_(FeaturedRep.objects.count(), 2)
        for m in response.context['messages']: m
        eq_(m.tags, u'success')


    def test_edit_featured(self):
        # Missing comment
        response = self.c.post('/featured/edit/1/',
                               {'user':5, 'text':'Foo'},
                               follow=True,)
        self.assertTemplateUsed(response, 'featuredrep_list.html')
        eq_(FeaturedRep.objects.count(), 1)
        for m in response.context['messages']: m
        eq_(m.tags, u'success')
        u = FeaturedRep.objects.all()[0]
        eq_(u.text, 'Foo')


    def test_delete_featured(self):
        # Missing comment
        response = self.c.post('/featured/delete/1/', follow=True)
        self.assertTemplateUsed(response, 'featuredrep_list.html')
        eq_(FeaturedRep.objects.count(), 0)
        for m in response.context['messages']: m
        eq_(m.tags, u'success')
