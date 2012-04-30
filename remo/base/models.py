import datetime

from django.db import models
from south.modelsinspector import add_introspection_rules

class UTCDateTimeField(models.DateTimeField):
    """A django DateTimeField that uses utcnow() instead of now()."""
    def pre_save(self, model_instance, add):
        if self.auto_now or (self.auto_now_add and add):
            value = datetime.datetime.utcnow()
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super(UTCDateTimeField, self).pre_save(model_instance, add)

# Add South Introspection Rules for UTCDateTimeField.
add_introspection_rules([], ["^remo\.base\.models\.UTCDateTimeField"])
