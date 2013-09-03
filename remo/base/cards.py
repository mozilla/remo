import libxml2
import tempfile
import os
import commands

from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

template_front = 'media/img/remo/remo_card_front.svg'
template_back = 'media/img/remo/remo_card_back.svg'


def prepare_data(user):
    display_name = user.userprofile.display_name
    user = get_object_or_404(User,
                             userprofile__display_name__iexact=display_name)

    data = {}
    data['fullname'] = '%s %s' % (user.first_name, user.last_name)
    data['bugzillamail'] = user.email
    data['twitter'] = user.userprofile.twitter_account
    data['irc'] = user.userprofile.irc_name
    data['website'] = user.userprofile.personal_website_url

    for key in data.keys():
        namekey = '%s-name' % key
        data[namekey] = key

    return data


def parse_svg(svg, output, *args, **kwargs):
    with open(svg, 'r') as content_file:
        content = content_file.read()
    svgdoc = libxml2.parseDoc(content)

    # set default values for data
    for node in svgdoc.xpathEval("//*[@default]"):
        node.setContent(node.hasProp("default").content)

    # set values for user
    for key in kwargs.keys():
        try:
            field = svgdoc.xpathEval("//*[@id='%s']" % key)[0]
        except IndexError:
            # we didn't find the key, ignore
            continue

        content = ''
        if field.hasProp("prepend"):
            content += field.hasProp("prepend").content

        content += kwargs[key]

        if field.hasProp("append"):
            content += field.hasProp("append").content

        field.setContent(content)

    # force lowercase to fields with force_lowercase attribute
    for node in svgdoc.xpathEval("//*[@force_lowercase]"):
        node.setContent(node.content.lower())

    output.write(str(svgdoc))
    output.close()


def svg2pdf(svgfile, output):
    svgfile.close()
    output.close()
    COMMAND = "rsvg-convert -f pdf '%s' > '%s'"
    status, output = commands.getstatusoutput(COMMAND %
                                              (svgfile.name, output.name))


class TempFile:
    def __init__(self):
        self.fd, self.filename = tempfile.mkstemp()
        self.file = os.fdopen(self.fd, 'w+b')

    @property
    def name(self):
        return self.filename

    def read(self, size=-1):
        return self.file.read(size)

    def seek(self, where):
        return self.file.seek(where)

    def tell(self):
        return self.file.tell()

    def write(self, what):
        return self.file.write(what)

    def close(self):
        return self.file.close()

    def delete(self):
        self.file.close()
        try:
            os.unlink(self.filename)
        except:
            pass


def send_card(user):
    svg_back = TempFile()
    svg_front = TempFile()
    pdf_front = TempFile()
    pdf_back = TempFile()

    # data
    data = prepare_data(user)

    # generate svg
    parse_svg(template_back, svg_back, **data)
    parse_svg(template_front, svg_front, **data)

    # generate pdf
    svg2pdf(svg_front, pdf_front)
    svg2pdf(svg_back, pdf_back)

    # email pdf
    email = EmailMessage('Your Mozilla Reps Business Card',
                         "Hi!\n\nEnjoy your new Mozilla Reps Business Card ;)"
                         "\n\nBest regards,\nThe ReMo bot\n",
                         'no-reply@mozillareps.org',  # from
                         [user.email],  # to
                         )
    email.attach('card-front.pdf', open(pdf_front.name).read(),
                 'application/pdf')
    email.attach('card-back.pdf', open(pdf_back.name).read(),
                 'application/pdf')
    email.send()

    #try:
    #    svg_back.delete()
    #    svg_front.delete()
    #    pdf_back.delete()
    #    pdf_front.delete()
    #except:
    #    pass

    data = "Check your inbox for your business card!"

    return data
