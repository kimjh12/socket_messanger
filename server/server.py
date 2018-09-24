import socket
import time
import pickle
from threading import Thread

from protocol import Message

sock = None
id_peer_map = {}

user_table = {}
# maps username and password
# TODO : encryption

users_online = {}
# users_online: { user1: thread id, ... }

pending_requests = {}
# pending_requests: { user1: Message, ...}

friends_list = {}
# friends_list : { user1: [ user2, user3, ... ], ...}

message_logs = {}
# message_logs :
#     {
#         (user1, user2) : [
#             [ sender, payload, unread1, unread2 ], ...
#         ],
#         ...
#     }


# Returns unique pair of two users
def get_tuple(first, second):
    return (first, second) if first < second else (second, first)

# Timer thread
class Timer(Thread):
    def __init__(self, parent):
        Thread.__init__(self)
        self.parent = parent

    def run(self):
        while True:
            self.parent.ping()
            time.sleep(10)


class MessageHandler(object):
    MAX_CONNECTIONS = 10
    PORT = 20236
    IP_ADDRESS = '147.46.241.102'

    # IP_ADDRESS = ''

    def __init__(self):
        self.initialize()
        for i in range(MessageHandler.MAX_CONNECTIONS):
            thread = MessageHandler.Connection(self)
            thread.daemon = True
            thread.start()
        
        timer = Timer(self)
        timer.daemon = True
        timer.start()

    # Initialize socket
    def initialize(self):
        global sock
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind((MessageHandler.IP_ADDRESS, MessageHandler.PORT))
        print("listening...")
        sock.listen(10)

    # Thread connecting to clients
    class Connection(Thread):
        def __init__(self, message_handler):
            self.message_handler = message_handler
            Thread.__init__(self)

        def run(self):
            peer, addr = sock.accept()
            print("accepted:", addr)
            id_peer_map[self.ident] = peer
            while True:
                try:
                    byte_message = peer.recv(1024)
                    message = pickle.loads(byte_message)
                    response = self.message_handler.handle_message(message, self.ident)
                    if response is not None:
                        peer.send(pickle.dumps(response))
                except EOFError:
                    # this happens when client app closed
                    peer.close()
                    print("closed:", addr)
                    online_ids = list(users_online.values())
                    if self.ident in online_ids:
                        username = list(users_online.keys())[online_ids.index(self.ident)]
                        del users_online[username]
                    peer, add = sock.accept()
                    print("accepted:", addr)
                    id_peer_map[self.ident] = peer

    # Handling message from client
    def handle_message(self, message, ident):
        if message.type == 'message':
            self.send_message(message.sender_id, message.receiver_id, message.payload)
        elif message.type == 'signup':
            return self.register_user(message.sender_id, message.payload)
        elif message.type == 'login':
            response = self.login(message.sender_id, message.payload)
            if response.type == 'success':
                users_online[message.sender_id] = ident
                if message.sender_id in pending_requests:
                    id_peer_map[ident].send(pickle.dumps(response))
                    msg = pending_requests[message.sender_id]
                    del pending_requests[message.sender_id]
                    return msg
            return response
        elif message.type == 'get_friends':
            return self.get_friends(message.sender_id)
        elif message.type == 'get_statuses':
            return self.get_statuses(message.sender_id)
        elif message.type == 'add_friend':
            return self.add_friend(message.sender_id, message.receiver_id)
        elif message.type == 'reply_request_friend':
            self.request_friend(message.sender_id, message.receiver_id, message.payload)
        elif message.type == 'get_logs':
            self.mark_read(message.sender_id, message.receiver_id)
            logs = message_logs[get_tuple(message.sender_id, message.receiver_id)]
            return Message("message_logs", 0, 0, logs)
        elif message.type == 'read_msg':
            self.mark_read(message.sender_id, message.receiver_id)
        elif message.type == 'signout':
            print("sign out:", message.sender_id)
            del users_online[message.sender_id]

    # Send text message to receiver
    def send_message(self, sender, receiver, payload):
        # struct: [sender, text, user1_unread, user2_unread]
        msg_struct = [sender, payload, 1, 1]
        i = 2 if sender < receiver else 3
        msg_struct[i] = 0
        message_logs[get_tuple(sender, receiver)].append(msg_struct)

        if receiver in users_online:
            peer = id_peer_map[users_online[receiver]]
            message = Message('message', sender, receiver, payload)
            try:
                peer.send(pickle.dumps(message))
            except BrokenPipeError:
                del users_online[receiver]


    def register_user(self, username, password):
        if username in user_table:
            return Message('fail', 0, 0, "Username already taken")
        else:
            user_table[username] = password
            friends_list[username] = []
            print("registered a user:", username)
            return Message('success', 0, 0, "Registered. Please login")

    def login(self, username, password):
        if username in users_online:
            return Message('fail', 0, 0, "User is already connected")
        elif username in user_table and user_table[username] == password:
            print("sign in:", username)
            return Message('success', 0, 0, "Welcome")
        else:
            return Message('fail', 0, 0, "Incorrect information. Try again")

    def add_friend(self, sender, username):
        if username not in user_table:
            return Message('fail', 0, 0, "User doesn't exist")
        if username in friends_list[sender]:
            return Message('fail', 0, 0, "User is your friend")

        message = Message('request_friend', sender, username, sender + " wants you to be friend")
        if username in users_online:
            peer = id_peer_map[users_online[username]]
            try:
                peer.send(pickle.dumps(message))
            except BrokenPipeError:
                del users_online[username]
                pending_requests[username] = messsage
        else:
            pending_requests[username] = message
        return Message('success', 0, 0, "Requested")

    def request_friend(self, sender, receiver, payload):
        if receiver in users_online:
            peer = id_peer_map[users_online[receiver]]
            message = Message('request_reply', sender, receiver, payload)
            try:
                peer.send(pickle.dumps(message))
            except BrokenPipeError:
                del users_online[receiver]
        if payload == "Accept":
            friends_list[sender].append(receiver)
            friends_list[receiver].append(sender)
            message_logs[get_tuple(sender, receiver)] = []
    
    def get_friends(self, sender):
        return Message("friends_list", 0, 0, friends_list[sender])
        
    def get_statuses(self, sender):
        statuses = map(lambda x: x in users_online, friends_list[sender])
        return Message("status_list", 0, 0, list(statuses))

    def mark_read(self, sender, receiver):
        i = 2 if sender < receiver else 3
        for log in message_logs[get_tuple(sender, receiver)]:
            log[i] = 0
    
    def ping(self):
        for user, ident in list(users_online.items()):
            peer = id_peer_map[ident]
            message = Message("ping")
            try:
                peer.send(pickle.dumps(message))
            except BrokenPipeError:
                del users_online[user]


message_handler = MessageHandler()

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    sock.close()
    for peer in id_peer_map.values():
        peer.close()
