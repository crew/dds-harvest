"""
This module is a simple configuration store for key/value pairs.
"""
__author__ = 'CCIS Crew <crew@ccs.neu.edu>'

import ConfigParser
import gflags as flags
import logging
import os
import sys

# Setup command line options for this module
flags.DEFINE_string('config_file', '/etc/dds-server.conf',
                    'Path to the configuration file')
flags.DEFINE_string('config_section', 'DEFAULT',
                    'Configuration file section to parse')
flags.DEFINE_string('log_file', None, 'Log file path')
flags.DEFINE_boolean('debug', False, 'Enable debugging')
flags.DEFINE_string('dds_path', '/', 'Path to the dds module.')
FLAGS = flags.FLAGS

# Shared options storage
OPTIONS = None

def config_file():
  """Get an expanded user path to the configuration file."""
  filename = os.path.expanduser(FLAGS.config_file)

  if not os.path.exists(filename):
    logging.error('Could not open config file %s. Please make sure it'
                  ' exists and is readable and try again.\n' % filename)
    sys.exit(1)

  return filename

def init():
  """
  Initialize this configuration store.
  """
  global OPTIONS
  file_path = config_file()
  config = ConfigParser.ConfigParser()
  config.read(file_path)
  OPTIONS = { 'username': config.get(FLAGS.config_section, 'username'),
              'password': config.get(FLAGS.config_section, 'password'),
              'resource': config.get(FLAGS.config_section, 'resource'),
              'server': config.get(FLAGS.config_section, 'server'),
              'debug': config.getboolean(FLAGS.config_section, 'debug'),
              'path': config.get(FLAGS.config_section, 'dds-path'),
              'log-file': config.get(FLAGS.config_section, 'log') }
  if FLAGS.debug:
      OPTIONS['debug'] = FLAGS.debug
  if FLAGS.dds_path != '/':
      OPTIONS['path'] = FLAGS.dds_path
  if FLAGS.log_file:
      OPTIONS['log_file'] = FLAGS.log_file

def option(name):
  """Get an option from the configuration object.
  Args:
     name: (string) configuration key
  """
  global OPTIONS
  if OPTIONS is None:
    init()
  return OPTIONS.get(name)
