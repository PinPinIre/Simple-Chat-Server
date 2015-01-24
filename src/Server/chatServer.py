# chatServer.py
# Lab 4 CS4032
# Cathal Geoghegan #11347076

import socket
import re
import sys
import hashlib
from tcpServer import TCPServer

import logging

logging.basicConfig(filename="sentMessage.log", level=logging.DEBUG)


class ChatServer(TCPServer):
    JOIN_REGEX = "JOIN_CHATROOM:[a-zA-Z0-9_]*\nCLIENT_IP:0\nPORT:0\nCLIENT_NAME:[a-zA-Z0-9_]*"
    LEAVE_REGEX = "LEAVE_CHATROOM: [0-9]*\nJOIN_ID: [0-9]*\nCLIENT_NAME: [a-zA-Z0-9_]*"
    MESSAGE_REGEX = "CHAT:[0-9]*\nJOIN_ID:[0-9]*\nCLIENT_NAME:[a-zA-Z0-9_]*\nMESSAGE:[a-zA-Z0-9_]*\n\n"
    DISCONNECT_REGEX = "DISCONNECT:0\nPORT:0\nCLIENT_NAME:[a-zA-Z0-9_]*\n"
    JOIN_REQUEST_RESPONSE_SUCCESS = "JOINED_CHATROOM:%s\nSERVER_IP:%s\nPORT:%s\nROOM_REF:%d\nJOIN_ID:%d\n"
    JOIN_REQUEST_RESPONSE_FAIL = "ERROR_CODE:%d\nERROR_DESCRIPTION:%s\n"
    LEAVE_REQUEST_RESPONSE_SUCCESS = "LEFT_CHATROOM:%s\nJOIN_ID:%s\n"
    LEAVE_REQUEST_RESPONSE_FAIL = LEAVE_REQUEST_RESPONSE_SUCCESS
    MESSAGE_RESPONSE = "CHAT:%s\nCLIENT_NAME:%s\nMESSAGE:%s\n\n"
    MESSAGE_HEADER = "CHAT:%s\nCLIENT_NAME:%s\nMESSAGE:%s\n\n"
    JOIN_MESSAGE = MESSAGE_HEADER

    def __init__(self, port_use=None):
        TCPServer.__init__(self, port_use, self.handler)
        self.rooms = dict()

    def handler(self, message, con, addr):
        if re.match(self.JOIN_REGEX, message):
            self.join(con, addr, message)
        elif re.match(self.LEAVE_REGEX, message):
            self.leave(con, addr, message)
        elif re.match(self.MESSAGE_REGEX, message):
            self.message(con, addr, message)
        elif re.match(self.DISCONNECT_REGEX, message):
            self.disconnect(con, addr, message)
        else:
            return False
        return True

    def join(self, con, addr, text):
        request = text.splitlines()
        room_name = request[0].split(":")[1]
        client_name = request[3].split(":")[1]

        hash_room_name = int(hashlib.md5(room_name).hexdigest(), 16)
        hash_client_name = int(hashlib.md5(client_name).hexdigest(), 16)

        if hash_room_name not in self.rooms:
            self.rooms[hash_room_name] = dict()
        if hash_client_name not in self.rooms[hash_room_name].keys():
            join_string = self.JOIN_MESSAGE % (str(hash_room_name), client_name, client_name + " has joined this chatroom.")
            self.rooms[hash_room_name][hash_client_name] = con
            return_string = self.JOIN_REQUEST_RESPONSE_SUCCESS % (room_name, self.HOST, self.PORT, hash_room_name, hash_client_name)
            logging.debug("Sending:\n" + return_string + "\n")
            con.sendall(return_string)
            clients = self.rooms[hash_room_name].keys()
            for client in clients:
                msg_con = self.rooms[hash_room_name][hash_client_name]
                msg_con.sendall(join_string)
                logging.debug("Sending:\n" + join_string + "\n")
        else:
            return_string = self.JOIN_REQUEST_RESPONSE_FAIL % (1, "Client already in room")
            con.sendall(return_string)
        return

    def leave(self, con, addr, text):
        request = text.splitlines()
        room_id = int(request[0].split()[1])
        client_id = int(request[1].split()[1])
        client_name = request[2].split()[1]
        return_string = self.LEAVE_REQUEST_RESPONSE_SUCCESS % (room_id, client_id)
        if room_id in self.rooms.keys() and client_id in self.rooms[room_id].keys():
            del self.rooms[room_id][client_id]
            clients = self.rooms[room_id].keys()
            for client in clients:
                msg_con = self.rooms[room_id][client]
                msg_con.sendall(return_string)
        con.sendall(return_string)
        logging.debug("Sending:\n" + return_string + "\n")
        return

    def message(self, con, addr, text):
        request = text.splitlines()
        room_id = int(request[0].split(":")[1])
        client_id = int(request[1].split(":")[1])
        client_name = request[2].split(":")[1]
        msg = request[3].split(":")[1]
        if room_id in self.rooms.keys() and client_id in self.rooms[room_id].keys():
            return_string = self.MESSAGE_RESPONSE % (room_id, client_name, msg)
            for client in self.rooms[room_id].keys():
                client_con = self.rooms[room_id][client]
                client_con.sendall(return_string)
        logging.debug("Sending:\n" + return_string + "\n")
        return

    def disconnect(self, con, addr, text):
        request = text.splitlines()
        client_id = int(request[1].split(":")[1])
        rooms = self.rooms.keys()
        for room in rooms:
            if client_id in self.rooms[room].keys():
                del self.rooms[room][client_id]
                clients = self.rooms[room].keys()
                for client in clients:
                    return_string = self.LEAVE_REQUEST_RESPONSE_SUCCESS % (room, client_id)
                    msg_con = self.rooms[room][client]
                    msg_con.sendall(return_string)
        con = None
        return


def main():
    try:
        if len(sys.argv) > 1 and sys.argv[1].isdigit():
            port = int(sys.argv[1])
            server = ChatServer(port)
        else:
            server = ChatServer()
        server.listen()
    except socket.error, msg:
        print "Unable to create socket connection: " + str(msg)
        con = None


if __name__ == "__main__": main()
