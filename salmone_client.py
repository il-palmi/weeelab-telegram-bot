from twisted.internet import ssl, protocol, reactor
from twisted.internet.protocol import connectionDone
from twisted.protocols.basic import LineReceiver
from twisted.python import failure
from twisted.python.modules import getModule
from threading import Thread

receiver = None


class TLSClient(LineReceiver):
    def connectionMade(self):
        global receiver
        receiver = self
        self.sendLine(b"plain text")
        self.sendLine(b"STARTTLS")

    def lineReceived(self, line):
        print(f"received: {line}")
        if line == b"READY":
            self.transport.startTLS(self.factory.options)
            self.sendLine(b"secure text")

    def connectionLost(self, reason: failure.Failure = connectionDone):
        print(reason)

    def sendMsg(self, msg: str):
        if self is None:
            print("Cannot send message to server. No connection.")
        else:
            msg = msg.encode('utf-8')
            self.sendLine(msg)

    def disconnect(self):
        self.transport.loseConnection()


class ClientFactory(protocol.ClientFactory):
    protocol = TLSClient

    def __init__(self):
        self.cert = None
        self.certData = None

    def startFactory(self):
        self.certData = getModule(__name__).filePath.sibling('client.pem').getContent()
        self.cert = ssl.PrivateCertificate.loadPEM(self.certData)
        self.options = self.cert.options()
    
    def clientConnectionFailed(self, connector, reason):
        print("Connection failed.")

    def update(self, data):
        print(data)


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

    def send(self, msg: str):
        self.reactor.callFromThread(TLSClient.sendMsg, receiver, msg)

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
        if cmd == 'reconnect':
            r_thread.reconnect()
        else:
            r_thread.send(cmd)


if __name__ == '__main__':
    main()
