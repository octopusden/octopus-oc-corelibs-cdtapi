import logging
import os
import psycopg2
from urllib.parse import urlparse

class PgQAPI (object):

    def __init__(self, pg_connection=None, url=None, username=None, password=None):
        logging.debug('Initializing PgQAPI')
        if pg_connection:
            logging.debug('Using provided connection')
            self.conn = pg_connection
        else:
            logging.debug('No connection provided, creating')
            self.conn = self.pg_connect(url, username, password)

    def get_queue_id(self, queue_code):
        logging.debug('reached get_queue_id')
        logging.debug('searching for queue with code [%s]' % queue_code) 
        csr = self.conn.cursor()
        q = 'select id from mq.queue_type where code = %s'
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

    def enqueue_message(self, msg_text, queue_name=None, pg_connection=None):
        None
