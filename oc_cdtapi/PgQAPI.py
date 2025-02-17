import psycopg2

class PgQAPI (object):

    def __init__(self, pg_connection=None, url=None, username=None, password=None):
        if pg_connection:
            self.conn = pg_connection
        else:
            self.conn = pg_connect(url, username, password)

    def pg_connect(self, url=None, username=None, password=None):
        None

    def enqueue_message(self, msg_text, queue_name=None, pg_connection=None):
        None
