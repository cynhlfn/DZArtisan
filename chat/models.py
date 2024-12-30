from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserRelation(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user_relations"
    )
    friend = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="friend_relations", default=None
    )
    accepted = models.BooleanField(default=False)
    relation_key = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'chat_userrelation'  # Matches the table name created in pgAdmin
        managed = False  # Prevent Django from managing this table
        unique_together = ('user', 'friend')  # Ensures unique user-friend pairs

    def __str__(self):
        return f"{self.user.username} - {self.friend.username}"


class Messages(models.Model):
    description = models.TextField()
    sender_name = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sender"
    )
    receiver_name = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="receiver"
    )
    time = models.TimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now, blank=True)

    class Meta:
        db_table = 'chat_messages'  # Matches the table name created in pgAdmin
        managed = False  # Prevent Django from managing this table
        ordering = ("timestamp",)

    def __str__(self):
        return f"From {self.sender_name} to {self.receiver_name} at {self.timestamp}"
