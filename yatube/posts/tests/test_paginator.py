from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

FIRST_PAGE_POSTS_COUNT: int = 10
SECOND_PAGE_POSTS_COUNT: int = 3

User = get_user_model()


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.posts = [Post(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        ) for _ in range(FIRST_PAGE_POSTS_COUNT + SECOND_PAGE_POSTS_COUNT)]
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(self.user)
        self.non_auth_client = Client()

    def test_posts_count_on_first_page(self):
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
                self.assertEqual(
                    len(response.context['page_obj']),
                    FIRST_PAGE_POSTS_COUNT,
                )

    def test_posts_count_on_second_page(self):
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
                response = self.auth_client.get(url + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    SECOND_PAGE_POSTS_COUNT,
                )
