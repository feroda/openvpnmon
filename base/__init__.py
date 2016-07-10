from django.db.backends.signals import connection_created
from django.conf import settings

from pprint import pprint


def use_schema(sender, **kwargs):

    connection = kwargs['connection']

    # If SCHEMA has been provided for this connection
    if settings.DATABASES[connection.alias]['ENGINE'].find('postgresql') != -1:
        db_schema = settings.DATABASE_SCHEMAS.get(connection.alias)
        if db_schema:
            cursor = connection.cursor()
            cursor.execute("SET search_path TO \"%s\";" % db_schema)


connection_created.connect(use_schema)
