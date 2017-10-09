import logging
import xml.etree.ElementTree as ET

import sleekxmpp
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import StanzaPath
from sleekxmpp.componentxmpp import ComponentXMPP
from sleekxmpp.plugins.xep_0009.binding import py2xml, _xml2py

COMPONENT="metrics.localhost"
SECRET="secret"
SERVER_HOST="127.0.0.1"
SERVER_PORT=8888


class Service(object):

    def __init__(self, xmpp):
        self.xmpp = xmpp
        xmpp.add_event_handler('message', self._handle_message)
        xmpp.add_event_handler('session_bind', self._handle_session_bind)
        xmpp.add_event_handler('presence', self._handle_presence)
        xmpp.add_event_handler('session_start', self._handle_session_start)
        xmpp.add_event_handler('jabber_rpc_method_call', self._handle_jabber_rpc_method_call)

        xmpp.register_plugin('xep_0009') # Jabber RPC
        xmpp.register_plugin('xep_0030') # Service Discovery
        xmpp.register_plugin('xep_0060') # PubSub
        xmpp.register_plugin('xep_0199') # XMPP Ping

        # Remove default pub/sub emssage handler, because I don't want to deal
        # with each of them item individually. I'd rather process them in batches
        xmpp.remove_handler('Pubsub Event: Items')
        xmpp.register_handler(
            Callback('Babble Pubsub Event: Items',
                    StanzaPath('message/pubsub_event/items'),
                    self._handle_pubsub_items))
        
        # TODO: check if server is keeping track of subscriptions sufficiently

    def _handle_message(self, msg):
        logging.info("Recived plain message from %s: %s", msg['from'])

    def _handle_session_bind(self, jid):
        logging.info("New session started by: %s", jid)

    def _handle_presence(self, presence):
        logging.info("Received presence update: %s", presence)
        logging.info("Known rosters: %s", self.xmpp.roster._rosters)

    def _handle_session_start(self, event):
        logging.info("Session started")

    def _handle_jabber_rpc_method_call(self, iq):
        pid = iq['id']
        caller_jid = iq['from']
        method = iq['rpc_query']['method_call']['method_name']
        logging.info("responding to method: %s", method)
        config = self._get_config()
        params = py2xml(config)
        res = self.xmpp['xep_0009'].make_iq_method_response(pid, caller_jid, params)
        logging.info("Sending respone: %s", res)
        res.send()
        self._subscribe(caller_jid)

    def _handle_probe(self, presence):
        sender = presence['from']
        # Populate the presence reply with the agent's current status.
        self.xmpp.send_presence(pto=sender, pstatus="Ready for data", pshow="chat")

    def _handle_pubsub_items(self, msg):
        mfrom = msg['from']
        node = msg['pubsub_event']['items']['node']
        count = len(msg['pubsub_event']['items'])
        items = [_xml2py(x.find('{jabber:iq:rpc}value')) for x in msg['pubsub_event']['items']]
        logging.info('Received %s event from %s (%d items, %s bytes): [%s, ...]',
                      node, mfrom, count, len(str(msg)), str(items[0]))
        
    def _subscribe(self, jid):
        xmpp = self.xmpp
        if jid.bare in xmpp.roster[xmpp.boundjid.bare]:
            logging.info("Already subscribed to %s presence", jid)
        else:
            logging.info("Subscribing to %s presence", jid)
            self.xmpp.sendPresenceSubscription(pto=jid,
                                               ptype='subscribe')

    def _get_config(self):
        return {'account': {'id': 'test-account'}}


def main ():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    xmpp = ComponentXMPP(COMPONENT, SECRET, SERVER_HOST, SERVER_PORT)
    service = Service(xmpp)
    if xmpp.connect():
        xmpp.process(block=True)
        logging.info("Done")
    else:
        logging.error("Unable to connect.")


if __name__ == '__main__':
    main()
