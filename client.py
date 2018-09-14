
from threading import Thread
import socket
import pickle

from protocol import Message


import sys
from PyQt5 import QtWidgets
from PyQt5 import uic



# IP_ADDRESS = '147.46.241.102'
IP_ADDRESS = '0.0.0.0'
PORT = 20236

BUFFER_LENGTH = 1024

class ReplyHandler(Thread):
    def __init__(self):
        Thread.__init__(self)
    def run(self):
        while True:
            byte_message = sock.recv(BUFFER_LENGTH)
            message = pickle.loads(byte_message)
            print(message.payload)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((IP_ADDRESS, PORT))
print("socket connected")

def login():
    username = input("username: ")
    password = input("password: ")
    login_message = Message('login', username, 0, password)
    sock.send(pickle.dumps(login_message))
    byte_message = sock.recv(BUFFER_LENGTH)
    message = pickle.loads(byte_message)
    print(message.payload)
    if message.type == 'success':
        main()
    else:
        login()

def signup():
    username = input("username: ")
    password = input("password: ")
    signup_message = Message('signup', username, 0, password)
    sock.send(pickle.dumps(signup_message))
    byte_message = sock.recv(BUFFER_LENGTH)
    message = pickle.loads(byte_message)
    print(message.payload)
    if message.type == 'success':
        login()
    else:
        signup()

def main():
    thread = ReplyHandler()
    thread.daemon = True
    thread.start()
    while True:
        payload = input('')
        sender_id = 0
        receiver_id = 1
        message = Message('text', sender_id, receiver_id, payload)
        byte_message = pickle.dumps(message)
        sock.send(byte_message)

def index():
    discriminator = input("1 to login, 2 to signup: ")
    if discriminator == '1':
        login()
    elif discriminator == '2':
        signup()

# index()


 
class Form(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.ui = uic.loadUi("form.ui")
        self.ui.show()
 
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = Form()
    sys.exit(app.exec())