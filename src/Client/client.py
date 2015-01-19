# Lab2Client.py
# Lab 4 CS4032
# Cathal Geoghegan #11347076

import socket
import sys
import re
import threading
import logging
import time

epoch_time = str(time.time())
logging.basicConfig(filename=epoch_time+'.log', level=logging.DEBUG)

class TCPClient:
    PORT = 8000
    HOST = "0.0.0.0"
    JOIN_HEADER = "JOIN_CHATROOM: %s\nCLIENT_IP: 0\nPORT: 0\nCLIENT_NAME: %s\n\n"
    LEAVE_HEADER = "LEAVE_CHATROOM: %s\nJOIN_ID: %s\nCLIENT_NAME: %s\n\n"
    MESSAGE_HEADER = "CHAT: %s\nJOIN_ID: %s\nCLIENT_NAME: %s\nMESSAGE: %s\n\n"
    DISCONNECT_HEADER = "DISCONNECT: 0\nPORT: 0\nCLIENT_NAME: %s\n\n"
    JOIN_REGEX = "join [a-zA-Z0-9_]* [a-zA-Z0-9_]*"
    LEAVE_REGEX = "leave [a-zA-Z0-9_]* [a-zA-Z0-9_]* [a-zA-Z0-9_]*"
    MSG_REGEX = "msg [a-zA-Z0-9_]* [a-zA-Z0-9_]* [a-zA-Z0-9_]* [a-zA-Z0-9_]*"
    MESSAGE_REPLY_REGEX = "CHAT: [0-9]*\nCLIENT_NAME: [a-zA-Z0-9_]*\nMESSAGE: [a-zA-Z0-9_]*\n\n"
    JOIN_SUCCESS_REGEX = "JOINED_CHATROOM: [a-zA-Z0-9_]*\nSERVER_IP: 0\nPORT: 0\nROOM_REF: [0-9]*\nJOIN_ID: [0-9]*\n\n"
    JOIN_FAIL_REGEX = "ERROR_CODE: [0-9]*\nERROR_DESCRIPTION: .*\n\n"
    LEAVE_REPLY_REGEX = "LEFT_CHATROOM: [0-9]*\nJOIN_ID: [0-9]*\n\n"
    NEW_JOIN_REGEX = "JOINED_ROOM: [0-9]*\nCLIENT_NAME: [a-zA-Z0-9_]*"
    REQUEST = "%s"
    LENGTH = 4096

    def __init__(self, port_use=None):
        if not port_use:
            self.port_use = self.PORT
        else:
            self.port_use = port_use
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.HOST, self.port_use))
        self.rooms = dict()
        thread = ThreadHandler(self.sock, self, self.LENGTH)
        thread.setDaemon(True)
        thread.start()
        self.listening_thread = thread

    def send_request(self, data):
        if not self.sock:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.HOST, self.port_use))

        self.sock.sendall(self.REQUEST % data)
        return

    def raw_request(self, string):
        # Do nothing if the string is empty or socket doesn't exist
        if len(string) > 0:
            self.send_request(string+"\n\n")
        return

    def join_room(self, query):
        paramaters = query.split()
        request = self.JOIN_HEADER % (paramaters[1], paramaters[2])
        return self.send_request(request)

    def leave_room(self, query):
        paramaters = query.split()
        request = self.LEAVE_HEADER % (paramaters[1], paramaters[2], paramaters[3])
        return self.send_request(request)

    def msg_room(self, query):
        paramaters = query.split()
        request = self.MESSAGE_HEADER % (paramaters[1], paramaters[2], paramaters[3], paramaters[4])
        return self.send_request(request)

    def disconnect(self, query):
        paramaters = query.split()
        request = self.LEAVE_HEADER % (paramaters[1], paramaters[2], paramaters[3])
        return self.send_request(request)

    def handler(self, message):
        if re.match(self.JOIN_SUCCESS_REGEX, message):
            self.join_handler(message)
        elif re.match(self.LEAVE_REPLY_REGEX, message):
            self.leave_handler(message)
        elif re.match(self.MESSAGE_REPLY_REGEX, message):
            self.msg_handler(message)
        elif re.match(self.NEW_JOIN_REGEX, message):
            logging.debug(message)
        else:
            logging.debug(message)
            return False
        return True

    def join_handler(self, request):
        logging.debug(request)
        request = request.splitlines()
        room_id = request[3].split()[1]
        client_id = request[4].split()[1]
        self.rooms[room_id][client_id] = True
        return

    def leave_handler(self, request):
        logging.debug(request)
        request = request.splitlines()
        room_id = request[0].split()[1]
        client_id = request[1].split()[1]
        if room_id in self.rooms.keys() and client_id in self.rooms[room_id].keys():
            del self.rooms[room_id][client_id]
        return

    def msg_handler(self, request):
        request = request.splitlines()
        room_id = request[0].split()[1]
        client_id = request[1].split()[1]
        msg = request[2].split()[1]
        logging.debug("Room: " + room_id + "\t Client: " + client_id + "\nMessage: \t" + msg)
        return


class ThreadHandler(threading.Thread):
    def __init__(self, sock, client, buffer_length):
        threading.Thread.__init__(self)
        self.socket = sock
        self.client = client
        self.buffer_length = buffer_length

    def run(self):
        # Thread loops and waits for connections to be added to the queue
        while True:
            message = ""
            # Loop and receive data
            while "\n\n" not in message:
                data = self.socket.recv(1024)
                message += data
                if len(data) < self.buffer_length:
                    break
            # If valid http request with message body
            if len(message) > 0:
                self.client.handler(message)


def main():
    try:
        if len(sys.argv) > 1 and sys.argv[1].isdigit():
            port = int(sys.argv[1])
            con = TCPClient(port)
        else:
            con = TCPClient()
    except socket.error, msg:
        print "Unable to create socket connection: " + str(msg)
        con = None
    while con:
        user_input = raw_input("Enter a message to send or type exit:")
        if user_input.lower() == "exit":
            con = None
        elif re.match(TCPClient.JOIN_REGEX, user_input.lower()):
            con.join_room(user_input)
        elif re.match(TCPClient.LEAVE_REGEX, user_input.lower()):
            con.leave_room(user_input)
        elif re.match(TCPClient.MSG_REGEX, user_input.lower()):
            con.msg_room(user_input)
        else:
            con.raw_request(user_input)


if __name__ == "__main__": main()
