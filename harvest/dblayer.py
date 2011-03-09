# vim: set tabstop=4 softtabstop=4 shiftwidth=4 expandtab :
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'dds.settings'
import xmpp
import xmlrpclib
from dds.orwell.models import Location, Client, ClientActivity, Slide, Message, Playlist

__author__ = 'Alex Lee <lee@ccs.neu.edu>'


def collect_messages():
    return Message.recent.all()


def generate_request(variables, methodname=None, methodresponse=None,
                     encoding='utf-8', allow_none=False):
    """Create an xml format of the varibles and the methodname if given."""
    request = xmlrpclib.dumps(variables, methodname, methodresponse, encoding,
                              allow_none)
    return [xmpp.simplexml.NodeBuilder(request).getDom()]


def get_default_location():
    location, _ = Location.objects.get_or_create(name='Unknown')
    return location

def get_client(jid):
    """Gets the Client from Django, if one exists."""
    client, created = Client.objects.get_or_create(pk=jid,
                                                   defaults={'location': get_default_location(), })
    return client, created

def get_slide(pk):
    try:
        slide = Slide.objects.get(pk=pk)
    except:
        return None
    return slide

def get_playlist(pk):
    try:
        playlist = Playlist.objects.get(pk=pk)
    except:
        return None
    return playlist


def get_activity(jid):
    return ClientActivity.objects.get_or_create(pk=jid)
