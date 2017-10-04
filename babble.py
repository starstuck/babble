import logging
import xml.etree.ElementTree as ET

import sleekxmpp
from sleekxmpp.componentxmpp import ComponentXMPP
from sleekxmpp.xmlstream.stanzabase import ElementBase

COMPONENT="metrics.localhost"
SECRET="secret"
SERVER_HOST="127.0.0.1"
SERVER_PORT=8888


class MetricsComponent(ComponentXMPP):

    def __init__(self, jid, secret, server, port):
        ComponentXMPP.__init__(self, jid, secret, server, port)

        self.add_event_handler("message", self._handle_message)
        self.add_event_handler("session_bind", self._handle_session_bind)
        self.add_event_handler("presence", self._handle_presence)
        self.add_event_handler('session_start', self._handle_session_start)
        self.add_event_handler('jabber_rpc_method_call', self._handle_jabber_rpc_method_call)

        self.register_plugin('xep_0009') # Jabber RPC
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0060') # PubSub
        self.register_plugin('xep_0199') # XMPP Ping

    def _handle_message(self, msg):
        """
        Process incoming message stanzas. Be aware that this also
        includes MUC messages and error messages. It is usually
        a good idea to check the messages's type before processing
        or sending replies.

        Since a component may send messages from any number of JIDs,
        it is best to always include a from JID.

        Arguments:
            msg -- The received message stanza. See the documentation
                   for stanza objects and the Message stanza to see
                   how it may be used.
        """
        # The reply method will use the messages 'to' JID as the
        # outgoing reply's 'from' JID.
        logging.info("Recived message: %s", msg)
        msg.reply("Thanks for sending\n%(body)s" % msg).send()

    def _handle_session_bind(self, jid):
        logging.info("New session started by: %s", jid)

    def _handle_presence(self, presence):
        logging.info("Got presence update: %s", presence)

    def _handle_session_start(self, event):
        logging.info("Session started: %s", event)
        #self.send_presence()
        #self.get_roster()

    def _handle_jabber_rpc_method_call(self, iq):
        logging.info("supposed to handle method call: %s", iq)
        pid = iq['id']
        caller_jid = iq['from']
        method = iq['rpc_query']['method_call']['method_name']
        logging.info("responding to method: %s", method)
        params = self._make_config_param()
        res = self['xep_0009'].make_iq_method_response(pid, caller_jid, params)
        logging.info("Sending respone: %s", res)
        res.send()

    def _make_config_param(self):
        params = ET.Element('params')
        param = ET.SubElement(params, 'param')
        pvalue = ET.SubElement(param, 'value')
        struct = ET.SubElement(pvalue, 'struct')
        member = ET.SubElement(struct, 'member')
        name = ET.SubElement(member, 'name')
        name.text = 'account'
        value = ET.SubElement(member, 'value')
        string = ET.SubElement(value, 'string')
        string.text = 'test-account'
        return ElementBase(params)


def main ():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    xmpp = MetricsComponent(COMPONENT, SECRET, SERVER_HOST, SERVER_PORT)
    if xmpp.connect():
        print("Connected")
        xmpp.process(block=True)
        print("Done")
    else:
        print("Unable to connect.")

        
if __name__ == '__main__':
    main()
