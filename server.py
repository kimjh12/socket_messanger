import socket
import pickle
from threading import Thread

from protocol import Message

sock, peers = None, []


class MessageHandler(object):
    MAX_CONNECTIONS = 10
    PORT = 20236
    # IP_ADDRESS = '147.46.241.102'
    IP_ADDRESS = ''

    def __init__(self):
        self.user_table = {}
        self.initialize()
        for i in range(MessageHandler.MAX_CONNECTIONS):
            thread = MessageHandler.Connection(self)
            thread.daemon = True
            thread.start()

    def initialize(self):
        global sock
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind((MessageHandler.IP_ADDRESS, MessageHandler.PORT))
        print("listening...")
        sock.listen(10)

    def send_message(self, message):
        for peer in peers:
            peer.sendall(message)

    class Connection(Thread):
        def __init__(self, message_handler):
            self.message_handler = message_handler
            Thread.__init__(self)

        def run(self):
            peer, addr = sock.accept()
            print("accepted:", addr)
            peers.append(peer)
            while True:
                byte_message = peer.recv(1024)
                message = pickle.loads(byte_message)
                response = self.message_handler.handle_message(message)
                if response is not None:
                    print(response.payload)
                    peer.send(pickle.dumps(response))

    def handle_message(self, message):
        if message.type == 'text':
            print(message.payload)
        elif message.type == 'signup':
            return self.register_user(message.sender_id, message.payload)
        elif message.type == 'login':
            return self.login(message.sender_id, message.payload)
        return None


    def register_user(self, username, password):
        if username in self.user_table:
            return Message('fail', 0, 0, "Username already taken")
        else:
            self.user_table[username] = password
            return Message('success', 0, 0, "Registered. Please login")

    def login(self, username, password):
        if username in self.user_table and self.user_table[username] == password:
            return Message('success', 0, 0, 'Welcome')
        else:
            return Message('fail', 0, 0, 'Incorrect information. Try again')




messageHandler = MessageHandler()
try:
    while True:
        message = input('')
        byt = message.encode()
        messageHandler.send_message(byt)

except KeyboardInterrupt:
    sock.close()
    for peer in peers:
        peer.close()
