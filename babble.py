import logging

import sleekxmpp
from sleekxmpp.componentxmpp import ComponentXMPP


COMPONENT="metrics.localhost"
SECRET="secret"
SERVER_HOST="127.0.0.1"
SERVER_PORT=8888


class MetricsComponent(ComponentXMPP):

    def __init__(self, jid, secret, server, port):
        ComponentXMPP.__init__(self, jid, secret, server, port)

        # You don't need a session_start handler, but that is
        # where you would broadcast initial presence.

        # The message event is triggered whenever a message
        # stanza is received. Be aware that that includes
        # MUC messages and error messages.
        self.add_event_handler("message", self._handle_message)
        self.add_event_handler("session_bind", self._handle_session_bind)
        self.add_event_handler("presence", self._handle_presence)

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
    

def main ():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-8s %(message)s')

    xmpp = MetricsComponent(COMPONENT, SECRET, SERVER_HOST, SERVER_PORT)
    xmpp.registerPlugin('xep_0030') # Service Discovery
    xmpp.registerPlugin('xep_0004') # Data Forms
    xmpp.registerPlugin('xep_0060') # PubSub
    xmpp.registerPlugin('xep_0199') # XMPP Ping
    if xmpp.connect():
        print("Connected")
        xmpp.process(block=True)
        print("Done")
    else:
        print("Unable to connect.")

        
if __name__ == '__main__':
    main()
