import socket
import threading

from appdaemon import appapi


from sleekxmpp import ClientXMPP
from sleekxmpp.exceptions import IqError, IqTimeout


class XmppConnector(appapi.AppDaemon, ClientXMPP):

    def initialize(self):
        ClientXMPP.__init__(self, "yuki@jumper047.tk", "password")

        self.register_plugin('xep_0004')
        self.register_plugin('xep_0030')
        self.register_plugin('xep_0054')
        self.register_plugin('xep_0060')
        self.register_plugin('xep_0084')
        self.register_plugin('xep_0153')
        self.register_plugin('xep_0172')
        self.register_plugin('xep_0199')

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)

        self.yuki_connect()

    def yuki_connect(self):
        print("Connecting...")
        if self.connect():
            self.process(block=False)
            print("Done")
        else:
            print("Unable to connect")

    def yuki_disconnect(self):
        pass

    def start(self, event):
        "Process the session_start event"
        self.send_presence()
        self.get_roster()

        self['xep_0172'].publish_nick('Юки')

        vcard = self['xep_0054'].stanza.VCardTemp()
        vcard['NICKNAME'] = 'Юки'
        vcard['JABBERID'] = self.boundjid.bare
        vcard['ORG']['ORGNAME'] = 'Jumper Inc'
        vcard['DESC'] = "Я - человекоподобный интерфейс умного дома. Ня ^_^!"

        avatar_data = None
        try:
            with open('/home/hass/sleekxmpp_data/avatar.png', 'rb') as avatar_file:
                avatar_data = avatar_file.read()
        except IOError:
            self.log('Could not load avatar')
        if avatar_data:
            avatar_id = self['xep_0084'].generate_id(avatar_data)
            print(avatar_id)
            info = {
                'id': avatar_id,
                'type': 'image/png',
                'bytes': len(avatar_data)
            }
            print(info)
            # self['xep_0084'].publish_avatar(avatar_data)
            self['xep_0084'].publish_avatar_metadata(items=[info])
            self['xep_0153'].set_avatar(avatar=avatar_data, mtype='image/png')

        self['xep_0054'].publish_vcard(vcard)
        self.send_message(mto="me@jumper047.tk",
                          mbody="Текстовый интерфейс запущен.", mtype="chat")

def message(self, message):
    "Process incoming message stanzas"
    self.get_app("brain").query(message.get('body'), "xmpp_connection")

def answer(self, message):
    self.send_message(mto="me@jumper047.tk", mbody=message, mtype="chat")


class SocketConnector(appapi.AppDaemon):

    def initialize(self):
        self.socket_handler = threading.Thread(target=self.socket_server)
        self.socket_handler.daemon = True
        self.socket_handler.start()
        print("Socket connector initialized")

    def answer(self, message):
        self.conn.send(message.encode())

    def socket_server(self):
        sock = socket.socket()
        sock.bind(('', 9097))
        sock.listen(1)

        self.conn, addr = sock.accept()

        print('Socket client connected', addr)

        while True:
            data = self.conn.recv(1024)
            self.get_app("brain").query(data.decode(), "socket_connection")

        conn.close()
