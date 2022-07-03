from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    LEN_PREVIEW = 15

    def test_post_models_have_correct_object_names(self):
        """Проверяем, что у модели поста корректно работает __str__."""
        error = 'отображение поста не работает'
        with self.subTest(error):
            self.assertEqual(str(self.post),
                             self.post.text[::self.LEN_PREVIEW])
            self.assertEqual(str(self.group), self.group.title)
