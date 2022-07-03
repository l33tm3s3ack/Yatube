import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTest(TestCase):
    POSTAMOUNT = 15
    POST_PER_LIST = 10

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.simple_image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B')
        cls.image = SimpleUploadedFile(name='simple_image.jpg',
                                       content=cls.simple_image,
                                       content_type='image/jpeg')
        cls.user = User.objects.create_user(username='author')
        cls.image_folder = 'posts/'
        cls.other_user = User.objects.create_user(username='test_dude')

        GROUPAMOUNT = 2
        # Создаем две группы для проверки включения постов в группы
        for i in range(GROUPAMOUNT):
            Group.objects.create(
                title=f'test group {i}',
                slug=f'test-group{i}',
                description='group for tests'
            )
        cls.main_group = Group.objects.get(title='test group 0')
        cls.backup_group = Group.objects.get(title='test group 1')
        # Создаем посты для теста пажинатора и отображения страниц.
        for i in range(cls.POSTAMOUNT):
            Post.objects.create(
                id=i,
                text=f'test post {i}',
                author=User.objects.get(username='author'),
                group=cls.main_group,
                image=cls.image
            )
        cls.post_for_edit = Post.objects.latest('pub_date')
        cls.main_page = ('posts:main_page', None,
                         '../templates/posts/index.html')
        cls.group_list = ('posts:group_list', [cls.main_group.slug],
                          '../templates/posts/group_list.html')
        cls.profile = ('posts:profile', [cls.user.username],
                       'posts/profile.html')
        cls.post_detail = ('posts:post_detail', [cls.post_for_edit.id],
                           'posts/post_detail.html')
        cls.post_create = ('posts:post_create', None, 'posts/create_post.html')
        cls.post_edit = ('posts:post_edit', [cls.post_for_edit.id],
                         'posts/create_post.html')
        cls.follow_link = ('posts:profile_follow', [cls.user.username],)
        cls.unfollow_link = ('posts:profile_unfollow', [cls.user.username],)
        cls.follow_index = ('posts:follow_index', None, 'posts/follow.html')
        cls.names_and_templates = (
            cls.main_page,
            cls.group_list,
            cls.profile,
            cls.post_detail,
            cls.post_create,
            cls.post_edit,
            cls.follow_index)
        cls.create_post_links = (cls.post_create,
                                 cls.post_edit)
        cls.links_with_list_of_post = (cls.main_page,
                                       cls.group_list,
                                       cls.profile)
        cls.other_group_link = reverse(
            'posts:group_list', args=[cls.backup_group.slug])

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.other_client = Client()
        self.other_client.force_login(self.other_user)
        cache.clear()

    def test_posts_name_resolved(self):
        """Проверяем отклик на имена ссылок"""
        for name, argument, template_ in self.names_and_templates:
            with self.subTest(name=name):
                response = self.authorized_client.get(
                    reverse(name, args=argument))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_name_templates_correct(self):
        """Проверяем корректное использование шаблонов при обработке имён"""
        for name, args, template in self.names_and_templates:
            with self.subTest(name=name):
                response = self.authorized_client.get(
                    reverse(name, args=args))
                self.assertTemplateUsed(response, template)

    def test_form_fields_in_templates_correct(self):
        """Проверяем передачу формы в шаблон создания и редактирования поста"""
        for link, args, template_ in self.create_post_links:
            response = self.authorized_client.get(reverse(link, args=args))
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
            }
            for field, type_field in form_fields.items():
                with self.subTest(field=field):
                    form_field = response.context.get('form').fields.get(field)
                    self.assertIsInstance(form_field, type_field)

    def check_fields(self, object, post):
        """Проверка полей контекста"""
        self.assertEqual(object.text, post.text)
        self.assertEqual(object.author, post.author)
        self.assertEqual(object.group, post.group)
        self.assertIsNotNone(object.image)

    def test_object_in_context_views(self):
        """Проверяем контекст постов главной страницы,
        групп постов и профиля пользователя"""
        for link, args, template_ in self.links_with_list_of_post:
            response = self.authorized_client.get(reverse(link, args=args))
            object = response.context['page_obj'][0]
            self.check_fields(object, self.post_for_edit)

    def test_context_in_post_detail(self):
        """Проверка контекста в подробной информации о постах"""
        response = self.authorized_client.get(
            reverse(self.post_detail[0], args=self.post_detail[1]))
        object = response.context['post']
        self.check_fields(object, self.post_for_edit)

    def test_group_obj_in_group_list(self):
        """Проверяем контескт групп в списке групп"""
        response = self.authorized_client.get(
            reverse(self.group_list[0], args=self.group_list[1]))
        object = response.context['group']
        self.assertEqual(object.title, self.main_group.title)
        self.assertEqual(object.description, self.main_group.description)

    def test_paginator_in_links(self):
        """Проверяем работу пажинатора на страницах"""
        cache.clear()
        for link, args, template_ in self.links_with_list_of_post:
            first_page = self.authorized_client.get(reverse(link, args=args))
            second_page = self.authorized_client.get(reverse(link, args=args)
                                                     + '?page=2')
            self.assertEqual(len(first_page.context['page_obj']),
                             self.POST_PER_LIST)
            self.assertEqual(len(second_page.context['page_obj']),
                             (self.POSTAMOUNT - self.POST_PER_LIST))

    def test_other_group_doesnt_have_posts(self):
        """Проверяем, что в других группах нет созданных постов"""
        response = self.authorized_client.get(self.other_group_link)
        list = response.context['page_obj']
#       В этой группе ничего нет, она должна быть пустой.
        self.assertEqual(len(list), 0)

    def test_cache_data(self):
        """Проверяем сохранение данных в кэше"""
        cache_page = self.authorized_client.get(
            reverse(self.main_page[0])).content
        self.post_for_edit.delete()
        new_entry = self.authorized_client.get(
            reverse(self.main_page[0])).content
        self.assertEqual(new_entry, cache_page)
        cache.clear()
        another_entry = self.authorized_client.get(
            reverse(self.main_page[0])).content
        self.assertNotEqual(another_entry, cache_page)

    def test_follow_user(self):
        """Проверяем, что пользователь может
        подписаться на автора и потом отписаться"""
        self.other_client.get(reverse(self.follow_link[0],
                              args=self.follow_link[1]))
        following = Follow.objects.filter(
            user=self.other_user, author=self.user).exists()
        self.assertTrue(following)
        self.other_client.get(reverse(self.unfollow_link[0],
                              args=self.unfollow_link[1]))
        following = Follow.objects.filter(
            user=self.other_user, author=self.user).exists()
        self.assertFalse(following)

    def test_follow_content_sheet(self):
        """Проверяем, что посты приходят в ленту только подписчиков"""
        self.other_client.get(reverse(self.follow_link[0],
                              args=self.follow_link[1]))
        response = self.other_client.get(reverse(self.follow_index[0]))
        content = response.context['page_obj']
        # У этого пользователя должны быть посты, ведь он только что подписался
        self.assertNotEqual(len(content), 0)
        new_entry = self.authorized_client.get(reverse(self.follow_index[0]))
        content = new_entry.context['page_obj']
        self.assertEqual(len(content), 0)
