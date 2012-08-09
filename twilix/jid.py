"""Module extends the JID class from twisted library."""

import copy

from twisted.words.protocols.jabber.jid import JID, InvalidFormat

class MyJID(JID):
    """Extends class JID from twisted.words.protocols.jabber.jid."""
    @property
    def is_bare(self):
        """Checks for bare jid (without resourse part)."""
        return self.resource is None

    def bare(self):
        """Make bare jid from current jid (without resourse part)."""
        new = copy.copy(self)
        new.resource = None
        return new

    def __unicode__(self):
        """
        Override unicode converter.
        Return JID in user@server/resourse form.
        """
        r = self.host
        if self.user:
            r = self.user + '@' + r
        if self.resource:
            r += '/' + self.resource
        return r

    # map for transformations
    __escapedMap = {
        u' ' :u'\\20',
        u'"' :u'\\22',
        u'&' :u'\\26',
        u'\'':u'\\27',
        u'/' :u'\\2f',
        u':' :u'\\3a',
        u'<' :u'\\3c',
        u'>' :u'\\3e',
        u'@' :u'\\40',
        }

    @classmethod
    def _escapedTransform(cls, string):
        buf = ''
        for ch in string:
            if ch in cls.__escapedMap.keys():
                buf += cls.__escapedMap[ch]
            elif ch == '\\':
                l = cls.__escapedMap.values()
                l.append(u'\\5c')
                for elem in l:
                    place = string[string.find(ch):].find(elem)
                    if place == 0:
                        buf += u'\\5c'
                        break
                else:
                    buf += ch
            else:
                buf += ch
        return buf

    @classmethod
    def _unescapedTransform(cls, string):
        __unescapedMap = dict(map(None,
                                  cls.__escapedMap.values(),
                                  cls.__escapedMap.keys()
                                  ))
        __unescapedMap[u'\\5c'] = '\\'
        for k in __unescapedMap.keys():
            while True:
                place = string.find(k)
                if place == -1:
                    break
                else:
                    string = string[:place]+__unescapedMap[k]+string[place+3:]
        return string

    @classmethod
    def escaped(cls, user=None, host=None, res=None):
        """
        Transforms unescaped characters into escaped
        Returns MyJID instance with valid user and resource

        >>> host = 'example.com'
        >>> print MyJID.escaped('space cadet', host)
        JID(u'space\\\\20cadet@example.com')
        >>> print MyJID.escaped('call me "ishmael"', host)
        JID(u'call\\\\20me\\\\20\\\\22ishmael\\\\22@example.com')
        >>> print MyJID.escaped('at&t guy', host)
        JID(u'at\\\\26t\\\\20guy@example.com')
        >>> print MyJID.escaped("d'artagnan", host)
        JID(u'd\\\\27artagnan@example.com')
        >>> print MyJID.escaped('/.fanboy', host)
        JID(u'\\\\2f.fanboy@example.com')
        >>> print MyJID.escaped('::foo::', host)
        JID(u'\\\\3a\\\\3afoo\\\\3a\\\\3a@example.com')
        >>> print MyJID.escaped('<foo>', host)
        JID(u'\\\\3cfoo\\\\3e@example.com')
        >>> print MyJID.escaped('user@host', host)
        JID(u'user\\\\40host@example.com')
        >>> print MyJID.escaped('c:\\\\net', host)
        JID(u'c\\\\3a\\\\net@example.com')
        >>> print MyJID.escaped('c:\\\\\\\\net', host)
        JID(u'c\\\\3a\\\\\\\\net@example.com')
        >>> print MyJID.escaped('c:\\\\cool stuff', host)
        JID(u'c\\\\3a\\\\cool\\\\20stuff@example.com')
        >>> print MyJID.escaped('c:\\\\5commas', host)
        JID(u'c\\\\3a\\\\5c5commas@example.com')

        """
        if host is None:
            raise Exception('Cannot escape characters with empty host!')
        if user != None:
            user = cls._escapedTransform(user)
        if res != None:
            res = cls._escapedTransform(res)
        return cls(tuple=(user, host, res))

    @property
    def unescaped(self):
        """
        Transforms escaped characters into unescaped
        Returns unicode string

        

        """
        uJID = self.host
        if self.user:
            uJID = self._unescapedTransform(self.user) + '@' + uJID
        if self.resource:
            uJID += '/' + self._unescapedTransform(self.resource)

        return uJID

#buffer for recent string-to-jid conversations
__internJIDs = {}
 
def internJID(jidstring):
    """
    Creates and returns MyJID-type object from any jidstring 
    (with bufferization).
    """
    if jidstring in __internJIDs:
        j = __internJIDs[jidstring]
    else:
        j = MyJID(jidstring)
        __internJIDs[jidstring] = j
    j = copy.copy(j)
    return j

if __name__ == '__main__':
    import doctest
    doctest.testmod()
