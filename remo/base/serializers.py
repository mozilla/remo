import codecs
import csv
import cStringIO
import pytz

from datetime import datetime

from django.conf import settings
from django.template import Context
from django.template.loader import get_template
from django.utils import timezone
from tastypie.serializers import Serializer


def flatten_dict(d, base=None):
    """Converts a dictionary of dictionaries or lists into a simple
    dictionary.

    For example the following dictionary

    foobar = {'key1': 'value1',
              'key2': {'skey1': 'svalue1'},
              'key3': ['svalue2', 'svalue3']}

    gets converted to

    foobar = {'key1': 'value1',
              'key2.skey1': 'svalue1',
              'key3.0': 'svalue2',
              'key3.1': 'svalue3'}

    """
    new_dict = {}
    for key, value in d.iteritems():
        if isinstance(value, dict):
            new_base = ''
            if base:
                new_base = '%s.' % base
            new_base += key
            new_dict.update(flatten_dict(value, base=new_base))
        elif isinstance(value, list):
            new_base = ''
            if base:
                new_base += '%s.' % base
            new_base += '%s' % key
            i = 0
            for item in value:
                new_base_index = new_base + '.%d' % i
                if isinstance(item, dict):
                    new_dict.update(flatten_dict(item, base=new_base_index))
                else:
                    new_dict.update({new_base_index: item})
                i += 1
        elif base:
            new_dict.update({'%s.%s' % (base, key): value})
        else:
            new_dict.update({key: value})

    return new_dict


class CSVUnicodeWriter(object):
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.

    Original code from http://docs.python.org/library/csv.html#csv-examples
    Altered by Giorgos Logiotatidis <giorgos@mozilla.com>

    """

    def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        newrow = []
        for s in row:
            newrow.append(unicode(s))

        self.writer.writerow([s.encode('utf-8') for s in newrow])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode('utf-8')
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


class CSVSerializer(Serializer):
    """Extend tastypie's serializer to export to CSV format."""
    formats = ['json', 'jsonp', 'xml', 'yaml', 'html', 'csv']
    content_types = {'json': 'application/json',
                     'jsonp': 'text/javascript',
                     'xml': 'application/xml',
                     'yaml': 'text/yaml',
                     'html': 'text/html',
                     'csv': 'text/csv'}

    def to_csv(self, data, options=None):
        """Convert data to CSV."""
        options = options or {}
        data = self.to_simple(data, options)
        raw_data = cStringIO.StringIO()

        writer = CSVUnicodeWriter(raw_data, delimiter=';', quotechar='"',
                                  quoting=csv.QUOTE_MINIMAL)

        for category in data:
            if category == 'objects' and len(data[category]) > 0:
                items = []
                available_keys = []
                for item in data[category]:
                    flatitem = flatten_dict(item)
                    items.append(flatitem)
                    available_keys += [key for key in flatitem.keys()
                                       if key not in available_keys]

                available_keys = sorted(available_keys)
                writer.writerow(available_keys)

                for item in data[category]:
                    flatitem = flatten_dict(item)
                    writer.writerow(map(lambda x: flatitem.get(x),
                                        available_keys))

        raw_data.seek(0)
        return raw_data


class iCalSerializer(Serializer):
    """Extend tastypie's serializer to export to iCal format."""
    formats = ['json', 'jsonp', 'xml', 'yaml', 'html', 'ical']
    content_types = {'json': 'application/json',
                     'jsonp': 'text/javascript',
                     'xml': 'application/xml',
                     'yaml': 'text/yaml',
                     'html': 'text/html',
                     'ical': 'text/calendar'}

    def to_ical(self, data, options=None):
        """Convert data to iCal."""
        options = options or {}

        events = [event.obj for event in data['objects']]

        date_now = timezone.make_aware(datetime.now(), pytz.UTC)
        ical = get_template('multi_event_ical_template.ics')

        return ical.render(Context({'events': events, 'date_now': date_now,
                                    'host': settings.SITE_URL}))
