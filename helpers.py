import psycopg2

from configuration import configuration


class PostgresHelper:
    """ Makes it more convenient to query postgres. It implements a context manager to ensure that the connection
    is closed.

     Since we never write to the DB using this class, no need to commit before closing. """

    def __init__(self,
                 user=configuration['psql']['user'],
                 host=configuration['psql']['host'],
                 database=configuration['psql']['database'],
                 password=configuration['psql']['password'],
                 port=configuration['psql']['port'],
                 application_name='m2mtool',
                 cursor_factory=psycopg2.extras.RealDictCursor,
                 **kwargs):
        """
        :param kwargs additional kwargs to pass to psycopg2.connect
        """
        self._host = host
        self._user = user
        self._database = database
        self._password = password
        self._port = port
        self._cursor_factory = cursor_factory
        self._application_name = application_name
        self._kwargs = kwargs

    def __enter__(self, ):
        self._conn = psycopg2.connect(host=self._host,
                                      user=self._user,
                                      database=self._database,
                                      password=self._password,
                                      port=self._port,
                                      cursor_factory=self._cursor_factory,
                                      application_name=self._application_name,
                                      **self._kwargs)
        return self._conn.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._conn.close()

    def commit(self):
        self._conn.commit()
