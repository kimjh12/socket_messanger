
from threading import Thread
import socket
import pickle

from protocol import Message

import sys
import time
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import *

IP_ADDRESS = '147.46.241.102'
# IP_ADDRESS = '0.0.0.0'
PORT = 20236

BUFFER_LENGTH = 1024

form_class = uic.loadUiType("main_window.ui")[0]
form_login = uic.loadUiType("login_dialog.ui")[0]

sock = None

def msg_to_string(msg):
    if msg[2] + msg[3] > 0:
        return "1 " + msg[0] + " : " + msg[1] 
    else:
        return "  " + msg[0] + " : " + msg[1] 

class MessageSender():
    def __init__(self):
        global sock
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((IP_ADDRESS, PORT))
        self.name = ""
        print("socket connected")

    def request_login(self, username, password):
        login_message = Message("login", username, 0, password)
        sock.send(pickle.dumps(login_message))
        message = pickle.loads(sock.recv(BUFFER_LENGTH))
        if message.type == "success":
            self.name = username
        return message

    def request_signup(self, username, password):
        signup_message = Message("signup", username, 0, password)
        sock.send(pickle.dumps(signup_message))
        message = pickle.loads(sock.recv(BUFFER_LENGTH))
        return message
    
    def request_add_friend(self, receiver):
        add_friend_message = Message("add_friend", self.name, receiver)
        sock.send(pickle.dumps(add_friend_message))
    
    
    def reply_request_friend(self, receiver, accepted):
        message = Message("reply_request_friend", self.name, receiver, accepted)
        sock.send(pickle.dumps(message))

    def send_message(self, receiver, text):
        message = Message("message", self.name, receiver, text)
        byte_message = pickle.dumps(message)
        sock.send(byte_message)

    def get_friends_list(self):
        message = Message("get_friends", self.name, 0)
        sock.send(pickle.dumps(message))

    def get_status_list(self):
        message = Message("get_statuses", self.name, 0)
        sock.send(pickle.dumps(message))

    def get_message_log(self, receiver):
        message = Message("get_logs", self.name, receiver)
        sock.send(pickle.dumps(message))
    
    def read_message(self, receiver):
        message = Message("read_msg", self.name, receiver)
        sock.send(pickle.dumps(message))
        
    def signout(self):
        message = Message("signout", self.name)
        sock.send(pickle.dumps(message))

class ReplyHandler(QThread):
    threadSignal = pyqtSignal(Message)

    def __init__(self, parent=None):
        super().__init__()

    def run(self):
        while True:
            byte_message = sock.recv(BUFFER_LENGTH)
            message = pickle.loads(byte_message)

            if type(message) == Message:
                self.threadSignal.emit(message)   

class TimerSignalSender(QThread):
    timerSignal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
    
    def run(self):
        while True:
            time.sleep(1)
            self.timerSignal.emit()

class MainWindow(QMainWindow, form_class):
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.addFriendButton.clicked.connect(self.add_friend_clicked)
        self.signoutButton.clicked.connect(self.signout_clicked)
        self.sendButton.clicked.connect(self.send_clicked)
        self.receiver = None
        message_sender.get_friends_list()
        
        self.reply_thread = ReplyHandler()
        self.reply_thread.threadSignal.connect(self.thread_signal_handler)
        self.reply_thread.start()

        self.timer_thread = TimerSignalSender()
        self.timer_thread.timerSignal.connect(self.timer_signal_handler)
        self.timer_thread.start()

    @pyqtSlot(Message)
    def thread_signal_handler(self, message):
        if message.type == "request_friend":
            self.handle_friend_request(message.sender_id)
        elif message.type == "request_reply":
            self.handle_request_reply(message.sender_id, message.payload)
        elif message.type == "message":
            if message.sender_id == self.receiver:
                self.receive_message()
        elif message.type == "friends_list":
            self.load_friends_list(message.payload)
        elif message.type == "status_list":
            self.load_status_list(message.payload)
        elif message.type == "message_logs":
            self.load_message_logs(message.payload)
        elif message.type == 'success':
            QMessageBox.about(self, "", message.payload)
        elif message.type == "fail":
            QMessageBox.about(self, "", message.payload)
        elif message.type == "ping":
            sock.send(pickle.dumps(Message("pong", message_sender.name)))
    

    @pyqtSlot(QListWidgetItem)
    def selectFriend(self, item):
        if item is not None:
            self.receiver = item.text()
            # self.load_message_logs()
            message_sender.get_message_log(item.text())

    @pyqtSlot()
    def timer_signal_handler(self):
        message_sender.get_status_list()
        if self.receiver is not None:
            message_sender.get_message_log(self.receiver)
    
    def add_friend_clicked(self):
        username, ok = QInputDialog.getText(self, "username", "Input username")
        if ok:
            if username == message_sender.name:
                QMessageBox.about(self, "", "Invalid ID")
                return
            message_sender.request_add_friend(username)
            
    def load_friends_list(self, friends_list):
        self.friendsList.clear()
        self.friendsList.addItems(friends_list)
    
    def load_status_list(self, status_list):
        self.statusList.clear()
        statuses = map(lambda x: "online" if x else "offline", status_list)
        self.statusList.addItems(statuses)

    def load_message_logs(self, message_logs):
        self.messageLogs.clear()
        self.messageLogs.addItems(map(lambda x: msg_to_string(x), message_logs))
    
    def receive_message(self):
        message_sender.read_message(self.receiver)
        message_sender.get_message_log(self.receiver)

    def reload_all(self):
        self.update()
        message_sender.get_friends_list()
        self.messageLogs.clear()

    def signout_clicked(self):
        message_sender.signout()
        self.close()
        self.timer_thread.terminate()
        self.reply_thread.terminate()
        login_dialog = LoginDialog()
        login_dialog.show()
        if login_dialog.exec() == QDialog.Accepted:
            main_window.__init__()
            main_window.show()

    def send_clicked(self):
        if self.receiver == None:
            QMessageBox.about(self, "", "Select a friend")
        else:
            text = self.messageInput.toPlainText()
            message_sender.send_message(self.receiver, text)
            self.messageLogs.addItem(msg_to_string([message_sender.name, text, 1, 1]))
        self.messageInput.clear()

    def handle_friend_request(self, username):
        msg = username + " wants to be your friend"
        if QMessageBox.question(self, "", msg, QMessageBox.Cancel, 
            QMessageBox.Ok) == QMessageBox.Ok:
            message_sender.reply_request_friend(username, "Accept")
        else:
            message_sender.reply_request_friend(username, "Decline")
        message_sender.get_friends_list()
    
    def handle_request_reply(self, username, reply):
        if reply == "Accept":
            msg = username + " accepted your request" 
        else:
            msg = username + " declined your request"
        QMessageBox.about(self, "", msg)
        message_sender.get_friends_list()

class LoginDialog(QDialog, form_login):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.buttonLogin.clicked.connect(self.handleLogin)
        self.buttonSignup.clicked.connect(self.handleSignup)

    def handleLogin(self):
        username = self.username.text()
        password = self.password.text()
        response = message_sender.request_login(username, password)
        if response.type == "success":
            self.accept()
        else:
            self.textLabel.setText(response.payload)

    def handleSignup(self):
        username = self.username.text()
        password = self.password.text()
        response = message_sender.request_signup(username, password)
        self.textLabel.setText(response.payload)
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    message_sender = MessageSender()
    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.Accepted:
        main_window = MainWindow()
        main_window.show()
    else:
        sys.exit()

    sys.exit(app.exec())