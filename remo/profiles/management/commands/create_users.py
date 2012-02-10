import sys
from optparse import make_option

from django.contrib.auth.models import User
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.validators import email_re
from django.core.mail import send_mail
# alphabetize imports

from django_browserid.auth import default_username_algo

# If this is a constant, capitalize all letters
username_algo = getattr(settings, 'BROWSERID_USERNAME_ALGO',
                        default_username_algo)

class Command(BaseCommand):
    # Missing comment
    args = '<user_list.txt>'
    help = 'Create new users from file'
    option_list = list(BaseCommand.option_list) + [
        make_option('--no-email',
                    action='store_false',
                    dest='email',
                    default=True,
                    help='Do not send invitation emails'
                    )
        ] # Move square bracket and parenthesis to the end of help='..'

    FROM_EMAIL = "reps@mozilla.com"
    SUBJECT = "Welcome to ReMo Portal"
    MESSAGE = "Welcome to ReMo Portal!\n\n"\
              "Please visit our website and login with BrowserID."\
              "We already created an account for you!\n\n"\
              "Enjoy,\n"\
              "Mozilla Reps WebDev Team"


    def handle(self, *args, **options):
        # Missing comment
        if len(args) != 1:
            print "Please provide a file with emails.\n"
            sys.exit(-1)

        with open(args[0], "r") as input_file:
            for email in input_file:
                email = email.strip()

                if not email_re.match(email):
                    print "Email '%s' is not valid, ignoring.\n" % email,
                    continue

                # create account <-- I think this is self explanatory so this comment is
                # not required.
                User.objects.create_user(username=username_algo(email),
                                         email=email)

                # send invitation email
                if options['email']:
                    # send
                    send_mail(self.SUBJECT, self.MESSAGE,
                              self.FROM_EMAIL, [email])
