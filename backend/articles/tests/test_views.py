import random
import os

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
import faker

from ..models import Tag, Article, ArticleLike, Comment, CommentVote
from ..serializers.article_serializers import ArticleSerializer


fake = faker.Faker('en')
User = get_user_model()


class ArticleTagViewsTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username=fake.first_name(),
            email=fake.email(),
            password=fake.password()
        )

        self.article = Article.objects.create(
            title='Test',
            content="test 123",
            user=self.user,
        )

        tag_names = ['javascript', 'python', 'vue', 'frontend', 'backend', 'docker']
        self.tags = []
        for name in tag_names:
            self.tags.append(Tag.objects.create(name=name))

    def test_create_article_with_tags(self):
        """ Creates an article with tags. """
        url = reverse('article-list')

        data = {
            'title': 'Test_123',
            'content': 'Test_content_123',
            'tags': ['javascript', 'frontend', 'vue']
        }

        self.client.force_authenticate(self.user)
        response = self.client.post(url, data, format='json')

        article_obj = Article.objects.get(pk=response.json()['id'])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(article_obj.tags.count(), 3)

    def test_remove_one_tag_from_article(self):
        """ Remove one tag from an article. """
        url = reverse('article-detail', kwargs={'slug': self.article.slug})

        data = {'tags': ['python', 'vue']}

        self.article.tags.set((self.tags[2].id, self.tags[3].id, self.tags[5].id,))

        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.article.tags.count(), 2)

    def test_maximum_tags_validation_on_create(self):
        """ Throws an error when trying to add more than 5 tags on creation. """
        url = reverse('article-list')

        data = {
            'title': 'Test_123',
            'content': 'Test_content123',
            'tags': ['javascript', 'python', 'vue', 'frontend', 'backend', 'docker']
        }

        self.client.force_authenticate(self.user)
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'details': 'You can\'t assign more than five tags'})

    def test_maximum_tags_validation_on_put(self):
        """ Throws an error when trying to add more than 5 tags on update. """
        url = reverse('article-detail', kwargs={'slug': self.article.slug})

        data = {'tags': ['javascript', 'python', 'vue', 'frontend', 'backend', 'docker']}

        self.article.tags.set((2, 3, 6))

        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'details': 'You can\'t assign more than five tags'})

    def test_article_removed_from_tag_relationship(self):
        """ Articles gets removed from tag correctly when deleting. """
        url = reverse('article-detail', kwargs={'slug': self.article.slug})

        self.article.tags.add(1)

        self.client.force_authenticate(self.user)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Tag.objects.get(pk=self.tags[1].id).articles.count(), 0)


class ArticleViewsTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username=fake.first_name(),
            email=fake.email(),
            password=fake.password()
        )

        self.user_2 = User.objects.create_user(
            username=fake.first_name() + '0',
            email=fake.email(),
            password=fake.password()
        )

        self.draft_user = User.objects.create_user(
            username='draft_user',
            email='draft_test@gmail.com',
            password='12345'
        )

        self.article = Article.objects.create(
            title='Test title',
            content='This is the content',
            user=self.user
        )

        self.draft_article = Article.objects.create(
            title='Test draft title',
            content='Content',
            draft=True,
            user=self.draft_user
        )

    def test_create_article_authorized(self):
        """ Creates an article. """
        url = reverse('article-list')

        data = {
            'title': 'Test title',
            'content': 'This is the content'
        }

        self.client.force_authenticate(self.user)
        response = self.client.post(url, data, format='json')

        article_id = response.json()['id']

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Article.objects.count(), 2)
        self.assertEqual(Article.objects.get(pk=article_id).user, self.user)

    def test_create_article_unauthorized(self):
        """
        can't create an article because
        the user isn't logged in.
        """
        url = reverse('article-list')

        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_article_draft(self):
        """ Creates an article as a draft. """
        url = reverse('article-list')

        data = {
            'title': 'Test title. draft',
            'content': 'This is the draft content',
            'draft': True
        }

        self.client.force_authenticate(self.user)
        response = self.client.post(url, data, format='json')

        article_id = response.json()['id']

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Article.drafts.get(pk=article_id).user, self.user)

    def test_create_article_with_thumbnail(self):
        """ Creates an article with a thumbnail. """
        url = reverse('article-list')

        with open('media/uploads/thumbnails/test_thumbnail.png', 'rb') as thumbnail:
            data = {
                'title': 'Test title',
                'content': 'This is the content',
                'thumbnail': thumbnail
            }

            self.client.force_authenticate(self.user)
            response = self.client.post(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(Article.objects.get(pk=response.json()['id']).thumbnail)

    def test_create_article_without_thumbnail(self):
        """ Create an article without a thumbnail. """
        url = reverse('article-list')

        data = {
            'title': 'Test title',
            'content': 'This is the content'
        }

        self.client.force_authenticate(self.user)
        response = self.client.post(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_articles(self):
        """ Gets all articles that aren't drafts. """
        url = reverse('article-list')

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_article_saved_count(self):
        """ Displays the total amount of saves the article has. """
        url = reverse('article-detail', kwargs={'slug': self.article.slug})

        self.user.saved_articles.add(self.article)

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['saved_count'], self.article.saves.count())

    def test_get_detail_article(self):
        """ Gets the full article. """
        url = reverse('article-detail', kwargs={'slug': self.article.slug})

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_own_article(self):
        """ Can update the user's own article. """
        url = reverse('article-detail', kwargs={'slug': self.article.slug})

        data = {
            'title': 'Test title, updated',
            'content': 'This is the NEW content'
        }

        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Article.objects.get(pk=self.article.id).title, data['title'])
        self.assertEqual(Article.objects.get(pk=self.article.id).content, data['content'])

    def test_update_other_article(self):
        """ Can't update someone else's article. """
        url = reverse('article-detail', kwargs={'slug': self.article.slug})

        data = {
            'title': 'Test title, updated',
            'content': 'This is the NEW content'
        }

        self.client.force_authenticate(self.user_2)
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_article(self):
        """ Can delete the user's own article. """
        url = reverse('article-detail', kwargs={'slug': self.article.slug})

        self.client.force_authenticate(self.user)
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_other_article(self):
        """ Can't delete someone else's article. """
        url = reverse('article-detail', kwargs={'slug': self.article.slug})

        self.client.force_authenticate(self.user_2)
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_draft_details_authorized(self):
        """ Returns the draft article becuase the user is the owner. """
        url = reverse('article-detail', kwargs={'slug': self.draft_article.slug})

        self.client.force_authenticate(self.draft_user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['title'], self.draft_article.title)

    def test_get_draft_details_unauthorized(self):
        """ Doesn't return the draft article becuase the user isn't the owner. """
        url = reverse('article-detail', kwargs={'slug': self.draft_article.slug})

        self.client.force_authenticate(self.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_drafts_authorized(self):
        """ Retrieves all the user's drafts """
        url = reverse('article-drafts')

        self.client.force_authenticate(self.draft_user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_list_drafts_unauthenticated(self):
        """ Responds with 401. """
        url = reverse('article-drafts')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_only_own_drafts(self):
        """ Retrieves all the user's drafts. (ensures that it's only theirs) """
        url = reverse('article-drafts')

        for _ in range(3):
            Article.objects.create(
                title='test draft title',
                content='test content',
                draft=True,
                user=self.user
            )

        self.client.force_authenticate(self.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            ArticleSerializer(Article.drafts.filter(user=self.user), many=True).data
        )

    def tearDown(self):
        # All of this code may be unecessary, but it works.

        directory = os.path.abspath('media/uploads/thumbnails/')
        preserved_files = ('test_thumbnail.png',)

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            is_file = (os.path.isfile(file_path) or os.path.islink(file_path))
            try:
                if is_file and filename not in preserved_files:
                    os.unlink(file_path)

            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))


class ArticleSaveViewsTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username=fake.first_name(),
            email=fake.email(),
            password=fake.password()
        )

        self.owner = User.objects.create_user(
            username=fake.first_name() + '0',
            email=fake.email(),
            password=fake.password()
        )

        self.article = Article.objects.create(
            title='Test title',
            content='This is the content',
            user=self.owner
        )

    def test_save_article(self):
        """ The user can save an article. """
        url = reverse('article-save', kwargs={'slug': self.article.slug})

        self.client.force_authenticate(self.user)
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'details': 'Saved article.'})

    def test_save_own_article(self):
        """ The user can't save its own article. """
        url = reverse('article-save', kwargs={'slug': self.article.slug})

        self.client.force_authenticate(self.owner)
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {'details': 'You can\'t save your own article.'})

    def test_save_twice(self):
        """ Can save an article twice. """
        url = reverse('article-save', kwargs={'slug': self.article.slug})

        self.client.force_authenticate(self.user)
        self.client.post(url, format='json')

        self.client.force_authenticate(self.user)
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'details': 'You have already saved this article.'})

    def test_unsave(self):
        """ Can unsave an article. """
        url = reverse('article-unsave', kwargs={'slug': self.article.slug})

        self.user.saved_articles.add(self.article)

        self.client.force_authenticate(self.user)
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(self.user.saved_articles.count(), 0)

    def test_unsave_twice(self):
        """ Can't unsave an article twice. """
        url = reverse('article-unsave', kwargs={'slug': self.article.slug})

        self.user.saved_articles.add(self.article)

        self.client.force_authenticate(self.user)
        self.client.delete(url, format='json')

        self.client.force_authenticate(self.user)
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'details': 'You must save before you can unsave.'})

        self.assertEqual(self.user.saved_articles.count(), 0)

    def test_unsave_own_article(self):
        """ The user can't unsave its own article. """
        url = reverse('article-unsave', kwargs={'slug': self.article.slug})

        self.client.force_authenticate(self.owner)
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {'details': 'You can\'t unsave your own post.'})


class ArticleLikeViewsTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username=fake.first_name(),
            email=fake.email(),
            password=fake.password()
        )

        self.owner = User.objects.create_user(
            username=fake.first_name() + '0',
            email=fake.email(),
            password=fake.password()
        )

        self.article = Article.objects.create(
            title='Test title',
            content='This is the content',
            user=self.owner
        )

        self.article_2 = Article.objects.create(
            title='Test title',
            content='This is the content',
            user=self.owner
        )

        self.like = ArticleLike(
            user=self.user,
            article=self.article
        )

        self.like_2 = ArticleLike(
            user=self.user,
            article=self.article_2
        )

        self.special_like = ArticleLike(
            special_like=True,
            user=self.user,
            article=self.article
        )

        self.special_like_2 = ArticleLike(
            special_like=True,
            user=self.user,
            article=self.article_2
        )

    def test_like_article(self):
        """ Likes an article. """
        url = reverse('article-like', kwargs={'slug': self.article.slug})

        self.client.force_authenticate(self.user)
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json(), {'details': 'Liked article.'})

        self.assertEqual(ArticleLike.objects.filter(special_like=False).count(), 1)
        self.assertEqual(ArticleLike.objects.get().user, self.user)
        self.assertEqual(ArticleLike.objects.get().article, self.article)

    def test_cannot_like_unauthenticated(self):
        """ Can't like a article if not logged in. """
        url = reverse('article-like', kwargs={'slug': self.article.slug})

        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_special_like_article(self):
        """ Special likes an article. """
        url = reverse('article-like', kwargs={'slug': self.article.slug})

        data = {'special_like': True}

        self.client.force_authenticate(self.user)
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json(), {'details': 'Superliked article.'})

        self.assertEqual(ArticleLike.objects.filter(special_like=True).count(), 1)
        self.assertEqual(ArticleLike.objects.get().user, self.user)
        self.assertEqual(ArticleLike.objects.get().article, self.article)

    def test_article_cannot_be_found(self):
        """ Can't like an article that doesn't exist. """
        url = reverse('article-like', kwargs={'slug': 'invalid_slug'})

        self.client.force_authenticate(self.user)
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_cannot_like(self):
        """ Can't like your own article. """
        url = reverse('article-like', kwargs={'slug': self.article.slug})

        self.client.force_authenticate(self.owner)
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {'details': 'Can\'t like your own post.'})

        self.assertEqual(ArticleLike.objects.filter(special_like=False).count(), 0)

    def test_owner_cannot_special_like(self):
        """ Can't special like your own article. """
        url = reverse('article-like', kwargs={'slug': self.article.slug})

        data = {'special_like': True}

        self.client.force_authenticate(self.owner)
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {'details': 'Can\'t like your own post.'})

        self.assertEqual(ArticleLike.objects.filter(special_like=True).count(), 0)

    def test_cannot_like_twice(self):
        """ Can't like an article twice. """
        url = reverse('article-like', kwargs={'slug': self.article.slug})

        self.client.force_authenticate(self.user)
        self.client.post(url, format='json')

        self.client.force_authenticate(self.user)
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'details': 'Can\'t like twice.'})

        self.assertEqual(ArticleLike.objects.filter(special_like=False).count(), 1)
        self.assertEqual(ArticleLike.objects.get().user, self.user)

    def test_cannot_special_like_twice(self):
        """ Can't special like an article twice. """
        url = reverse('article-like', kwargs={'slug': self.article.slug})

        data = {'special_like': True}

        self.client.force_authenticate(self.user)
        self.client.post(url, data, format='json')

        self.client.force_authenticate(self.user)
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'details': 'Can\'t special like twice.'})

        self.assertEqual(ArticleLike.objects.filter(special_like=True).count(), 1)
        self.assertEqual(ArticleLike.objects.get().user, self.user)

    def test_unlike(self):
        """ Unlikes an article. """
        url = reverse('article-unlike', kwargs={'slug': self.article.slug})
        self.like.save()

        self.client.force_authenticate(self.user)
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ArticleLike.objects.filter(special_like=False).count(), 0)

    def test_cannot_unlike_unauthenticated(self):
        """ Can't unlikes an article because the user isn't logged in. """
        url = reverse('article-unlike', kwargs={'slug': self.article.slug})
        self.like.save()

        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unlike_special_like(self):
        """ Unlikes a special like. """
        url = reverse('article-unlike', kwargs={'slug': self.article.slug})
        self.special_like.save()

        data = {'special_like': True}

        self.client.force_authenticate(self.user)
        response = self.client.delete(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ArticleLike.objects.filter(special_like=True).count(), 0)


class CommentViewsTest(APITestCase):
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

        self.article = Article.objects.create(
            title='Test title',
            content='This is the content',
            user=self.user
        )

        self.comment = Comment(
            body='TestComment',
            article=self.article,
            user=self.user
        )

    def test_create_comment_authorized(self):
        """ User can comment because the user is logged in. """
        url = reverse('comment-list')

        data = {
            'body': 'Test Comment',
            'article': self.article.id
        }

        self.client.force_authenticate(self.user)
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(self.article.comments.count(), 1)
        self.assertEqual(self.article.comments.get().body, 'Test Comment')
        self.assertEqual(self.article.comments.get().parent, None)

    def test_create_comment_unauthorized(self):
        """ User can't comment because the user isn't logged in. """
        url = reverse('comment-list')

        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_article_comments(self):
        """ Gets all comments on an article. """
        url = reverse('article-detail', kwargs={'slug': self.article.slug})

        for _ in range(2):
            Comment.objects.create(
                body='TestComment',
                article=self.article,
                user=self.user
            )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_own_comment(self):
        """ User can delete its own comment. """
        self.comment.save()
        url = reverse('comment-detail', kwargs={'pk': self.comment.id})

        self.client.force_authenticate(self.user)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.article.comments.get().body, 'deleted')

    def test_delete_other_comment(self):
        """ User can't delete someone else's comment. """
        self.comment.save()
        url = reverse('comment-detail', kwargs={'pk': self.comment.id})

        self.client.force_authenticate(self.user_2)
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_create_child_with_another_article_id(self):
        """ Can't reply to a comment on another article, from another article. """
        url = reverse('comment-list')

        article_2 = Article.objects.create(
            title='title',
            content='content',
            user=self.user
        )

        parent_comment = Comment.objects.create(
            body='Parent comment',
            user=self.user,
            article=self.article
        )

        data = {
            'body': 'Test Comment',
            'article': article_2.id,
            'parent': parent_comment.id
        }

        self.client.force_authenticate(self.user)
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            response.json(),
            {'non_field_errors': ['Parent comment must have the same article id']}
        )

    def test_create_child_comment(self):
        """ Creates a reply (child comment). """
        self.comment.save()
        # Comment.objects.create(body='2', article=self.article, user=self.user)
        url = reverse('comment-list')

        data = {
            'body': 'Test Comment',
            'article': self.article.id,
            'parent': self.comment.id
        }

        self.client.force_authenticate(self.user)
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 2)
        self.assertEqual(self.article.comments.count(), 2)
        self.assertEqual(self.article.comments.get(pk=7).parent, self.comment)


class CommentVoteViewsTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username=fake.first_name(),
            email=fake.email(),
            password=fake.password()
        )

        self.article = Article.objects.create(
            title='Test title',
            content='This is the content',
            user=self.user
        )

        self.comment = Comment.objects.create(
            user=self.user,
            article=self.article
        )

        self.comment_vote = CommentVote(
            user=self.user,
            comment=self.comment
        )

    def test_upvote_comment(self):
        """ Upvotes a comment. """
        url = reverse('comment-vote', kwargs={'pk': self.comment.id})

        self.client.force_authenticate(self.user)
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(CommentVote.objects.filter(downvote=False).count(), 1)
        self.assertEqual(self.comment.comment_votes.count(), 1)
        self.assertEqual(self.comment.score, 1)

    def test_downvote_comment(self):
        """ Downvotes a comment. """
        url = reverse('comment-vote', kwargs={'pk': self.comment.id})

        data = {'downvote': True}

        self.client.force_authenticate(self.user)
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(CommentVote.objects.filter(downvote=True).count(), 1)
        self.assertEqual(self.comment.comment_votes.count(), 1)
        self.assertEqual(self.comment.score, -1)

    def test_delete_comment_vote(self):
        """ Unvotes a comment. """
        url = reverse('comment-vote-delete', kwargs={'pk': self.comment.id})
        self.comment_vote.save()

        self.client.force_authenticate(self.user)
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(CommentVote.objects.filter(downvote=True).count(), 0)
        self.assertEqual(self.comment.comment_votes.count(), 0)
        self.assertEqual(self.comment.score, 0)

    def test_comment_score(self):
        """ Get a comments total score (upvotes - downvotes). """
        url = reverse('comment-detail', kwargs={'pk': self.comment.id})

        for _ in range(5):
            CommentVote.objects.create(
                downvote=bool(random.getrandbits(1)),
                user=self.user,
                comment=self.comment
            )

        upvote_amount = CommentVote.objects.filter(downvote=False).count()
        downvote_amount = CommentVote.objects.filter(downvote=True).count()

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json()['score'], self.comment.score)
        self.assertEqual(response.json()['score'], upvote_amount - downvote_amount)


class FollowTagViewsTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username=fake.first_name(),
            email=fake.email(),
            password=fake.password()
        )

        self.tag = Tag.objects.create(name='Python')

    def test_follow_tag(self):
        """ User starts to follow the tag. """
        url = reverse('tag-follow', kwargs={'slug': self.tag.slug})

        self.client.force_authenticate(self.user)
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json(), {'details': 'Follow successful.'})

    def test_follow_tag_twice(self):
        """ User can't follow a tag twice. """
        url = reverse('tag-follow', kwargs={'slug': self.tag.slug})

        self.tag.followers.add(self.user)

        self.client.force_authenticate(self.user)
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'details': 'Already following.'})

    def test_unfollow_tag(self):
        """ User unfollows the tag. """
        url = reverse('tag-unfollow', kwargs={'slug': self.tag.slug})

        self.tag.followers.add(self.user)

        self.client.force_authenticate(self.user)
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_unfollow_not_followed_tag(self):
        """ User can't unfollow the tag because he hasn't followed it yet. """
        url = reverse('tag-unfollow', kwargs={'slug': self.tag.slug})

        self.tag.followers.remove(self.user)

        self.client.force_authenticate(self.user)
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'details': 'You\'re not following that tag.'})
