import re
import datetime

from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.core.exceptions import ValidationError

def _validate_birth_date(data, **kwargs):
    today = datetime.date.today()
    youth_threshold_day = datetime.date(today.year-12, today.month, today.day)+\
                          datetime.timedelta(hours=24)

    maturity_threshold_day = datetime.date(today.year-90, today.month, today.day)-\
                             datetime.timedelta(hours=24)

    if data < youth_threshold_day and data > maturity_threshold_day:
        return data

    else:
        raise ValidationError("Provided Birthdate is not valid")


def _validate_twitter_username(data, **kwargs):
    if re.match(r'@([A-Za-z0-9_]+)', data):
        return data

    else:
        raise ValidationError("Provided Twitter Username is not valid")


def _validate_gpg_keyid(data, **kwargs):
    if re.match(r'0x[A-Fa-f0-9]{8}$', data):
        return data

    else:
        raise ValidationError("Provided GPG KeyID is not valid")


def _validate_mozillians_url(data, **kwargs):
    if re.match(r'http(s)?://(www.)?mozillians.org/', data):
        return data

    else:
        raise ValidationError("Provided Mozillians url is not valid")


def _validate_linkedin_url(data, **kwargs):
    if re.match(r'http(s)?://(www.)?linkedin.com/', data):
        return data

    else:
        raise ValidationError("Provided LinkedIn url is not valid")


def _validate_facebook_url(data, **kwargs):
    if re.match(r'http(s)?://(www.)?facebook.com/', data):
        return data

    else:
        raise ValidationError("Provided Facebook url is not valid")


class IRCChannel(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=300)

    def __unicode__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    birth_date = models.DateField(validators=[_validate_birth_date])
    city = models.CharField(max_length=30, blank=True)
    region = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=30, blank=False)
    lon = models.FloatField(blank=True, null=True)
    lat = models.FloatField(blank=True, null=True)
    display_name = models.CharField(max_length=15, blank=True, null=False)
    private_email = models.EmailField(blank=True, null=True)
    private_email_visible = models.BooleanField(default=True)
    mozillians_profile_url = models.URLField(validators=
                                             [_validate_mozillians_url])
    twitter_account = models.CharField(max_length=16,
                                       validators=[_validate_twitter_username],
                                       blank=True, null=True)
    gpg_key = models.CharField(max_length=10, validators=[_validate_gpg_keyid],
                               blank=True, null=True)
    irc_name = models.CharField(max_length=30, blank=True, null=True)
    irc_channels = models.ManyToManyField(IRCChannel)
    linkedin_url = models.URLField(blank=True, null=True,
                                   validators=[_validate_linkedin_url])
    facebook_url = models.URLField(blank=True, null=True,
                                   validators=[_validate_facebook_url])
    diaspora_url = models.URLField(blank=True, null=True)
    personal_website_url = models.URLField(blank=True, null=True)
    personal_blog_feed = models.URLField(blank=True, null=True)


    @property
    def is_private_email_visible(self):
        return self.private_email_visible


    def join_group(self, group_name):
        try:
            group = Group.objects.get(name=group_name)

        except Group.DoesNotExist:
            raise ValueError("Group %s does not exist" % group_name)

        if group in self.user.groups.iterator():
            raise ValueError("User already in %s group" % group_name)

        else:
            group.user_set.add(self.user)


    def leave_group(self, group_name):
        try:
            group = Group.objects.get(name=group_name)

        except Group.DoesNotExist:
            raise ValueError("Group %s does not exist" % group_name)

        if group not in self.user.groups.iterator():
            raise ValueError("User not in %s group" % group_name)

        else:
            group.user_set.remove(self.user)


    def join_irc_channel(self, channel_name):
        channel, created = IRCChannel.objects.get_or_create(name=channel_name.lower())
        if created:
            channel.save()

        if channel in self.irc_channels.iterator():
            raise ValueError("User already in channel %s" % channel_name)

        else:
            self.irc_channels.add(channel)


    def leave_irc_channel(self, channel_name):
        try:
            channel = IRCChannel.objects.get(name=channel_name.lower())

        except IRCChannel.DoesNotExist:
            raise ValueError("Channel %s does not exist" % channel_name)

        if channel not in self.irc_channels.iterator():
            raise ValueError("User not in channel %s" % channel_name)

        else:
            self.irc_channels.remove(channel)


def userprofile_set_display_name_pre_save(sender, instance, **kwargs):
    """
    Set display_name from user.username if display_name == ''
    """
    if not instance.display_name:
        instance.display_name = instance.user.username

models.signals.pre_save.connect(userprofile_set_display_name_pre_save,
                                sender=UserProfile)


def userprofile_set_active_post_save(sender, instance, created, **kwargs):
    """
    Set user active if UserProfile get's created
    """
    if created:
        instance.user.is_active = True
        instance.user.save()

models.signals.post_save.connect(userprofile_set_active_post_save,
                                 sender=UserProfile)


def user_set_inactive_pre_save(sender, instance, **kwargs):
    """
    Set user inactive if there is no associated UserProfile
    """
    try:
        instance.get_profile()

    except UserProfile.DoesNotExist:
        instance.is_active = False

models.signals.pre_save.connect(user_set_inactive_pre_save,
                                sender=User)
