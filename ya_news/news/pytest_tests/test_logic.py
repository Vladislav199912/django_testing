from http import HTTPStatus
from pytest_django.asserts import assertRedirects, assertFormError

from django.urls import reverse
from news.forms import BAD_WORDS, WARNING
from news.models import Comment


def test_user_can_create_comment(db,
                                 author_client,
                                 author,
                                 comment_form_data,
                                 news):
    url = reverse('news:detail', args=(news.id,))
    response = author_client.post(url, data=comment_form_data)
    assertRedirects(response, f'{url}#comments')
    assert Comment.objects.count() == 1
    new_comment = Comment.objects.get()
    assert new_comment.text == comment_form_data['text']
    assert new_comment.news == news
    assert new_comment.author == author


def test_anonymous_user_cant_create_comment(db,
                                            client,
                                            comment_form_data,
                                            id_for_news):

    url = reverse('news:detail', args=(id_for_news))
    response = client.post(url, data=comment_form_data)
    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={url}'
    assertRedirects(response, expected_url)
    assert Comment.objects.count() == 0


def test_not_bad_words(author_client, comment_form_data, news,):
    url = reverse('news:detail', args=(news.id,))
    comment_form_data['text'] = f'Текст {BAD_WORDS[0]} еще текст'
    response = author_client.post(url, data=comment_form_data)
    assertFormError(response,
                    form='form',
                    field='text',
                    errors=WARNING)
    assert Comment.objects.count() == 0


def test_author_can_edit_comment(author_client,
                                 comment_form_data,
                                 comment,
                                 id_for_comment,
                                 news,
                                 author):
    url = reverse('news:edit', args=(id_for_comment))
    response = author_client.post(url, comment_form_data)
    url_add = reverse('news:detail', args=(id_for_comment))
    assertRedirects(response, f'{url_add}#comments')
    comment.refresh_from_db()
    assert comment.text == comment_form_data['text']
    assert comment.news == news
    assert comment.author == author


def test_other_user_cant_edit_comment(db,
                                      admin_client,
                                      comment_form_data,
                                      news,
                                      comment,
                                      id_for_comment,
                                      author):
    url = reverse('news:edit', args=(id_for_comment))
    response = admin_client.post(url, comment_form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment_from_db = Comment.objects.get(id=comment.id)
    assert comment.text == comment_from_db.text
    assert comment.news == news
    assert comment.author == author


def test_author_can_delete_comment(author_client, id_for_comment, id_for_news):
    url = reverse('news:delete', args=(id_for_comment))
    response = author_client.post(url)
    url_add = reverse('news:detail', args=(id_for_news))
    assertRedirects(response, f'{url_add}#comments')
    assert Comment.objects.count() == 0


def test_other_user_cant_delete_comment(admin_client, id_for_comment):
    url = reverse('news:delete', args=(id_for_comment))
    response = admin_client.post(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == 1
