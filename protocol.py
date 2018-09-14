class Message:

    def __init__(self, typ, sender_id, receiver_id, payload):
        self.type = typ
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.payload = payload