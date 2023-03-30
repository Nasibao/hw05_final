import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormTest(TestCase):
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
            group=cls.group,
        )
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(self.user)
        self.non_auth_client = Client()

    def test_create_post_by_form_add_new_record_to_db(self):
        posts_count = Post.objects.count()
        form = {
            'text': self.post.text,
            'group': self.group.pk,
            'image': self.uploaded.name,
        }
        self.auth_client.post(
            reverse('posts:post_create'),
            data=form,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_create_post_by_modelform_add_new_record_to_db(self):
        posts_count = Post.objects.count()
        request = HttpRequest()
        request.POST = {
            'text': self.post.text,
            'group': self.group.pk,
            'image': self.uploaded.name,
        }
        form = PostForm(request.POST)
        form.instance.author = self.user
        form.save()
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_edit_post_by_form_change_record_in_db(self):
        posts_count = Post.objects.count()
        form = {
            'text': self.post.text + '1',
            'group': self.group.pk,
            'image': self.uploaded.name,
        }
        self.auth_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(Post.objects.get(pk=self.post.pk).text, form['text'])

    def test_create_comment_auth_client(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': self.post.text,
            'author': self.user,
        }
        self.auth_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        response = self.auth_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk},
        ))
        self.assertEqual(
            response.context['comments'][0].text, form_data['text'],
        )

    def test_create_comment_non_auth_client(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': self.post.text,
            'author': self.user,
        }
        self.non_auth_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comment_count)

    def test_cache_index(self):
        pre_content = self.auth_client.get('posts:index').content
        Post.objects.create(
            author=self.user,
            text=self.post.text,
            group=self.group
        )
        post_content = self.auth_client.get('posts:index').content
        self.assertEqual(pre_content, post_content)
        cache.clear()
        post_content = self.auth_client.get('posts:index').content
        self.assertEqual(pre_content, post_content)
