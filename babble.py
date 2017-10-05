import logging
import xml.etree.ElementTree as ET

import sleekxmpp
from sleekxmpp.componentxmpp import ComponentXMPP
from sleekxmpp.plugins.xep_0009.binding import py2xml

COMPONENT="metrics.localhost"
SECRET="secret"
SERVER_HOST="127.0.0.1"
SERVER_PORT=8888


class Service(object):

    def __init__(self, xmpp):
        self.xmpp = xmpp
        xmpp.add_event_handler("message", self._handle_message)
        xmpp.add_event_handler("session_bind", self._handle_session_bind)
        xmpp.add_event_handler("presence", self._handle_presence)
        xmpp.add_event_handler('session_start', self._handle_session_start)
        xmpp.add_event_handler('jabber_rpc_method_call', self._handle_jabber_rpc_method_call)

        xmpp.register_plugin('xep_0009') # Jabber RPC
        xmpp.register_plugin('xep_0030') # Service Discovery
        xmpp.register_plugin('xep_0060') # PubSub
        xmpp.register_plugin('xep_0199') # XMPP Ping

        # TODO: the service should manage its roster

    def _handle_message(self, msg):
        # outgoing reply's 'from' JID.
        logging.info("Recived message: %s", msg)
        msg.reply("Thanks for sending\n%(body)s" % msg).send()

    def _handle_session_bind(self, jid):
        logging.info("New session started by: %s", jid)

    def _handle_presence(self, presence):
        logging.info("Received presence update: %s", presence)
        logging.info("Known rosters: %s", self.xmpp.roster._rosters)

    def _handle_session_start(self, event):
        logging.info("Session started: %s", event)
        #self.send_presence()
        #self.get_roster()

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

    def _subscribe(self, jid):
        xmpp = self.xmpp
        if jid.bare in xmpp.roster[xmpp.boundjid.bare]:
            logging.info("Already subscribed to %s presence", jid)
        else:
            logging.info("Subscribing to %s presence", jid)
            self.xmpp.sendPresenceSubscription(pto=jid,
                                               ptype='subscribe')

    def _get_config(self):
        return {'account': 'nice-account'}


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
