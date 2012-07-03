import csv
import StringIO
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
        raw_data = StringIO.StringIO()

        writer = csv.writer(raw_data, delimiter=';', quotechar='"',
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
