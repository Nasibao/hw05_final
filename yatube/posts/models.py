from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Имя группы',
        help_text='Введи имя группы',
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Слаг',
        help_text='Подбери уникальный слаг',
    )
    description = models.TextField(
        verbose_name='Описание',
        help_text='Опиши',
    )

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Введите текст поста',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
        db_index=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name='Автор',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="posts",
        verbose_name='Группа',
        help_text='Выберите группу',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
    )

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост',
        help_text='Пост, к которому будет оставлен комментарий',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='comments',
        blank=True,
        null=True,
        verbose_name='Автор комментария',
    )
    text = models.TextField(
        null=True,
        max_length=100,
        verbose_name='Текст комментария',
        help_text='Текст нового комментария',
    )
    created = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата публикации комментария',
    )

    class Meta:
        ordering = ('-created', )


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        blank=True,
        null=True,
        verbose_name='Имя подписчика',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        blank=True,
        null=True,
        verbose_name='Имя автора',
    )

    class Meta:
        constraints = (models.UniqueConstraint(fields=('user', 'author'),
                                               name='unique_following'), )
