"""
Module provides stanzas which are used in Out-of-band Bytestream (XEP-0065).
"""

from twilix.stanzas import Query
from twilix.base.velement import VElement
from twilix import fields
from twilix import errors

from twilix.bytestreams.socks5 import SOCKS5_NS

class Socks5Query(Query):
    """
    Base class for socks5 queries.
    """

    elementUri = SOCKS5_NS

class Socks5QueryWithSid(Socks5Query):
    """
    Socks5 query containes sid.

    Attributes:
        sid -- session ID.
    """

    sid = fields.StringAttr('sid')

class StreamHost(VElement):
    """
    Class represents stanza contains information about the host.

    Attributes:
        rhost -- the IP address or DNS domain name of the host.

        jid -- the JabberID of the host for communication over XMPP.

        port -- the port on wich to connect for SOCKS5 communication.
    """

    elementName = 'streamhost'

    rhost = fields.StringAttr('host')
    jid = fields.JidAttr('jid')
    port = fields.StringAttr('port')

    def clean_port(self, value):
        try:
            value = int(value)
            assert value < 65536
        except (ValueError, TypeError, AssertionError):
            raise NotAcceptableException
        return value

class StreamHostUsed(VElement):
    """
    Specifies which StreamHost was used.

    Attributes:
        jid -- the JabberID of the host.
    """

    elementName = 'streamhost-used'

    jid = fields.JidAttr('jid')

class StreamHostUsedQuery(Socks5QueryWithSid):
    streamhost_used = fields.ElementNode(StreamHostUsed)

class StreamHostQuery(Socks5QueryWithSid):
    result_class = StreamHostUsedQuery

    streamhosts = fields.ElementNode(StreamHost, listed=True)

class GotStreamHost(Socks5Query):
    streamhost = fields.ElementNode(StreamHost)
    
class GetStreamHostsQuery(Socks5Query):
    result_class = GotStreamHost

class ActivateQuery(Socks5QueryWithSid):
    jid = fields.JidNode('activate')

