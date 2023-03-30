import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.user = User.objects.create_user(username='auth')
        cls.other_user = User.objects.create_user(username='other')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.other_group = Group.objects.create(
            title='Тестовая группа',
            slug='other_test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        cache.clear()

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(self.user)
        cache.clear()

    def test_templates(self):
        urls = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug},
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username},
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk},
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk},
            ): 'posts/post_create.html',
        }
        for url, template in urls.items():
            with self.subTest():
                response = self.auth_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_index_page_use_correct_context(self):
        response = self.auth_client.get(reverse('posts:index'))
        post1_page_obj = response.context['page_obj'][0]
        context_objects = {
            self.post.author: post1_page_obj.author,
            self.post.text: post1_page_obj.text,
            self.post.group: post1_page_obj.group,
            self.post.image: post1_page_obj.image,
        }
        for object_item, context_item in context_objects.items():
            with self.subTest():
                self.assertEqual(object_item, context_item)

    def test_group_posts_page_use_correct_context(self):
        response = self.auth_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug},
            ),
        )
        post1_page_obj = response.context['page_obj'][0]
        group = response.context['group']
        context_objects = {
            self.post.author: post1_page_obj.author,
            self.post.text: post1_page_obj.text,
            self.post.group: post1_page_obj.group,
            self.post.image: post1_page_obj.image,
            self.group: group,
        }
        for object_item, context_item in context_objects.items():
            with self.subTest():
                self.assertEqual(object_item, context_item)

    def test_profile_page_use_correct_context(self):
        response = self.auth_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username},
            ),
        )
        post1_page_obj = response.context['page_obj'][0]
        athour = response.context['author']
        context_objects = {
            self.post.author: post1_page_obj.author,
            self.post.text: post1_page_obj.text,
            self.post.group: post1_page_obj.group,
            self.post.image: post1_page_obj.image,
            self.user: athour,
        }
        for object_item, context_item in context_objects.items():
            with self.subTest():
                self.assertEqual(object_item, context_item)

    def test_post_detail_page_use_correct_context(self):
        response = self.auth_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk},
            ),
        )
        post = response.context['post']
        user_posts_count = response.context['user_posts_count']
        context_objects = {
            self.post.author: post.author,
            self.post.text: post.text,
            self.post.group: post.group,
            self.post.image: post.image,
            Post.objects.filter(author=self.user).count(): user_posts_count,
        }
        for object_item, context_item in context_objects.items():
            with self.subTest():
                self.assertEqual(object_item, context_item)

    def test_post_create_page_use_correct_context(self):
        response = self.auth_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for field_name, field_type in form_fields.items():
            with self.subTest():
                form_field = response.context['form'].fields.get(field_name)
                self.assertIsInstance(form_field, field_type)

    def test_post_edit_page_use_correct_context(self):
        response = self.auth_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk},
            ),
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for field_name, field_type in form_fields.items():
            with self.subTest():
                form_field = response.context['form'].fields.get(field_name)
                self.assertIsInstance(form_field, field_type)
        post = response.context['post']
        context_objects = {
            response.context['is_edit']: True,
            self.post.author: post.author,
            self.post.text: post.text,
            self.post.group: post.group,
            self.post.image: post.image,
        }
        for object_item, context_item in context_objects.items():
            with self.subTest():
                self.assertEqual(object_item, context_item)

    def test_post_create_show_on_pages(self):
        urls = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug},
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username},
            ),
        ]
        for url in urls:
            with self.subTest():
                response = self.auth_client.get(url)
                posts_count = len(response.context['page_obj'])
                Post.objects.create(
                    author=self.user,
                    text='Тестовый пост',
                    group=self.group,
                )
                cache.clear()
                response = self.auth_client.get(url)
                self.assertEqual(
                    posts_count + 1,
                    len(response.context['page_obj']),
                )

    def test_post_create_doesnt_show_on_pages(self):
        urls = [
            reverse(
                'posts:group_list',
                kwargs={'slug': self.other_group.slug},
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.other_user.username},
            ),
        ]
        for url in urls:
            with self.subTest():
                response = self.auth_client.get(url)
                posts_count = len(response.context['page_obj'])
                Post.objects.create(
                    author=self.user,
                    text='Тестовый пост',
                    group=self.group,
                )
                response = self.auth_client.get(url)
                self.assertEqual(
                    posts_count,
                    len(response.context['page_obj']),
                )

    def test_follow_for_auth(self):
        follow_count = Follow.objects.count()
        Follow.objects.create(
            user=self.user,
            author=self.other_user,
        )
        self.auth_client.post(reverse(
            'posts:profile_follow', kwargs={'username': self.other_user},
        ))
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.other_user,
            ).exists(),
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)

    def test_unfollow_for_auth(self):
        Follow.objects.create(
            user=self.user,
            author=self.other_user
        )
        follow_count = Follow.objects.count()
        self.auth_client.post(reverse(
            'posts:profile_unfollow', kwargs={'username': self.other_user},
        ))
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.other_user,
            ).exists(),
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)
