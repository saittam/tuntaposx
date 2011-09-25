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

import fcntl
import socket
import struct

from tuntap import ioctl
from tuntap.sockaddr import SockaddrIn, SockaddrIn6

class Address(object):
    """
    Wraps address parameters for an interface.
    """

    def __init__(self, af, local, remote, dst, mask):
        self.af = af
        self.local = local
        self.remote = remote
        self.dst = dst
        self.mask = mask

    def __makeSaProperty(name):
        def get(self):
            addrmap = { socket.AF_INET: SockaddrIn,
                        socket.AF_INET6: SockaddrIn6 }
            addr = getattr(self, name)
            if self.af not in addrmap:
                return None
            if addr == None:
                return addrmap[self.af](af = 0, addr = None)
            return addrmap[self.af](af = self.af, addr = addr)

        return property(get)

    sa_local = __makeSaProperty('local')
    sa_remote = __makeSaProperty('remote')
    sa_dst = __makeSaProperty('dst')
    sa_mask = __makeSaProperty('mask')


class InterfaceHarness(object):
    """
    Base class for network interface harnesses. Provides helpers to configure the interface.
    """

    SIOCSIFFLAGS = ioctl.IOC(ioctl.OUT, 'i', 16, '16s16s')
    SIOCGIFFLAGS = ioctl.IOC(ioctl.INOUT, 'i', 17, '16s16s')

    SIOCAIFADDR = ioctl.IOC(ioctl.OUT, 'i', 26, '16s16s16s16s')
    SIOCAIFADDR_IN6 = ioctl.IOC(ioctl.OUT, 'i', 26, '16s28s28s28sIQQII')
    SIOCGIFADDR = ioctl.IOC(ioctl.INOUT, 'i', 33, '16s16s')
    SIOCGIFDSTADDR = ioctl.IOC(ioctl.INOUT, 'i', 34, '16s16s')
    SIOCGIFBRDADDR = ioctl.IOC(ioctl.INOUT, 'i', 35, '16s16s')
    SIOCGIFNETMASK = ioctl.IOC(ioctl.INOUT, 'i', 37, '16s16s')

    IFF_UP          = 0x1
    IFF_BROADCAST   = 0x2
    IFF_DEBUG       = 0x4
    IFF_LOOPBACK    = 0x8
    IFF_POINTOPOINT = 0x10
    IFF_NOTRAILERS  = 0x20
    IFF_RUNNING     = 0x40
    IFF_NOARP       = 0x80
    IFF_PROMISC     = 0x100
    IFF_ALLMULTI    = 0x200
    IFF_OACTIVE     = 0x400
    IFF_SIMPLEX     = 0x800
    IFF_LINK0       = 0x1000
    IFF_LINK1       = 0x2000
    IFF_LINK2       = 0x4000
    IFF_MULTICAST   = 0x8000

    def __init__(self, class_name, unit):
        """
        Initializes the harness.

        Args:
            class_name: Interface class name.
            unit: The interface number.
        """
        self._class_name = class_name
        self._unit = unit

    def _ioctl(self, af, cmd, format, arg):
        """
        Performs a socket ioctl.

        Args:
            af: address family.
            cmd: the ioctl cmd.
            format: argument format description.
            arg: argument data tuple.

        Returns:
            Output data tuple.
        """
        s = socket.socket(af, socket.SOCK_DGRAM)
        try:
            return struct.unpack(format, fcntl.ioctl(s, cmd, struct.pack(format, *arg)))
        finally:
            s.close()

    @property
    def flags(self):
        """
        Retrieves the interface flags.

        Returns:
            The interface flags.
        """
        return self._ioctl(socket.AF_INET, self.SIOCGIFFLAGS, '16sH', (self.name, 0))[1]

    @flags.setter
    def flags(self, flags):
        """
        Sets new interface flags.

        Args:
            flags: new interface flags.
        """
        self._ioctl(socket.AF_INET, self.SIOCSIFFLAGS, '16sH', (self.name, flags))

    @property
    def name(self):
        """
        Gets the interface name.

        Returns:
            Full interface name.
        """
        return "%s%d" % (self._class_name, self._unit)

    def addIfAddr(self, local, dst, mask):
        """
        Set an interface address.

        Args:
            addr: local address.
            dst: broadcast address or destination address, respectively.
            mask: the netmask.
        """
        self._ioctl(socket.AF_INET, self.SIOCAIFADDR, '16s16s16s16s',
                    (self.name, local.encode(), dst.encode(), mask.encode()))

    @property
    def addr(self):
        return SockaddrIn.decode(self._ioctl(socket.AF_INET, self.SIOCGIFADDR,
                                             '16s16s', (self.name, ''))[1])

    @property
    def broadaddr(self):
        return SockaddrIn.decode(self._ioctl(socket.AF_INET, self.SIOCGIFBRDADDR,
                                             '16s16s', (self.name, ''))[1])

    @property
    def dstaddr(self):
        return SockaddrIn.decode(self._ioctl(socket.AF_INET, self.SIOCGIFDSTADDR,
                                             '16s16s', (self.name, ''))[1])

    @property
    def mask(self):
        return SockaddrIn.decode(self._ioctl(socket.AF_INET, self.SIOCGIFNETMASK,
                                             '16s16s', (self.name, ''))[1])

    def addIfAddr6(self, local, dst, mask):
        """
        Set an INET6 address for the interface.

        Args:
            local: local address.
            dst: destination address.
            mask: the netmask.
        """
        self._ioctl(socket.AF_INET6, self.SIOCAIFADDR_IN6, '16s28s28s28sIQQII',
                    (self.name, local.encode(), dst.encode(), mask.encode(),
                     0, 0, 0, 0xffffffff, 0xffffffff))
