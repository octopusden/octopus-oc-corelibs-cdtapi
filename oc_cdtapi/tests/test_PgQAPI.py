import unittest
from unittest.mock import patch, MagicMock
from oc_cdtapi import PgQAPI

class TestPgQAPI(unittest.TestCase):

    @patch("psycopg2.connect")
    def test_compose_any_message(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        pgq = PgQAPI.PgQAPI()
        msg = pgq.compose_any_message('register_checksum','checksum',[{'add_data':'add_data'}])
        eth_msg = ['register_checksum', ['checksum', [{'add_data': 'add_data'}]], {}]
        self.assertEqual(msg, eth_msg)
        return True


    @patch("psycopg2.connect")
    def test_compose_message_dlbuild(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        pgq = PgQAPI.PgQAPI()
        params = {}
        params['tag'] = 'this is a tag'
        msg = pgq.compose_message('dlbuild', params)
        eth_msg = ['build_delivery', ['this is a tag'], {}]
        self.assertEqual(msg, eth_msg)


    @patch("psycopg2.connect")
    def test_compose_message_dlupload(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        pgq = PgQAPI.PgQAPI()
        msg = pgq.compose_message('dlupload','CLIENT_CODE')
        eth_msg = ['upload_delivery', ['CLIENT_CODE'], {}]
        self.assertEqual(msg, eth_msg)


    @patch("psycopg2.connect")
    def test_compose_message_reg_cs(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        pgq = PgQAPI.PgQAPI()
        params = {}
        params['file_loc'] = 'file_loc'
        params['checksum'] = 'checksum'
        params['citype'] = 'citype'
        params['mime'] = 'mime'
        msg = pgq.compose_message('register_checksum', params)
        eth_msg = ['register_checksum', ['file_loc', 'checksum', {'citype': 'citype'}, 'mime']]
        self.assertEqual(msg, eth_msg)


    @patch("psycopg2.connect")
    def test_compose_message_reg_cs_none(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        pgq = PgQAPI.PgQAPI()
        params = {}
        msg = pgq.compose_message('register_checksum', params)
        self.assertEqual(msg, None)


    @patch("psycopg2.connect")
    def test_compose_message_reg_file(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        pgq = PgQAPI.PgQAPI()
        params = {}
        params['location'] = ['path','type']
        params['citype'] = 'citype'
        params['depth'] = 'depth'
        msg = pgq.compose_message('register_file', params)
        eth_msg = ['register_file', [['path', 'type'], 'citype', 'depth'], {}]
        self.assertEqual(msg, eth_msg)


    @patch("psycopg2.connect")
    def test_compose_message_reg_file_none(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        pgq = PgQAPI.PgQAPI()
        params = {}
        params['location'] = ['path','type']
        params['depth'] = 'depth'
        msg = pgq.compose_message('register_file', params)
        self.assertEqual(msg, None)


    @patch("psycopg2.connect")
    def test_compose_message_nonexistent(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        pgq = PgQAPI.PgQAPI()
        params = {}
        msg = pgq.compose_message('nonexistent', params)
        self.assertEqual(msg, None)


    def test_enqueue_message(self):
        mock_conn = MagicMock()
        pgq = PgQAPI.PgQAPI(pg_connection=mock_conn)
        pgq.get_queue_id = MagicMock(return_value='nothing')
        pgq.enqueue_message(queue_code='nonexistent',msg_text='dummy')
        pgq.get_queue_id.assert_called_once_with('nonexistent')


    def test_get_msg(self):
        mock_conn = MagicMock()
        pgq = PgQAPI.PgQAPI(pg_connection=mock_conn)
        pgq.exec_select = MagicMock(return_value=[10])
        msg = pgq.get_msg(10)
        pgq.exec_select.assert_called_once()
        self.assertEqual(msg, 10)


    def test_get_queue_id(self):
        mock_conn = MagicMock()
        pgq = PgQAPI.PgQAPI(pg_connection=mock_conn)
        pgq.exec_select = MagicMock(return_value=[[10],10])
        q_id = pgq.get_queue_id('dummy')
        pgq.exec_select.assert_called_once()
        self.assertEqual(q_id, 10)


    def test_msg_proc_start_nonexistent(self):
        mock_conn = MagicMock()
        pgq = PgQAPI.PgQAPI(pg_connection=mock_conn)
        pgq.get_msg = MagicMock(return_value=None)
        payload = pgq.msg_proc_start(10)
        self.assertEqual(payload, None)


    def test_msg_proc_start_bad_status(self):
        mock_conn = MagicMock()
        msg = ('F','payload')
        pgq = PgQAPI.PgQAPI(pg_connection=mock_conn)
        pgq.get_msg = MagicMock(return_value=msg)
        payload = pgq.msg_proc_start(10)
        self.assertEqual(payload, False)


    def test_msg_proc_start_ok(self):
        mock_conn = MagicMock()
        msg = ('N','payload')
        pgq = PgQAPI.PgQAPI(pg_connection=mock_conn)
        pgq.get_msg = MagicMock(return_value=msg)
        pgq.exec_update = MagicMock()
        payload = pgq.msg_proc_start(10)
        self.assertEqual(payload, 'payload')


    def test_msg_proc_end_nonexistent(self):
        mock_conn = MagicMock()
        pgq = PgQAPI.PgQAPI(pg_connection=mock_conn)
        pgq.get_msg = MagicMock(return_value=None)
        payload = pgq.msg_proc_end(10)
        self.assertEqual(payload, None)


    def test_msg_proc_end_bad_status(self):
        mock_conn = MagicMock()
        msg = ('F','payload')
        pgq = PgQAPI.PgQAPI(pg_connection=mock_conn)
        pgq.get_msg = MagicMock(return_value=msg)
        payload = pgq.msg_proc_end(10)
        self.assertEqual(payload, False)


    def test_msg_proc_end_ok(self):
        mock_conn = MagicMock()
        msg = ('A','payload')
        pgq = PgQAPI.PgQAPI(pg_connection=mock_conn)
        pgq.get_msg = MagicMock(return_value=msg)
        pgq.exec_update = MagicMock()
        payload = pgq.msg_proc_end(10)
        self.assertEqual(payload, 'payload')


    def test_msg_proc_fail_nonexistent(self):
        mock_conn = MagicMock()
        pgq = PgQAPI.PgQAPI(pg_connection=mock_conn)
        pgq.get_msg = MagicMock(return_value=None)
        payload = pgq.msg_proc_fail(10)
        self.assertEqual(payload, None)


    def test_msg_proc_fail_bad_status(self):
        mock_conn = MagicMock()
        msg = ('F','payload')
        pgq = PgQAPI.PgQAPI(pg_connection=mock_conn)
        pgq.get_msg = MagicMock(return_value=msg)
        payload = pgq.msg_proc_fail(10)
        self.assertEqual(payload, False)


    def test_msg_proc_fail_ok(self):
        mock_conn = MagicMock()
        msg = ('A','payload')
        pgq = PgQAPI.PgQAPI(pg_connection=mock_conn)
        pgq.get_msg = MagicMock(return_value=msg)
        pgq.exec_update = MagicMock()
        payload = pgq.msg_proc_fail(10)
        self.assertEqual(payload, 'payload')


    def test_new_msg_from_queue_no_queue(self):
        mock_conn = MagicMock()
        pgq = PgQAPI.PgQAPI(pg_connection=mock_conn)
        pgq.get_queue_id = MagicMock(return_value=None)
        msg = pgq.new_msg_from_queue('nonexistent')
        self.assertEqual(msg, None)


    def test_new_msg_from_queue_no_new(self):
        mock_conn = MagicMock()
        pgq = PgQAPI.PgQAPI(pg_connection=mock_conn)
        pgq.get_queue_id = MagicMock(return_value=10)
        pgq.exec_select = MagicMock(return_value=[[0,0],0])
        msg = pgq.new_msg_from_queue('dummy')
        self.assertEqual(msg, None)


    def test_new_msg_from_queue_ok(self):
        mock_conn = MagicMock()
        pgq = PgQAPI.PgQAPI(pg_connection=mock_conn)
        pgq.get_queue_id = MagicMock(return_value=10)
        pgq.exec_select = MagicMock(return_value=[[10,1],0])
        pgq.msg_proc_start = MagicMock(return_value='payload')
        payload, msg_id = pgq.new_msg_from_queue('dummy')
        self.assertEqual(msg_id, 10)
        self.assertEqual(payload, 'payload')
