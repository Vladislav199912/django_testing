from http import HTTPStatus
from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import WARNING


User = get_user_model()


class TestLogic(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Author')
        cls.user = User.objects.create(username='User')
        cls.url = reverse('notes:add')
        cls.note = Note.objects.create(title='Заголовок',
                                       text='text',
                                       author=cls.author)
        cls.form_data = {
            'title': 'Другой заголовок',
            'text': 'Другой текст',
            'slug': 'another_slug'
        }

    def test_anonymous_user_cant_create_note(self):
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_auth_user_can_create_note(self):
        self.client.force_login(self.author)
        response = self.client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        new_note = Note.objects.last()
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(Note.objects.count(), 2)

    def test_empty_slug(self):
        self.form_data.pop('slug')
        self.client.force_login(self.author)
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 2)
        new_note = Note.objects.last()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_not_unique_slug(self):
        self.form_data['slug'] = self.note.slug
        self.client.force_login(self.author)
        response = self.client.post(self.url, data=self.form_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=(self.note.slug + WARNING)
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        url = reverse('notes:edit', args=(self.note.slug,))
        self.client.force_login(self.author)
        response = self.client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        update_note = Note.objects.get(id=self.note.id)
        self.assertEqual(update_note.title, self.form_data['title'])
        self.assertEqual(update_note.text, self.form_data['text'])
        self.assertEqual(update_note.slug, self.form_data['slug'])
        self.assertEqual(update_note.author, self.author)

    def test_author_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        self.client.force_login(self.author)
        response = self.client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_cant_edit_note(self):
        url = reverse('notes:edit', args=(self.note.slug,))
        self.client.force_login(self.user)
        response = self.client.post(url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        existing_note = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, existing_note.title)
        self.assertEqual(self.note.text, existing_note.text)
        self.assertEqual(self.note.slug, existing_note.slug)

    def test_user_cant_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        self.client.force_login(self.user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)
