from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User.objects.create_user(username='author')

        Group.objects.create(
            title='test group',
            slug='test-group',
            description='group for tests'
        )
        Post.objects.create(
            id=1,
            text='test post',
            author=User.objects.get(username='author'),
            group=Group.objects.get(title='test group')
        )
    main_page = ('/', '../templates/posts/index.html')
    group_list = ('/group/test-group/',
                  '../templates/posts/group_list.html')
    profile = ('/profile/author/', 'posts/profile.html')
    post_detail = ('/posts/1/', 'posts/post_detail.html')
    create_post = ('/create/', 'posts/create_post.html')
    post_edit = ('/posts/1/edit/', 'posts/create_post.html')
    post_comment = ('/posts/1/comment/', 'posts/post_detail.html')
    common_links_info = (main_page,
                         group_list,
                         profile,
                         post_detail,)
    links_redirect = ((create_post[0], '/auth/login/?next=/create/'),
                      (post_comment[0], '/auth/login/?next=/posts/1/comment/'),
                      (post_edit[0], post_detail[0]))
    auth_links_info = (common_links_info
                       + (create_post,
                          post_edit,))
    unknown_link = '/i-dont-know-what-im-doing/'

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.user = User.objects.create_user(username='Noname')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаем автора поста
        self.author = User.objects.get(username='author')
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        cache.clear()

    def test_response_unknown_links(self):
        """Проверяем, что неизвестная ссылка уводит в 404"""
        response = self.guest_client.get(self.unknown_link)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_guest_redirect_link(self):
        """Проверяем перенаправление на тех ссылках, куда нет входа гостям"""
        for link, redirect in self.links_redirect:
            with self.subTest('проверка не пройдена'):
                response = self.guest_client.get(link)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                self.assertRedirects(response, redirect)

    def test_response_unauthorized_links(self):
        """Проверяем доступность общедоступных ссылок"""
        for link, template_ in self.common_links_info:
            with self.subTest('проверка не пройдена'):
                response = self.guest_client.get(link)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_response_authorized_link(self):
        """Проверяем ссылки для авторизованного пользователя"""
        for link, template_ in self.auth_links_info:
            with self.subTest('проверка не пройдена'):
                response = self.authorized_author.get(link)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_authorized_link(self):
        """Проверяем ссылку редактирования
         для авторизованного пользователя, но не автора"""
        response = self.authorized_client.get(self.post_edit[0])
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, (self.post_detail[0]))

    def test_correct_templates_guest_links(self):
        """Проверяем шаблоны для страниц, доступных гостям"""
        for link, template in self.common_links_info:
            with self.subTest(link=link):
                response = self.guest_client.get(link)
                self.assertTemplateUsed(response, template)

    def test_correct_templates_auth_users_links(self):
        """Проверяем шаблоны для страниц,
         доступных авторизованным пользователям"""

        for link, template in self.auth_links_info:
            with self.subTest(link=link):
                response = self.authorized_author.get(link)
                self.assertTemplateUsed(response, template)

    def test_auth_comment_redirect(self):
        """Проверяем возможность комментирования постов пользователями"""
        response = self.authorized_client.get(self.post_comment[0])
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, (self.post_detail[0]))
