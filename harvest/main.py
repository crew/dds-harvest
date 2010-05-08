# vim: set shiftwidth=4 tabstop=4 softtabstop=4 expandtab :
# ***** BEGIN LICENCE BLOCK *****
#
# The Initial Developer of the Original Code is
# The Northeastern University CCIS Volunteer Systems Group
#
# Contributor(s):
#   Alex Lee <lee@ccs.neu.edu>
#
# ***** END LICENCE BLOCK *****
import os
import sys
import time
import signal
import logging
import threading
import xmpp
import gflags as flags
from daemonize import daemonize

flags.DEFINE_string('config_file', '/etc/dds-server.conf',
                    'Path to the configuration file')
flags.DEFINE_string('config_section', 'DEFAULT',
                    'Configuration file section to parse')
flags.DEFINE_string('log_file', None, 'Log file path')
flags.DEFINE_boolean('debug', False, 'Enable debugging')
flags.DEFINE_boolean('daemonize', True, 'Enable Daemon Mode')
flags.DEFINE_string('dds_path', '/', 'Path to the dds module.')
FLAGS = flags.FLAGS


def parse_config():
    import ConfigParser
    config = ConfigParser.RawConfigParser()
    config.read(FLAGS.config_file)
    return [config.get(FLAGS.config_section, 'username'),
            config.get(FLAGS.config_section, 'password'),
            config.get(FLAGS.config_section, 'resource'),
            config.get(FLAGS.config_section, 'server'),
            config.getboolean(FLAGS.config_section, 'debug'),
            config.get(FLAGS.config_section, 'dds-path'),
            config.get(FLAGS.config_section, 'log')]


def get_options():
    all_list = parse_config()

    # Sync up.
    if FLAGS.debug:
        all_list[4] = FLAGS.debug
    if FLAGS.dds_path != '/':
        all_list[5] = FLAGS.dds_path
    if FLAGS.log_file:
        all_list[6] = FLAGS.log_file

    return all_list


def alive(dispatch):
    try:
        dispatch.Process(1)
    except Exception, e:
        logging.error('%s', e)
        logging.info('Connection closed.')
        return False
    return True


class MainThread(threading.Thread):

    def __init__(self, username, password, resource, server, debug, path,
                 *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.username = username
        self.password = password
        self.resource = resource
        self.server = server
        self.debug = debug
        self.path = path

    def get_client(self):
        server = self.server
        if self.debug:
            return xmpp.Client(server=server)
        else:
            return xmpp.Client(server=server, debug=[])

    def connect_client(self, client):
        try:
            client.connect()
        except:
            logging.debug('Connecting to server failed.')
            sys.exit(2)

    def auth_client(self, client):
        try:
            client.auth(self.username, self.password, self.resource,
                        sasl=False)
        except:
            logging.debug('Authorization failed.')
            sys.exit(3)

    def register_handlers(self, client, handler):
        client.RegisterHandler('presence', handler.presence_handle)
        client.RegisterHandler('iq', handler.iq_handle, ns=xmpp.NS_RPC)
        client.sendInitPresence()

    def run(self):
        logging.info('path: %s', self.path)
        # Delayed import because the path is not set before this point.
        sys.path.insert(0, self.path)
        try:
            from handler import DDSHandler
            from harvest import Combine
            handler = DDSHandler()
        except ImportError:
            logging.critical('The path to DDS is not set.')
            sys.stderr.write('The dds module is not found.\n')
            sys.exit(1)

        client = self.get_client()
        self.connect_client(client)
        self.auth_client(client)
        self.register_handlers(client, handler)

        logging.info('Connection started')

        combine = Combine(client, timeout=10)
        combine.daemon = True
        combine.start() # wrrrrrrr

        try:
            while alive(client):
                pass
        except KeyboardInterrupt:
            logging.debug('Shutting down.')
            combine.die()
            combine.join()
            return

def main():
    options = get_options()
    log = options[6]
    options = options[:6]

    if FLAGS.daemonize:
        daemonize()

    logging.basicConfig(level=logging.DEBUG, filename=log, filemode='a',
                        format='%(asctime)s %(filename)s %(lineno)s '
                               '%(levelname)s %(message)s')

    while True:
        pid = os.fork()
        if pid == 0:
            logging.info('Starting main thread')
            mt = MainThread(*options)
            mt.run()
            return
        elif pid > 0:
            logging.info('sleeping for 30')
            time.sleep(30)
            os.kill(pid, signal.SIGINT)
            os.waitpid(pid, 0)
        else:
            sys.exit(1)
