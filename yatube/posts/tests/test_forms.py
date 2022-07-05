import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests (TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.simple_image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(name='simple_image.jpg',
                                       content=cls.simple_image,
                                       content_type='image/jpeg')
        cls.image_2 = SimpleUploadedFile(name='simple_image_2.jpg',
                                         content=cls.simple_image,
                                         content_type='image/jpeg')
        cls.post = Post.objects.create(
            text='test post',
            author=User.objects.get(username='author'),
        )
        cls.assigned_group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовая группа',
        )
        cls.link_comment = reverse('posts:add_comment',
                                   kwargs={'post_id': cls.post.id})
        cls.link_create_redirect = reverse(
            'posts:profile',
            kwargs={'username': cls.user.username})
        cls.link_edit_redirect = reverse('posts:post_edit',
                                         kwargs={'post_id': cls.post.id})

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.guest_client = Client()
        self.authorized_client.force_login(self.user)

    def check_fields(self, post, form):
        self.assertEqual(post.text, form['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group.id, form['group'])
        self.assertIn(form['image'].name, post.image.name)

    def test_create_post(self):
        """Проверяем, что можно создать пост"""
        post_count = Post.objects.count()
        form_data = {'text': 'Текст нового поста',
                     'group': self.assigned_group.id,
                     'image': self.image}
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_data, follow=True)
        created_post = Post.objects.latest('pub_date')
        self.assertRedirects(response, self.link_create_redirect)
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.check_fields(created_post, form_data)
        self.assertIn(self.image.name, created_post.image.name)

    def test_edit_post(self):
        """Проверяем, что можно отредактировать пост"""
        form_data = {'text': 'Пост отредактирован',
                     'group': self.assigned_group.id,
                     'image': self.image_2}
        self.authorized_client.post(self.link_edit_redirect,
                                    form_data)
        redacted_post = Post.objects.get(id=self.post.id)
        self.check_fields(redacted_post, form_data)

    def test_guest_cant_create_posts(self):
        """Проверяем, что пост не может быть создан гостем"""
        form_data = {'text': 'Текст поста для гостя'}
        create_post = self.guest_client.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )
        self.assertRaises(Exception, create_post)

    def test_comment_form(self):
        """Проверяем добавление комментариев"""
        form_data = {'text': 'Комментарий к сообщению'}
        response = self.authorized_client.post(self.link_comment,
                                               form_data,
                                               follow=True)
        comment = response.context['comments'][0]
        db_comment = Comment.objects.get(text=form_data['text'])
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.text, db_comment.text)
