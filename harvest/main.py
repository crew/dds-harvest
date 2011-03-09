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
from xmpp_setup import setup_xmpp, process_client
import config

def main():
    LOGFORMAT = '%(asctime)s %(levelname)s %(filename)s %(lineno)s %(message)s'
    logging.basicConfig(level=logging.DEBUG, filemode='a', format=LOGFORMAT,
                        filename=config.option('log_file'))
    logging.debug('Starting main thread')
    # Delayed import because the path is not set before this point.
    sys.path.insert(0, config.option("path"))
    from handler import DDSHandler
    from harvest import Combine
    client = setup_xmpp(DDSHandler())

    logging.debug('Connection started')

    combine = Combine(client, timeout=10)
    combine.daemon = True
    combine.start() # wrrrrrrr

    try:
        process_client(client)
    except KeyboardInterrupt: # SIGINT
        logging.debug('Shutting down.')
        combine.die()
        combine.join()
