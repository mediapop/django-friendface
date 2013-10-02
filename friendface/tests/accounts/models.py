from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    facebook = models.OneToOneField('friendface.FacebookUser',
                                    blank=True,
                                    null=True)

@receiver(post_save, sender=User, dispatch_uid='create_profile')
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
