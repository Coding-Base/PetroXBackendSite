# updates/models.py
from django.conf import settings
from django.db import models
from django.utils import timezone


User = settings.AUTH_USER_MODEL


class Update(models.Model):
# blog/announcement
title = models.CharField(max_length=255)
slug = models.SlugField(max_length=255, unique=True)
body = models.TextField() # consider markdown
author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updates')
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
published = models.BooleanField(default=True)
featured_image = models.ImageField(upload_to='updates/', null=True, blank=True)


class Meta:
ordering = ['-created_at']


def __str__(self):
return self.title


class Comment(models.Model):
update = models.ForeignKey(Update, on_delete=models.CASCADE, related_name='comments')
user = models.ForeignKey(User, on_delete=models.CASCADE)
parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)
body = models.TextField()
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)


class Meta:
ordering = ['created_at']


def is_root(self):
return self.parent is None


class Like(models.Model):
user = models.ForeignKey(User, on_delete=models.CASCADE)
# generic relation if you want to like comments too. Simpler: likes only for Update for now
update = models.ForeignKey(Update, on_delete=models.CASCADE, related_name='likes')
created_at = models.DateTimeField(auto_now_add=True)


class Meta:
unique_together = ('user', 'update')


class UpdateReadState(models.Model):
user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='update_states')
update = models.ForeignKey(Update, on_delete=models.CASCADE)
viewed = models.BooleanField(default=False)
viewed_at = models.DateTimeField(null=True, blank=True)


class Meta:
unique_together = ('user', 'update')