"""
Module provides stanzas which are used in In-Band Bytestreams (XEP-0047).
"""

from twilix.stanzas import Query, Message
from twilix import errors
from twilix import fields
from twilix.base.velement import VElement

from twilix.bytestreams.ibb import IBB_NS

class IbbQuery(Query):
    """
    Base class for any IBB query.
    """

    elementUri = IBB_NS

class OpenQuery(IbbQuery):
    """
    Query for initiating an in-band bytestream.

    Attributes:
        block_size -- defines the maximum size in bytes of each data chunk.

        sid -- defines a unique session ID for this IBB session.

        stanza_type -- defines whether the data will be sent using IQ stanzas
                        or message stanzas.
    """

    elementName = 'open'

    block_size = fields.StringAttr('block-size')
    sid = fields.StringAttr('sid')
    stanza_type = fields.StringAttr('stanza', required=False)

    def clean_block_size(self, value):
        try:
            value = int(value)
            assert value <= 65535
        except (ValueError, TypeError, AssertionError):
            raise errors.BadRequestException
        return value

    def clean_stanza(self, value):
        if value not in ('iq', 'message'):
            raise errors.BadRequestException
        return value

class DataElement(VElement):
    """
    Class represents data element used to send data via IBB.

    Attributes:
        seq -- number that acts as a counter for data chunks sent in a
                particular direction within the session.

        sid -- ties the data chunk to particular IBB session.
    """

    elementName = 'data'
    elementUri = IBB_NS

    seq = fields.StringAttr('seq')
    sid = fields.StringAttr('sid')

    def clean_seq(self, value):
        try:
            value = int(value)
        except (ValueError, TypeError, AssertionError):
            raise errors.BadRequestException
        value = value % 65536
        return value

class DataQuery(DataElement, Query):
    """
    Query for data sending.
    """

    pass

class MessageDataQuery(DataElement):
    """
    Query for data sending vie message stanzas.
    """
    parentClass = Message

class CloseQuery(IbbQuery):
    """
    Query used to close IBB session.

    Attributes:
        sid -- session ID of the IBB to be closed.
    """

    elementName = 'close'

    sid = fields.StringAttr('sid')
