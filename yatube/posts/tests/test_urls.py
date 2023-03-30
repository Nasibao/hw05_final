from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()

PAGE_404 = '/page_404/'


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.other_user = User.objects.create_user(username='other')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.auth_client = Client()
        self.other_auth_client = Client()
        self.non_auth_client = Client()
        self.auth_client.force_login(self.user)
        self.other_auth_client.force_login(self.other_user)
        cache.clear()

    def test_response_status_for_non_auth_client(self):
        urls = {
            reverse('posts:index'): HTTPStatus.OK,
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug},
            ): HTTPStatus.OK,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username},
            ): HTTPStatus.OK,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk},
            ): HTTPStatus.OK,
            PAGE_404: HTTPStatus.NOT_FOUND,
        }
        for url, status in urls.items():
            with self.subTest():
                response = self.non_auth_client.get(url)
                self.assertEqual(response.status_code, status)

    def test_response_status_for_auth_client(self):
        urls = {
            reverse('posts:index'): HTTPStatus.OK,
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug},
            ): HTTPStatus.OK,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username},
            ): HTTPStatus.OK,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk},
            ): HTTPStatus.OK,
            reverse('posts:post_create'): HTTPStatus.OK,
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk},
            ): HTTPStatus.OK,
            PAGE_404: HTTPStatus.NOT_FOUND,
        }
        for url, status in urls.items():
            with self.subTest():
                response = self.auth_client.get(url)
                self.assertEqual(response.status_code, status)

    def test_teplates(self):
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

    def test_redirects_for_non_auth_client(self):
        urls = [
            reverse('posts:post_create'),
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk},
            ),
        ]
        for url in urls:
            with self.subTest():
                response = self.non_auth_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                self.assertIn(reverse('users:login'), response.url)

    def test_redirects_for_non_author(self):
        url = reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.pk},
        )
        response = self.other_auth_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}),
            response.url,
        )
