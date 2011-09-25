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

import errno
import socket
import unittest

from tuntap.char_dev_harness import TunCharDevHarness, TapCharDevHarness
from tuntap.interface_harness import Address, InterfaceHarness
from tuntap.sockaddr import SockaddrIn, SockaddrIn6
from tuntap.tun_tap_harness import TunHarness, TapHarness

class TestInterface(unittest.TestCase):

    def __init__(self, name, harness):
        super(TestInterface, self).__init__(name)
        self.harness = harness

    def setUp(self):
        self.harness.start()

    def tearDown(self):
        self.harness.stop()

    def test_CloseWhileUp(self):
        self.harness.interface.flags |= InterfaceHarness.IFF_UP
        self.harness.char_dev.close()
        self.harness.start()

    def test_UpDown(self):
        self.harness.interface.flags |= InterfaceHarness.IFF_UP
        self.assertEquals(InterfaceHarness.IFF_UP,
                          self.harness.interface.flags & InterfaceHarness.IFF_UP)
        self.harness.interface.flags &= ~InterfaceHarness.IFF_UP
        self.assertEquals(0,
                          self.harness.interface.flags & InterfaceHarness.IFF_UP)

    def test_NetmaskAFFix(self):
        self.harness.interface.addIfAddr(local = self.harness.addr.sa_local,
                                         dst = self.harness.addr.sa_dst,
                                         mask = SockaddrIn(af = 0, addr = self.harness.addr.mask))
        self.assertEquals(socket.AF_INET, self.harness.interface.mask.af)

    def test_Address6(self):
        self.harness.interface.addIfAddr6(local = self.harness.addr6.sa_local,
                                          dst = self.harness.addr6.sa_dst,
                                          mask = self.harness.addr6.sa_mask)
        # Ideally, we'd check whether the correct address has been configured. Unfortunately,
        # SIOCGIFADDR_IN6 and friends don't work, getifaddrs is not easily available from python,
        # and the underlying NET_RT_IFLIST sysctl call is far from trivial.


class TestTunInterface(TestInterface):

    def __init__(self, name):
        super(TestTunInterface, self).__init__(name, TunHarness())

    def test_Flags(self):
        self.assertEquals(InterfaceHarness.IFF_POINTOPOINT |
                          InterfaceHarness.IFF_RUNNING |
                          InterfaceHarness.IFF_SIMPLEX |
                          InterfaceHarness.IFF_MULTICAST,
                          self.harness.interface.flags)
        
    def test_Address(self):
        self.harness.interface.addIfAddr(local = self.harness.addr.sa_local,
                                         dst = self.harness.addr.sa_dst,
                                         mask = self.harness.addr.sa_mask)
        self.assertEquals(self.harness.addr.local, self.harness.interface.addr.addr)
        self.assertEquals(self.harness.addr.dst, self.harness.interface.dstaddr.addr)
        self.assertEquals(self.harness.addr.mask, self.harness.interface.mask.addr)


class TestTapInterface(TestInterface):

    def __init__(self, name):
        super(TestTapInterface, self).__init__(name, TapHarness())

    def test_Flags(self):
        self.assertEquals(InterfaceHarness.IFF_BROADCAST |
                          InterfaceHarness.IFF_RUNNING |
                          InterfaceHarness.IFF_SIMPLEX |
                          InterfaceHarness.IFF_MULTICAST,
                          self.harness.interface.flags)

    def test_Address(self):
        self.harness.interface.addIfAddr(local = self.harness.addr.sa_local,
                                         dst = self.harness.addr.sa_dst,
                                         mask = self.harness.addr.sa_mask)
        self.assertEquals(self.harness.addr.local, self.harness.interface.addr.addr)
        self.assertEquals(self.harness.addr.dst, self.harness.interface.broadaddr.addr)
        self.assertEquals(self.harness.addr.mask, self.harness.interface.mask.addr)
