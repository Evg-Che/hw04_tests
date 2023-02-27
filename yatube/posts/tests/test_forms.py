from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='UserTest')
        cls.group_1 = Group.objects.create(
            title='Тестовая группа_1',
            slug='group_test_1'
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа_2',
            slug='group_test_2'
        )
        cls.group_3 = Group.objects.create(
            title='Тестовая группа_3',
            slug='group_test_3'
        )

    def setUp(self):
        self.guest_user = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
            group=self.group_1)

    def test_create_post_form(self):
        post_count = Post.objects.all().count()
        form_data = {
            'text': 'Новый пост',
            'group': self.group_1.id
        }
        response = self.authorized_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(
            Post.objects.all().count(),
            post_count + 1,
            'Пост не сохранен в базу данных!'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post = Post.objects.latest('id')
        self.assertTrue(post.text == form_data['text'])
        self.assertTrue(post.author == self.user)
        self.assertTrue(post.group_id == form_data['group'])

    def test_edit_post_form(self):
        form_data = {
            'text': 'Новый пост_ред.',
            'group': self.group_2.id
        }
        response = self.authorized_user.post(
            reverse('posts:post_edit', args=[self.post.pk]),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post = Post.objects.get(id=self.post.pk)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group_id, form_data['group'])

    def test_unauthorized_user_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый пост',
            'group': self.group_3.id,
        }
        response = self.guest_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        redirect = reverse('login') + '?next=' + reverse('posts:post_create')
        self.assertRedirects(response, redirect)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_unauthorized_user_edit(self):
        redir = reverse('users:login')
        redir_2 = reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group_3.id,
        }
        response = self.guest_user.post(
            redir_2,
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(
            response,
            f"{redir}?next={redir_2}")

        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост',
            ).exists()
        )
