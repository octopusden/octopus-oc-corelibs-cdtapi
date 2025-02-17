import logging
import os
import psycopg2
from urllib.parse import urlparse



class PgQAPI (object):
    """
    message statuses are:
    N = new
    A = active, being processed
    F = failed
    P = processed
    message priority 1-100 the higher value the lower priority
    """

    def __init__(self, pg_connection=None, url=None, username=None, password=None):
        logging.debug('Initializing PgQAPI')
        if pg_connection:
            logging.debug('Using provided connection')
            self.conn = pg_connection
        else:
            logging.debug('No connection provided, creating')
            self.conn = self.pg_connect(url, username, password)

    def create_queue(self, queue_code, queue_name):
        logging.debug('reached create_queue')
        logging.debug('checking existence of queue with code [%s]' % queue_code)
        q_id = self.get_queue_id(queue_code)
        if q_id:
            logging.error('queue with code [%s] already exists' % queue_code)
            return None
        else:
            csr = self.conn.cursor()
            q = 'insert into queue_type (code, name, status) values (%s, %s, %s)'
            csr.execute(q, (queue_code, queue_name, 'A') )
            self.conn.commit()
            q_id = self.get_queue_id(queue_code)
        if q_id:
            return q_id
        else:
            logging.error('failed to create queue')

    def enqueue_message(self, queue_code=None, msg_text=None, priority=50, pg_connection=None):
        logging.debug('reached enqueue_message')
        if pg_connection:
            logging.debug('using provided connection')
            conn = pg_connection
        else:
            conn = self.conn
        logging.debug('will try to create message [%s] in queue [%s]' % (msg_text, queue_code) )
        q_id = self.get_queue_id(queue_code)
        csr = conn.cursor()
        q = 'insert into queue_message (queue_type__oid, status, payload, priority) values (%s, %s, %s, %s)'
        csr.execute(q, (q_id, 'N', msg_text, priority) )
        conn.commit()

    def get_queue_id(self, queue_code):
        logging.debug('reached get_queue_id')
        logging.debug('searching for queue with code [%s]' % queue_code) 
        csr = self.conn.cursor()
        q = 'select id from queue_type where code = %s'
        csr.execute(q, (queue_code, ) )
        ds = csr.fetchone()
        if ds:
            logging.debug('queue found, returning its id')
            return ds[0]
        else:
            logging.debug('no queue found, returning None')
            return None

    def pg_connect(self, url=None, username=None, password=None):
        logging.debug('reached pg_connect')
        if (url is None):
            logging.debug('constructing dsn from env variables')
            url = os.environ.get('PSQL_MQ_URL')
            username = os.environ.get('PSQL_MQ_USER')
            password = os.environ.get('PSQL_MQ_PASSWORD')
        else:
            logging.debug('constructing dsn from parameters')
        dsn = f"postgresql://{username}:{password}@{url}"
        logging.debug('attempting to connect to [%s]' % url)
        conn = psycopg2.connect(dsn)
        return conn

