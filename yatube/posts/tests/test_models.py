from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class ModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_post_model_have_correct_object_name(self):
        self.assertEqual(self.post.text[:15], str(self.post))

    def test_group_model_have_correct_object_name(self):
        self.assertEqual(self.group.title, str(self.group))

    def test_post_model_fields_have_verbose_name(self):
        fields = 'text', 'pub_date', 'author', 'group'
        for field in fields:
            with self.subTest():
                verbose = Post._meta.get_field(field).verbose_name
                self.assertNotEqual(verbose, field)

    def test_group_model_fields_have_verbose_name(self):
        fields = 'title', 'slug', 'description'
        for field in fields:
            with self.subTest():
                verbose = Group._meta.get_field(field).verbose_name
                self.assertNotEqual(verbose, field)

    def test_post_model_fields_have_help_text(self):
        fields = 'text', 'group'
        for field in fields:
            with self.subTest():
                verbose = Post._meta.get_field(field).help_text
                self.assertNotEqual(verbose, field)

    def test_group_model_fields_have_help_text(self):
        fields = 'title', 'slug', 'description'
        for field in fields:
            with self.subTest():
                verbose = Group._meta.get_field(field).help_text
                self.assertNotEqual(verbose, field)
