from nose.tools import eq_
from test_utils import TestCase

from remo.base.serializers import flatten_dict


class TestSerializers(TestCase):
    """Test Serializers."""

    def test_dictionary_convertion(self):
        """Test flatten_dict()."""
        foobar = {'key1': 'value1',
                  'key2': {'skey1': 'svalue1'},
                  'key3': ['svalue2', 'svalue3']}

        expected_result = {'key1': 'value1',
                           'key2.skey1': 'svalue1',
                           'key3.0': 'svalue2',
                           'key3.1': 'svalue3'}

        eq_(flatten_dict(foobar), expected_result)
