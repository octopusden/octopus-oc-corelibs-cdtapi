# created 2025-02 https://github.com/ivansa-ru

import json
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
    message priority 1-100 the higher value the lower priority (to be implemented)
    """

    def __init__(self, pg_connection=None, url=None, username=None, password=None):
        logging.debug('Initializing PgQAPI')
        if pg_connection:
            logging.debug('Using provided connection')
            self.conn = pg_connection
        else:
            logging.debug('No connection provided, creating')
            self.conn = self.pg_connect(url, username, password)
        self.message_types = ['dlartifacts', 'dlbuild', 'dlcontents', 'dlupload', 'ns']

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

    def compose_message(self, message_type, parms):
        logging.debug('reached compose_message')
        logging.debug('trying to compose message of type [%s]' % message_type)
        if message_type not in self.message_types:
            logging.error('unknown message type [%s]' % message_type)
            return None
        method_name = f'compose_{message_type}'
        method = getattr(self, method_name, None)
        return method(parms)

    def compose_dlbuild(self, parms):
        logging.debug('reached compose_dlbuild')
        logging.debug('received parms: [%s]' % parms)
        tag = parms.get('tag')
        if not tag:
            logging.error('no tag specified')
            return None
        logging.debug('composing message for tag [%s]' % tag)
        message = ["build_delivery", [tag], {}]
        logging.debug('composed message')
        logging.debug(message)
        return message

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
        csr.execute(q, (q_id, 'N', json.dumps(msg_text), priority) )
        conn.commit()

    def exec_select(self, q, parms=None):
        logging.debug('reached exec_select')
        logging.debug('will try to execute [%s] with [%s]' % (q, parms) )
        csr = self.conn.cursor()
        csr.execute(q, parms)
        ds = csr.fetchall()
        return ds

    def exec_update(self, q, parms=None, commit=True):
        logging.debug('reached exec_update')
        logging.debug('will try to execute [%s] with [%s]' % (q, parms) )
        csr = self.conn.cursor()
        csr.execute(q, parms)
        if commit:
            self.conn.commit()

    def get_msg(self, message_id):
        logging.debug('reached get_msg')
        logging.debug('getting status of message [%s]' % message_id)
        ds = self.exec_select('select status, payload from queue_message where id = %s', (str(message_id) ) )
        if ds:
            logging.debug('message found, returning [%s]', ds[0])
            return ds[0]
        else:
            return None

    def get_queue_id(self, queue_code):
        logging.debug('reached get_queue_id')
        logging.debug('searching for queue with code [%s]' % queue_code) 
        ds = self.exec_select('select id from queue_type where code = %s', (queue_code, ) )
        if ds:
            logging.debug('queue found, returning its id [%s]' % ds[0][0])
            return ds[0][0]
        else:
            logging.error('queue does not exist, returning None')
            # TODO raise an exception here
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
        if conn:
            logging.debug('connected. [%s]' % conn)
            return conn
        logging.error('failed to connect')
        return None

    def msg_proc_start(self, message_id):
        logging.debug('reached msg_proc_start')
        logging.debug('starting processing of message [%s]' % message_id)
        ds = self.get_msg(message_id)
        if not ds:
            logging.error('message [%s] does not exist' % message_id)
            return None
        (msg_status, payload) = ds
        if msg_status != 'N':
            logging.error('message [%s] is in bad status [%s]' % (str(message_id), msg_status) )
            return False
        self.exec_update('update queue_message set proc_start=now(), status=%s where id = %s', ('A', message_id) )
        return payload

    def new_msg_from_queue(self, queue_code):
        logging.debug('reached new_msg_from_queue')
        logging.debug('checking queue [%s]' % queue_code)
        queue_id = self.get_queue_id(queue_code)
        if not queue_id:
            logging.error('queue [%s] does not exist' % queue_code)
            return None
        ds = self.exec_select('select min(id), count(id) from queue_message where queue_type__oid = %s and status = %s', (queue_id, 'N') )
        if ds[0][1] == 0:
            logging.debug('currently no new messages in queue [%s]' % queue_code)
            return None
        msg_id = ds[0][0]
        logging.debug('found new message id [%s], [%s] new messages in queue' % (msg_id, ds[0][1]) )
        logging.debug('setting status of message to A')
        payload = self.msg_proc_start(msg_id)
        return payload
        
