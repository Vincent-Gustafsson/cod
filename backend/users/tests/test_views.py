import os

from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase, force_authenticate
from rest_framework.authtoken.models import Token

import faker

from ..models import UserFollowing


fake = faker.Faker('en')
User = get_user_model()


class UserRegistrationViewTest(APITestCase):
    def setUp(self):
        # Other user for unique validation
        self.non_unique_username = fake.first_name()
        self.non_unique_email = fake.email()
        User.objects.create_user(
            username=self.non_unique_username,
            email=self.non_unique_email,
            password=fake.password()
        )

        # Not unique user generation
        password = fake.password()
        self.non_unique_user = {
            'username': self.non_unique_username,
            'email': self.non_unique_email,
            'password': password,
            'password2': password
        }

        # Valid user generation
        valid_user_password = fake.password()
        self.valid_user = {
            'username': fake.first_name(),
            'email': fake.email(),
            'password': valid_user_password,
            'password2': valid_user_password
        }

        # Short password user generation
        short_user_password = fake.password()[:5]
        self.short_password_user = {
            'username': fake.first_name(),
            'email': fake.email(),
            'password': short_user_password,
            'password2': short_user_password
        }

        # Non matching passwords user generation
        self.non_matching_passwords_user = {
            'username': fake.first_name(),
            'email': fake.email(),
            'password': fake.password()[:6],
            'password2': fake.password()[:6]
        }

    def test_create_valid_user(self):
        """ Tests if user registration works. """
        url = reverse('rest_register')

        response = self.client.post(url, self.valid_user, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.last().username, self.valid_user['username'])
        self.assertEqual(response.data['key'], Token.objects.get().key)

    def test_username_valid(self):
        url = reverse('rest_register')

        response = self.client.post(url, self.valid_user, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_username_invalid(self):
        url = reverse('rest_register')

        data = {
            'username': 'invalid_username',
            'email': 'test@gmail.com',
            'password': 'test12345'
        }

        base_username = data['username']

        for char in ['@', '-', '#', '!', '?']:
            data['username'] += char
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(
                response.json()['username'],
                ['The username may only contain A-Z, a-z, 0-9 and _']
            )

            data['username'] = base_username

    def test_password_validation_length(self):
        """ Tests if the password length validation works. """
        url = reverse('rest_register')

        response = self.client.post(url, self.short_password_user, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            'This password is too short. It must contain at least 6 characters.' in response.json()['password'] # noqa
        )

    def test_password_validation_must_match(self):
        """ Tests if the password matching validation works. """
        url = reverse('rest_register')

        response = self.client.post(url, self.non_matching_passwords_user, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['password'], 'Passwords must match.')

    def test_unique_constraints(self):
        """ Tests if the unique constraints on username and email works. """
        url = reverse('rest_register')

        response = self.client.post(url, self.non_unique_user, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['username'][0], 'user with this username already exists.')
        self.assertEqual(response.json()['email'][0], 'user with this email already exists.')


class AuthViewsTest(APITestCase):
    def setUp(self):
        self.details_user = User.objects.create_user(
            username='testUserDetails',
            email='testUserDetails@test.com',
            password=fake.password()
        )

        self.change_password_user = User.objects.create_user(
            username='testUserPassword',
            email='testUserPassword@test.com',
            password=fake.password()
        )

    def test_login_user(self):
        url = reverse('rest_login')

        user = User.objects.create_user(
            username='testLogin',
            email='testLogin@test.com',
            password='12345'
        )

        data = {
            'username': 'testLogin',
            'password': '12345'
        }

        response = self.client.post(url, data, format='json')

        token = Token.objects.get(user=user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['key'], token.key)

    def test_logout_user(self):
        url = reverse('rest_logout')

        user = User.objects.create_user(
            username='testUserLogout',
            email='testUserLogout@test.com',
            password='12345'
        )
        token = Token.objects.create(user=user)

        response = self.client.post(url)
        force_authenticate(response, user=user, token=token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_user_details(self):
        url = reverse('rest_user_details')

        self.client.force_authenticate(self.details_user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['id'], self.details_user.id)

    def test_update_user_details(self):
        url = reverse('rest_user_details')

        updated_username = fake.first_name()

        data = {'username': updated_username}

        self.client.force_authenticate(self.details_user)
        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.get(pk=self.details_user.id).username, updated_username)

    def test_change_password(self):
        url = reverse('rest_password_change')

        new_password = fake.password()
        data = {'new_password1': new_password, 'new_password2': new_password}

        old_password_hash = self.change_password_user.password

        self.client.force_authenticate(self.change_password_user)
        response = self.client.post(url, data)

        new_password_hash = self.change_password_user.password

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(old_password_hash, new_password_hash)


class UserViewsTest(APITestCase):
    def setUp(self):
        for i in range(3):
            User.objects.create_user(
                username=f'{i}{fake.first_name()}',
                email=f'{i}{fake.email()}',
                password=fake.password()
            )

        self.users = User.objects.all()

    def test_list_users(self):
        """ Tests if the user-list endpoint returns all the users """
        # TODO Will have to add test cases for search params and stuff
        url = reverse('user-list')

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), User.objects.count())

        for (i, user) in enumerate(self.users):
            self.assertEqual(user.username, response.json()[i]['username'])

    def test_retrieve_user(self):
        """ Tests if the user detail endpoint returns the right user """
        url = reverse('user-detail', kwargs={'slug': self.users[0].slug})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['username'], self.users[0].username)

    def test_delete_user(self):
        """ Tests if the user delete endpoint works """
        url = reverse('user-delete')

        user = self.users[0]

        self.client.force_authenticate(user)
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=user.id).exists())

    def test_update_user_profile(self):
        """ Tests if the user update profile endpoint works """

        url = reverse('user-profile-update')

        user = self.users[0]
        original_avatar = self.users[0].avatar

        new_display_name = fake.first_name()
        avatar_fp = 'C:/dev/cod/backend/media/uploads/avatars/r6.jpg'

        with open(avatar_fp, 'rb') as avatar:
            data = {
                'display_name': new_display_name,
                'description': 'This is a test description.',
                'avatar': avatar
            }

            self.client.force_authenticate(user)
            response = self.client.patch(url, data, format='multipart')

        new_avatar = self.users[0].avatar

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.users[0].display_name, new_display_name)
        self.assertEqual(self.users[0].description, 'This is a test description.')
        self.assertNotEqual(original_avatar, new_avatar)

    def tearDown(self):
        # All of this code may be unecessary, but it works.

        directory = 'C:/dev/cod/backend/media/uploads/avatars'
        preserved_files = ('r6.jpg', 'default_avatar.png',)

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            is_file = (os.path.isfile(file_path) or os.path.islink(file_path))
            try:
                if is_file and filename not in preserved_files:
                    os.unlink(file_path)

            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))


class FollowViewsTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username=fake.first_name(),
            email=fake.email(),
            password=fake.password()
        )

        self.user_2 = User.objects.create_user(
            username=fake.first_name(),
            email=fake.email(),
            password=fake.password()
        )

        self.follow_obj = UserFollowing(
            user_follows=self.user,
            user_followed=self.user_2
        )

    def test_follow_user(self):
        url = reverse('user-follow', kwargs={'slug': self.user_2.slug})

        self.client.force_authenticate(self.user)
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json(), {'details': 'follow successful'})

        self.assertEqual(UserFollowing.objects.count(), 1)
        self.assertEqual(UserFollowing.objects.get().user_follows, self.user)
        self.assertEqual(UserFollowing.objects.get().user_followed, self.user_2)

    def test_unfollow_user(self):
        self.follow_obj.save()
        url = reverse('user-unfollow', kwargs={'slug': self.user_2.slug})

        self.client.force_authenticate(self.user)
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(UserFollowing.objects.count(), 0)

    def test_follow_self(self):
        url = reverse('user-follow', kwargs={'slug': self.user.slug})

        self.client.force_authenticate(self.user)
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'details': 'Can\'t follow yourself'})

    def test_unfollow_self(self):
        url = reverse('user-unfollow', kwargs={'slug': self.user.slug})

        self.client.force_authenticate(self.user)
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'details': 'Can\'t unfollow yourself'})

    def test_already_following(self):
        self.follow_obj.save()
        url = reverse('user-follow', kwargs={'slug': self.user_2.slug})

        self.client.force_authenticate(self.user)
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'details': 'Already following'})

        self.assertEqual(UserFollowing.objects.count(), 1)

    def test_already_not_following(self):
        url = reverse('user-unfollow', kwargs={'slug': self.user_2.slug})

        self.client.force_authenticate(self.user)
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'details': 'You\'re not following that person'})

    def test_follow_invalid_user(self):
        """
        Responds with 404 if the user does not exist (if the slug is invalid).
        """
        url = reverse('user-follow', kwargs={'slug': 'does-not-exist'})

        self.client.force_authenticate(self.user)
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_unfollow_invalid_user(self):
        """
        Responds with 404 if the user does not exist (if the slug is invalid).
        """
        url = reverse('user-unfollow', kwargs={'slug': 'does-not-exist'})

        self.client.force_authenticate(self.user)
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'Not found.'})

    def test_follow_unauthenticated(self):
        """
        Responds with 401 Unauthorized.
        """
        url = reverse('user-follow', kwargs={'slug': self.user_2.slug})

        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.json(),
            {'detail': 'Authentication credentials were not provided.'}
        )

    def test_unfollow_unauthenticated(self):
        """
        Responds with 401 Unauthorized.
        """
        url = reverse('user-unfollow', kwargs={'slug': self.user_2.slug})

        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.json(),
            {'detail': 'Authentication credentials were not provided.'}
        )
