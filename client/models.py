import uuid

from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profilev2')
    about = models.TextField(blank=True, null=True)
    profile_picture = models.CharField(blank=True, null=True, max_length=255)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Chat(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)  # Unique ID for each chat
    name = models.CharField(max_length=255, null=True, blank=True)  # Only for group chats
    description = models.CharField(max_length=255, null=True, blank=True)  # Only for group chats
    is_group = models.BooleanField(default=False)  # Flag to indicate whether it's a group chat
    created_by = models.OneToOneField(User, on_delete=models.CASCADE, related_name='group_creator', blank=True,
                                      null=True)
    users = models.ManyToManyField(User, related_name='chatsv2')  # Users involved in this chat
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of when the chat was created
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True)  # Image for the chat (optional)

    def __str__(self):
        return self.name if self.is_group else "Private Chat"

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name if self.is_group else f'1-on-1 with {", ".join([user.username for user in self.users.all()])}'


class Message(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Document'),
        ('poll', 'Poll'),
        ('list', 'List'),
        ('button', 'Button'),
        ('flashcard', 'Flashcard'),
        ('location', 'Location'),
        ('sticker', 'Sticker'),
        ('form', 'Form'),
        ('payment', 'Payment'),
        ('system', 'System'),
        ('ephemeral', 'Ephemeral'),
    ]

    chat = models.ForeignKey('Chat', related_name='messagesv2', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='senderv2')
    type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')  # Type of message
    content = models.TextField(null=True, blank=True)  # For text or generic content
    has_media = models.BooleanField(default=False)
    media_url = models.URLField(null=True, blank=True)  # URL for media files (images, videos, audio, etc.)
    is_reply = models.BooleanField(default=False)
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    # Location-specific fields
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Poll-specific fields
    poll_question = models.TextField(null=True, blank=True)
    poll_options = models.JSONField(null=True, blank=True)  # Example: ["Option1", "Option2"]
    poll_responses = models.JSONField(null=True, blank=True)  # Example: {"user1": "Option1", "user2": "Option2"}

    # List-specific field
    list_items = models.JSONField(null=True, blank=True)  # Example: ["Item1", "Item2"]

    # Button-specific field
    button_label = models.CharField(max_length=100, null=True, blank=True)
    button_action = models.URLField(null=True, blank=True)

    # Audio-specific fields
    audio_duration = models.FloatField(null=True, blank=True)

    # Document-specific fields
    document_name = models.CharField(max_length=255, null=True, blank=True)
    document_size = models.IntegerField(null=True, blank=True)

    # Sticker/GIF-specific field
    sticker_url = models.URLField(null=True, blank=True)

    # Payment-specific field
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_currency = models.CharField(max_length=10, null=True, blank=True)
    payment_link = models.URLField(null=True, blank=True)

    # Ephemeral-specific fields
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Message ({self.type}) from {self.sender.username} in {self.chat.name}'


class MessageReaction(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_reactions')
    reaction = models.CharField(max_length=10)  # Store emoji or reaction type (e.g., 'thumbs_up', 'heart')

    def __str__(self):
        return f'Reaction ({self.reaction}) by {self.user.username} on Message {self.message.id}'
