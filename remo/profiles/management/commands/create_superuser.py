from optparse import make_option

from django.contrib.auth.models import Group, User
from django.core.management import BaseCommand, CommandError
from django.core.validators import email_re
from django.conf import settings

from django_browserid.auth import default_username_algo

USERNAME_ALGO = getattr(settings, 'BROWSERID_USERNAME_ALGO',
                        default_username_algo)


class Command(BaseCommand):
    """Command to create superuser."""

    option_list = list(BaseCommand.option_list) + [
        make_option('--email',
                    dest='email',
                    default=None,
                    help='You must specify your email'),
        make_option('--password',
                    dest='password',
                    default=None,
                    help='You must specify a password')
    ]

    def handle(self, *args, **options):
        """Create an account with superuser status with the email and
        password provided as input.
        """
        email = options.get('email')
        password = options.get('password')

        if not email or not password:
            raise CommandError('Usage --email your_email '
                               '--password your_password')

        if not email_re.match(email):
            raise CommandError('Please supply a valid email address')

        user, created = User.objects.get_or_create(
            username=USERNAME_ALGO(email), email=email)

        if created:
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.save()

            user.groups.add(Group.objects.get(name='Admin'))
            user.groups.add(Group.objects.get(name='Rep'))
            self.stdout.write('User successfully created')
        else:
            self.stdout.write('A user with this email already '
                              'exists in the database.')
