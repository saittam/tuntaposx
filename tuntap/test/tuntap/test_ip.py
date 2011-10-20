# Copyright (c) 2011 Mattias Nissler <mattias.nissler@gmx.de>
#
# Redistribution and use in source and binary forms, with or without modification, are permitted
# provided that the following conditions are met:
#
#   1. Redistributions of source code must retain the above copyright notice, this list of
#      conditions and the following disclaimer.
#   2. Redistributions in binary form must reproduce the above copyright notice, this list of
#      conditions and the following disclaimer in the documentation and/or other materials provided
#      with the distribution.
#   3. The name of the author may not be used to endorse or promote products derived from this
#      software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import functools
import socket
from unittest import TestCase

from tuntap.packet import IPv4Packet, IPv6Packet, UDPPacket

class TestIO(TestCase):

    def __init__(self, name, af, codec):
        super(TestIO, self).__init__(name)
        self._codec = codec(af)

    def __str__(self):
        return '%s [%s]' % (super(TestIO, self).__str__(), str(self._codec))

    def setUp(self):
        super(TestIO, self).setUp()
        self._codec.start()

    def tearDown(self):
        self._codec.stop()
        super(TestIO, self).tearDown()


class TestIp(TestIO):

    def __init__(self, name, codec):
        super(TestIp, self).__init__(name, socket.AF_INET, codec)

    def test_Send(self):
        payload = 'knock, knock!'
        port = 12345
        self._codec.sendUDP(payload, (self._codec.addr.remote, port))
        self._codec.expectPacket(
            { 'version': 4,
              'src': socket.inet_aton(self._codec.addr.local),
              'dst': socket.inet_aton(self._codec.addr.remote),
              'proto': IPv4Packet.PROTO_UDP,
              'payload': { 'dst': port,
                           'payload': payload } })
        self.assertTrue(self._codec.runPacket())

    def test_Recv(self):
        srcport = 23456
        payload = 'who\'s there?'
        packet = IPv4Packet(proto = IPv4Packet.PROTO_UDP,
                            src = socket.inet_aton(self._codec.addr.remote),
                            dst = socket.inet_aton(self._codec.addr.local),
                            payload = UDPPacket(src = srcport,
                                                dst = self._codec.UDPPort,
                                                payload = payload))
        self._codec.sendPacket(packet.encode())
        self._codec.expectUDP(payload)
        self.assertTrue(self._codec.runUDP())


class TestIp6(TestIO):

    def __init__(self, name, codec):
        super(TestIp6, self).__init__(name, socket.AF_INET6, codec)

    def test_Send(self):
        payload = 'knock, knock!'
        port = 12345
        self._codec.sendUDP(payload, (self._codec.addr.remote, port))
        self._codec.expectPacket(
            { 'version': 6,
              'src': socket.inet_pton(self._codec.af, self._codec.addr.local),
              'dst': socket.inet_pton(self._codec.af, self._codec.addr.remote),
              'proto': IPv6Packet.PROTO_UDP,
              'payload': { 'dst': port,
                           'payload': payload } })
        self.assertTrue(self._codec.runPacket())

    def test_Recv(self):
        srcport = 23456
        payload = 'who\'s there?'
        packet = IPv6Packet(proto = IPv6Packet.PROTO_UDP,
                            src = socket.inet_pton(self._codec.af, self._codec.addr.remote),
                            dst = socket.inet_pton(self._codec.af, self._codec.addr.local),
                            payload = UDPPacket(src = srcport,
                                                dst = self._codec.UDPPort,
                                                payload = payload))
        self._codec.sendPacket(packet.encode())
        self._codec.expectUDP(payload)
        self.assertTrue(self._codec.runUDP())
