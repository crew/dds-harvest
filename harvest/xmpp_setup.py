"""
Handles various xmpp related setup for harvest
"""
__author__ = 'CCIS Crew <crew@ccs.neu.edu>'

import config
import xmpp
import logging

def process_client(client):
    """
    Process connections from the given client until an Exception is
    raised.
    """
    def alive(client):
        try:
            client.Process(1)
        except Exception, e:
            logging.error(e)
            logging.debug('Connection closed.')
            return False
        return True
    while alive(client):
        pass

def get_client():
    """
    Returns an xmpp client object that connects to the xmpp server
    specified in harvest's configuration.
    """
    if config.option("debug"):
        return xmpp.Client(server=config.option("server"))
    else:
        return xmpp.Client(server=config.option("server"), debug=[])

def connect_client(client):
    """
    Attempts to connect the given xmpp client object. Logs an error
    and raises some sort of xmpp error if connection fails.
    """
    try:
        client.connect()
    except Exception, e:
        logging.info('Connecting to %s failed.', config.option("server"))
        raise e

def auth_client(client):
    """
    Attempts to authenticate the given xmpp client object with the
    username and password credentials specified in harvest's
    config. Returns True if the client was successfully authed, and
    False otherwise
    """
    try:
        logging.info('Authenticating %s...', config.option("username"))
        auth = client.auth(config.option("username"),
                           config.option("password"),
                           config.option("resource"), sasl=False)
        if not auth:
            logging.info('Auth may have failed for %s.',
                         config.option("username"))
        return auth
    except:
        logging.info('Authentication failed for %s.', config.option("username"))
    return False

def register_handlers(client, handler):
    """
    Registers handler's presence_handle() and iq_handle() methods with
    client's 'presence' and 'iq' events.
    """
    client.RegisterHandler('presence', handler.presence_handle)
    client.RegisterHandler('iq', handler.iq_handle, ns=xmpp.NS_RPC)
    client.sendInitPresence()

def setup_xmpp(handler):
    """
    Sets up harvest's xmpp connection, and returns a client object to
    use it. If the username specified in harvest's configuration has
    not been registered yet, it's automatically registered with the
    config-specified password.

    The returned client object has its 'presence' and 'iq' events
    handled by the given handler object.
    """
    client = get_client()
    connect_client(client)
    if not auth_client(client):
        logging.warning('Unrecognized XMPP account: %s! Attempting registration...',
                        config.option("username"))
        ident = {"username": config.option("username"),
                 "password": config.option("password")}
        if not xmpp.features.register(config.option("client"),
                                      config.option("server"), ident):
            raise Exception('XMPP New Account registration failed. Bailing out!')
        else:
            logging.info('Registered %s.  Restarting setup...',
                         config.option("username"))
            # At this point, we have created a new XMPP account, and need to restart
            # the setup process.
            return SetupXmpp()
    register_handlers(client, handler)
    return client
