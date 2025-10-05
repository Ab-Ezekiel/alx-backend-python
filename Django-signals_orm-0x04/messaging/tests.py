# messaging/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Message, Notification, MessageHistory
from django.contrib.auth import get_user_model


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


class DeleteUserSignalTests(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(username='u1', password='pass')
        self.u2 = User.objects.create_user(username='u2', password='pass')

    def test_deleting_user_removes_related_messaging_data(self):
        # u1 sends a message to u2 and u2 sends one to u1
        m1 = Message.objects.create(sender=self.u1, receiver=self.u2, content='m1')
        m2 = Message.objects.create(sender=self.u2, receiver=self.u1, content='m2')
        # notifications (created by post_save) exist
        self.assertTrue(Notification.objects.filter(user=self.u2, message=m1).exists())
        self.assertTrue(Notification.objects.filter(user=self.u1, message=m2).exists())

        # Edit a message to create history
        m1.content = 'm1 edited'
        m1.save()
        self.assertTrue(MessageHistory.objects.filter(message=m1).exists())

        # Delete user u1
        self.u1.delete()

        # Ensure messages and notifications related to u1 are removed
        self.assertFalse(Message.objects.filter(pk=m1.pk).exists())
        self.assertFalse(Message.objects.filter(pk=m2.pk).exists())
        self.assertFalse(Notification.objects.filter(message__in=[m1.pk, m2.pk]).exists())
        self.assertFalse(MessageHistory.objects.filter(message__in=[m1.pk, m2.pk]).exists())


class UnreadMessagesManagerTests(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(username='sender', password='pass')
        self.u2 = User.objects.create_user(username='recv', password='pass')
        # create one read and one unread
        Message.objects.create(sender=self.u1, receiver=self.u2, content='unread1', read=False)
        Message.objects.create(sender=self.u1, receiver=self.u2, content='read1', read=True)

    def test_unread_manager_filters_unread_for_user(self):
        qs = Message.unread.for_user(self.u2)
        self.assertEqual(qs.count(), 1)
        m = qs.first()
        self.assertEqual(m.content, 'unread1')
