import sys
from optparse import make_option

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.core.validators import email_re
from django.contrib.auth.models import User

from django_browserid.auth import default_username_algo

USERNAME_ALGO = getattr(settings, 'BROWSERID_USERNAME_ALGO',
                        default_username_algo)


class Command(BaseCommand):
    """ Command to create users massivelly.

    This command creates users from a file. The list must contain an
    email per line.
    """
    args = '<user_list.txt>'
    help = 'Create new users from file'
    option_list = list(BaseCommand.option_list) + [
        make_option('--no-email',
                    action='store_false',
                    dest='email',
                    default=True,
                    help='Do not send invitation emails')]

    FROM_EMAIL = "reps@mozilla.com"
    SUBJECT = "Welcome to ReMo Portal"
    MESSAGE = "Welcome to ReMo Portal!\n\n"\
              "Please visit our website and login with BrowserID."\
              "We already created an account for you!\n\n"\
              "Enjoy,\n"\
              "Mozilla Reps WebDev Team"


    def handle(self, *args, **options):
        """
        Read emails from text file and create accounts. If
        options['email'] is set then send out emails to invited users.
        """
        if len(args) != 1:
            print "Please provide a file with emails.\n"
            sys.exit(-1)

        with open(args[0], "r") as input_file:
            for email in input_file:
                email = email.strip()

                if not email_re.match(email):
                    print "Email '%s' is not valid, ignoring.\n" % email,
                    continue

                User.objects.create_user(username=USERNAME_ALGO(email),
                                         email=email)

                # Send invitation email if option is True. Default (yes)
                if options['email']:
                    send_mail(self.SUBJECT, self.MESSAGE,
                              self.FROM_EMAIL, [email])
