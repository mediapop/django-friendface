from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from friendface.fixtures import FacebookPageFactory, \
    FacebookApplicationFactory, FacebookUserFactory, \
    FacebookInvitationFactory, FacebookAuthorizationFactory


class TestFacebookPageAdmin(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin',
                                      email=None,
                                      password='password')
        self.client.login(username='admin', password='password')
        self.page = FacebookPageFactory()

    def test_access_changelist(self):
        response = self.client.get(reverse('admin:%s_%s_changelist' % (
            self.page._meta.app_label,
            self.page._meta.module_name
        )))
        self.assertTemplateUsed(response, 'admin/change_list.html')

    def test_access_add(self):
        response = self.client.get(reverse('admin:%s_%s_add' % (
            self.page._meta.app_label,
            self.page._meta.module_name
        )))
        self.assertTemplateUsed(response, 'admin/change_form.html')

    def test_access_change(self):
        response = self.client.get(reverse('admin:%s_%s_change' % (
            self.page._meta.app_label,
            self.page._meta.module_name
        ), args=(self.page.pk,)))
        self.assertTemplateUsed(response, 'admin/change_form.html')


class TestFacebookApplicationAdmin(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin',
                                      email=None,
                                      password='password')
        self.client.login(username='admin', password='password')
        self.application = FacebookApplicationFactory()

    def test_access_changelist(self):
        response = self.client.get(reverse('admin:%s_%s_changelist' % (
            self.application._meta.app_label,
            self.application._meta.module_name
        )))
        self.assertTemplateUsed(response, 'admin/change_list.html')

    def test_access_add(self):
        response = self.client.get(reverse('admin:%s_%s_add' % (
            self.application._meta.app_label,
            self.application._meta.module_name
        )))
        self.assertTemplateUsed(response, 'admin/change_form.html')

    def test_access_change(self):
        response = self.client.get(reverse('admin:%s_%s_change' % (
            self.application._meta.app_label,
            self.application._meta.module_name
        ), args=(self.application.pk,)))
        self.assertTemplateUsed(response, 'admin/change_form.html')


class TestFacebookUserAdmin(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin',
                                      email=None,
                                      password='password')
        self.client.login(username='admin', password='password')
        self.user = FacebookUserFactory()

    def test_access_changelist(self):
        response = self.client.get(reverse('admin:%s_%s_changelist' % (
            self.user._meta.app_label,
            self.user._meta.module_name
        )))
        self.assertTemplateUsed(response, 'admin/change_list.html')

    def test_access_add(self):
        response = self.client.get(reverse('admin:%s_%s_add' % (
            self.user._meta.app_label,
            self.user._meta.module_name
        )))
        self.assertTemplateUsed(response, 'admin/change_form.html')

    def test_access_change(self):
        response = self.client.get(reverse('admin:%s_%s_change' % (
            self.user._meta.app_label,
            self.user._meta.module_name
        ), args=(self.user.pk,)))
        self.assertTemplateUsed(response, 'admin/change_form.html')


class TestFacebookInvitationAdmin(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin',
                                      email=None,
                                      password='password')
        self.client.login(username='admin', password='password')
        self.invitation = FacebookInvitationFactory()

    def test_access_changelist(self):
        response = self.client.get(reverse('admin:%s_%s_changelist' % (
            self.invitation._meta.app_label,
            self.invitation._meta.module_name
        )))
        self.assertTemplateUsed(response, 'admin/change_list.html')

    def test_access_add(self):
        response = self.client.get(reverse('admin:%s_%s_add' % (
            self.invitation._meta.app_label,
            self.invitation._meta.module_name
        )))
        self.assertTemplateUsed(response, 'admin/change_form.html')

    def test_access_change(self):
        response = self.client.get(reverse('admin:%s_%s_change' % (
            self.invitation._meta.app_label,
            self.invitation._meta.module_name
        ), args=(self.invitation.pk,)))
        self.assertTemplateUsed(response, 'admin/change_form.html')


class TestFacebookAuthorizationAdmin(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin',
                                      email=None,
                                      password='password')
        self.client.login(username='admin', password='password')
        self.invitation = FacebookAuthorizationFactory()

    def test_access_changelist(self):
        response = self.client.get(reverse('admin:%s_%s_changelist' % (
            self.invitation._meta.app_label,
            self.invitation._meta.module_name
        )))
        self.assertTemplateUsed(response, 'admin/change_list.html')

    def test_access_add(self):
        response = self.client.get(reverse('admin:%s_%s_add' % (
            self.invitation._meta.app_label,
            self.invitation._meta.module_name
        )))
        self.assertTemplateUsed(response, 'admin/change_form.html')

    def test_access_change(self):
        response = self.client.get(reverse('admin:%s_%s_change' % (
            self.invitation._meta.app_label,
            self.invitation._meta.module_name
        ), args=(self.invitation.pk,)))
        self.assertTemplateUsed(response, 'admin/change_form.html')
