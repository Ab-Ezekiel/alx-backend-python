# messaging/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Message, Notification, MessageHistory

User = get_user_model()

class MessageNotificationSignalTests(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(username='alice', password='password123')
        self.receiver = User.objects.create_user(username='bob', password='password123')

    def test_notification_created_when_message_is_created(self):
        message = Message.objects.create(sender=self.sender, receiver=self.receiver, content='Hello Bob')
        qs = Notification.objects.filter(user=self.receiver, message=message)
        self.assertTrue(qs.exists())
        notif = qs.first()
        self.assertFalse(notif.is_read)
        self.assertEqual(notif.message, message)
        self.assertEqual(notif.user, self.receiver)

    def test_no_new_notification_on_message_update(self):
        message = Message.objects.create(sender=self.sender, receiver=self.receiver, content='First')
        initial_count = Notification.objects.filter(user=self.receiver, message=message).count()
        self.assertEqual(initial_count, 1)

        # update the message — should NOT create another notification
        message.content = 'Edited'
        message.save()
        self.assertEqual(Notification.objects.filter(user=self.receiver, message=message).count(), 1)

class MessageHistorySignalTests(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(username='charlie', password='password123')
        self.receiver = User.objects.create_user(username='dave', password='password123')

    def test_message_edit_creates_history_and_sets_edited_flag(self):
        message = Message.objects.create(sender=self.sender, receiver=self.receiver, content='Original text')
        # No history initially
        self.assertEqual(MessageHistory.objects.filter(message=message).count(), 0)
        # Edit the message content
        message.content = 'Changed text'
        message.save()
        # A history record should exist with the old content
        history_qs = MessageHistory.objects.filter(message=message)
        self.assertEqual(history_qs.count(), 1)
        history = history_qs.first()
        self.assertEqual(history.old_content, 'Original text')
        # Message should now be flagged as edited
        message.refresh_from_db()
        self.assertTrue(message.edited)

    def test_no_history_created_when_content_unchanged(self):
        message = Message.objects.create(sender=self.sender, receiver=self.receiver, content='Stay same')
        # Save without changing content
        message.save()
        self.assertEqual(MessageHistory.objects.filter(message=message).count(), 0)
