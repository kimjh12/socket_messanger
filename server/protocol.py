class Message:

    def __init__(self, typ, sender_id=0, receiver_id=0, payload=None):
        self.type = typ
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.payload = payload