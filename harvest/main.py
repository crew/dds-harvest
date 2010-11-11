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

LOGFORMAT = '%(asctime)s %(levelname)s %(filename)s %(lineno)s %(message)s'


def parse_config():
    import ConfigParser
    config = ConfigParser.RawConfigParser()
    config.read(FLAGS.config_file)
    return {
        'username': config.get(FLAGS.config_section, 'username'),
        'password': config.get(FLAGS.config_section, 'password'),
        'resource': config.get(FLAGS.config_section, 'resource'),
        'server': config.get(FLAGS.config_section, 'server'),
        'debug': config.getboolean(FLAGS.config_section, 'debug'),
        'path': config.get(FLAGS.config_section, 'dds-path'),
        'log-file': config.get(FLAGS.config_section, 'log'),
    }


def get_options():
    options = parse_config()
    # Sync up.
    if FLAGS.debug:
        options['debug'] = FLAGS.debug
    if FLAGS.dds_path != '/':
        options['path'] = FLAGS.dds_path
    if FLAGS.log_file:
        options['log-file'] = FLAGS.log_file
    return options


class MainThread(threading.Thread):

    def __init__(self, username=None, password=None, resource=None,
                 server=None, debug=None, path=None, **kwargs):
        threading.Thread.__init__(self, **kwargs)
        self.username = username
        self.password = password
        self.resource = resource
        self.server = server
        self.debug = debug
        self.path = path

    def get_client(self):
        if self.debug:
            return xmpp.Client(server=self.server)
        else:
            return xmpp.Client(server=self.server, debug=[])

    def connect_client(self, client):
        try:
            client.connect()
            return True
        except:
            logging.info('Connecting to %s failed.', self.server)
        return False

    def auth_client(self, client):
        try:
            logging.info('Authenticating %s...', self.username)
            auth = client.auth(self.username, self.password, self.resource,
                               sasl=False)
            if not auth:
                logging.info('Auth may have failed for %s.', self.username)
                return False
            return True
        except:
            logging.info('Authentication failed for %s.', self.username)
        return False

    def register_handlers(self, client, handler):
        client.RegisterHandler('presence', handler.presence_handle)
        client.RegisterHandler('iq', handler.iq_handle, ns=xmpp.NS_RPC)
        client.sendInitPresence()
        return True

    def alive(self, client):
        try:
            client.Process(1)
        except Exception, e:
            logging.error(e)
            logging.debug('Connection closed.')
            return False
        return True

    def SetupXmpp(self):
        client = self.get_client()
        if not self.connect_client(client):
            return False
        auth = self.auth_client(client)
        if not auth:
            logging.warning('Unrecognized XMPP account: %s ! Attempting registration...', self.username)
            ident = {"username": self.username, "password": self.password}
            if not xmpp.features.register(client, self.server, ident):
                logging.error('XMPP New Account registration failed. Bailing out!')
                os.abort()
                return False
            else:
                logging.info('Registered %s.  Restarting setup...', self.username)
                # At this point, we have created a new XMPP account, and need to restart
                # the setup process.
                return self.SetupXmpp()
        return client

    def run(self):
        # Delayed import because the path is not set before this point.
        sys.path.insert(0, self.path)
        try:
            from handler import DDSHandler
            from harvest import Combine
            handler = DDSHandler()
        except ImportError:
            logging.critical('The path to DDS is not set.')
            sys.stderr.write('The dds module is not found.\n')
            return

        client = self.SetupXmpp()
        if not client:
            return
        if not self.register_handlers(client, handler):
            return

        logging.debug('Connection started')

        combine = Combine(client, timeout=10)
        combine.daemon = True
        combine.start() # wrrrrrrr

        try:
            while self.alive(client):
                pass
        except KeyboardInterrupt: # SIGINT
            logging.debug('Shutting down.')
            combine.die()
            combine.join()
            return


def main(interval=30):
    options = get_options()

    logging.basicConfig(level=logging.DEBUG, filemode='a', format=LOGFORMAT,
                        filename=options.pop('log-file'))

    if FLAGS.daemonize:
        daemonize()

    # mask the password for logging
    options_copy = dict(options)
    options_copy['password'] = '********'
    logging.info(options_copy)

    # Restart every <interval> seconds
    while True:
        pid = os.fork()
        if pid == 0:
            # in the child
            # run the main thread
            logging.debug('Starting main thread')
            mt = MainThread(**options)
            mt.daemon = True
            mt.start()
            mt.join()
            return
        elif pid > 0:
            # in the parent
            # sleep for the interval, then kill the child
            logging.debug('Sleeping for %d', interval)
            time.sleep(interval)
            # use SIGINT first, then SIGKILL
            os.kill(pid, signal.SIGINT)
            time.sleep(0.5)
            os.kill(pid, signal.SIGKILL)
            # reap the child (lest there be zombies)
            os.waitpid(pid, 0)
        else:
            # oh crap, we can't fork.
            sys.exit(1)
