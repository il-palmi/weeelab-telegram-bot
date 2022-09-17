'''
This is an example client for salmone.
'''
import builtins
import threading

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    filters,
    CallbackQueryHandler,
    CallbackContext,
    MessageHandler,
    InlineQueryHandler,
)
from twisted.internet import ssl, protocol, reactor
from twisted.internet.protocol import connectionDone
from twisted.protocols.basic import LineReceiver
from twisted.python import failure
from twisted.python.modules import getModule
from threading import Thread
from salmone_standard_messages import *
import json
import os

receiver = None


class TLSClient(LineReceiver):
    def connectionMade(self):
        global receiver
        receiver = self
        message = json.dumps(TLS_HANDSHAKE).encode("utf-8")
        self.sendLine(message)

    def lineReceived(self, line):
        self.factory: ClientFactory
        print(f"CLIENT_THREAD -- received: {line}")
        if line == b"TLS_READY":
            self.transport.startTLS(self.factory.options)
        else:
            try:
                line = line.decode("utf-8")
                self.factory.send_update(line)
            except builtins.AttributeError as exc:
                if "NoneType" in str(exc):
                    print("CLIENT_THREAD -- ERROR: Trying to disconnect but no connection established.")


    def connectionLost(self, reason: failure.Failure = connectionDone):
        print(f"CLIENT_THREAD -- {reason.getErrorMessage()}")

    def sendMsg(self, msg: str):
        if self is None:
            print("CLIENT_THREAD -- Cannot send message to server. No connection.")
        else:
            msg = msg.encode('utf-8')
            self.sendLine(msg)

    def disconnect(self):
        self.transport.loseConnection()


class ClientFactory(protocol.ClientFactory):
    protocol = TLSClient
    chat_id = Update
    context = ContextTypes.DEFAULT_TYPE

    def __init__(self):
        self.cert = None
        self.certData = None

    def startFactory(self):
        self.check_certificate()
        with open("client.pem", "r") as file:
            self.certData = file.read()
        self.cert = ssl.PrivateCertificate.loadPEM(self.certData)
        self.options = self.cert.options()

    def clientConnectionFailed(self, connector, reason):
        print("CLIENT_THREAD -- Connection failed.")

    def update(self, data):
        print(f"CLIENT_THREAD -- {data}")

    def check_certificate(self):
        if os.path.exists("client.pem"):
            try:
                certData = getModule(__name__).filePath.sibling('client.pem').getContent()
                ssl.PrivateCertificate.loadPEM(certData)
            except:
                print("CLIENT_THREAD -- ERROR: Certificate expired or not valid.")
                self.generate_certificate()
        else:
            self.generate_certificate()

    @staticmethod
    def generate_certificate():
        os.system('openssl req -new -x509 -config openssl.cnf -nodes -days 365 -keyout client.pem -out client.pem')

    def send_update(self, data: str):
        self.context.bot.send_message(
            chat_id=self.chat_id.effective_chat.id,
            text=data
        )


class ReactorThread(Thread):
    def __init__(self, host: str, port: int):
        Thread.__init__(self)
        self.host = host
        self.port = port
        self.protocol = TLSClient
        self.factory = ClientFactory()
        self.reactor = reactor

    def run(self):
        self.reactor.connectTCP(self.host, self.port, self.factory)
        self.reactor.run(installSignalHandlers=False)

    def stop(self):
        self.reactor.callFromThread(TLSClient.disconnect, receiver)

    def send(self, update: Update, context: ContextTypes.DEFAULT_TYPE, msg: str):
        self.reactor.callFromThread(TLSClient.sendMsg, receiver, update, context, msg)

    def reconnect(self):
        self.reactor.connectTCP(self.host, self.port, self.factory)
        self.reactor.callFromThread(TLSClient.disconnect, receiver)


def main():
    host = "127.0.0.1"
    port = 1234
    r_thread = ReactorThread(host, port)
    r_thread.start()
    while True:
        cmd = input()
        match cmd:
            case 'reconnect':
                r_thread.reconnect()
            case 'auth':
                message = authorization_command("polmi")
                r_thread.send(message)
            case _:
                r_thread.send(cmd)


if __name__ == '__main__':
    main()
