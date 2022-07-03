from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='название')
    slug = models.SlugField(max_length=30,
                            unique=True,
                            verbose_name='идентификатор')
    description = models.TextField(verbose_name='описание')

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name='текст поста',)
    pub_date = models.DateTimeField(auto_now_add=True,
                                    null=False,
                                    blank=False,
                                    verbose_name='дата публикации')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='posts',
                               verbose_name='автор поста')
    group = models.ForeignKey(Group,
                              on_delete=models.SET_NULL,
                              related_name='group_posts',
                              blank=True,
                              null=True,
                              verbose_name='группа поста',)
    image = models.ImageField('Картинка',
                              upload_to='posts/',
                              blank=True)

    def __str__(self):
        LEN = 15
        return self.text[::LEN]

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'


class Comment(models.Model):
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             related_name='comment',
                             verbose_name='комментируемый пост')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comment',
                               verbose_name='автор комментария')
    text = models.TextField(verbose_name='текст комментария')
    created = models.DateTimeField(auto_now_add=True,
                                   null=False,
                                   blank=False,)


class Follow(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='follower',
                             verbose_name='подписчик')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='following',
                               verbose_name='автор')
