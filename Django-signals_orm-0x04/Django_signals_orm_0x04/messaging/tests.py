# messaging/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Message, Notification

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

        # update the message - should NOT create another notification
        message.content = 'Edited'
        message.save()
        self.assertEqual(Notification.objects.filter(user=self.receiver, message=message).count(), 1)
