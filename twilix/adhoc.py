from twilix.base import VElement
from twilix.base.myelement import EmptyStanza
from twilix.stanzas import Iq, MyIq
from twilix.errors import BadRequestException, ItemNotFoundException

class BaseCommandStanza(VElement):
    elementName = 'command'
    parentClass = Iq

class Command(BaseCommand):

    elementUri = 'http://jabber.org/protocol/commands'

    node = fields.StringAttr('node')
    sessionid = fields.StringAttr('sessionid', required=False)
    action = fields.StringAttr('action', required=False)
    status = fields.StringAttr('status', required=False)


class MyCommandQuery(Command):
    parentClass = MyIQ

    def setHandler(self):
        try:
            node = self.iq.command.node
        except:
            raise BadRequestException
        if self.host._handlers.has_key(jid):
            if self.host._handlers[jid].has_key(node):
                self.host._handlers[jid][node]['execute'](self)
            else:
                raise ItemNotFoundException
        elif self.host._handlers[''].has_key(node):
            self._handlers[''][node]['execute'](self)
        else:
            raise ItemNotFoundException
        return EmptyStanza()

class Commands(object):

    def __init__(self, dispatcher):
        self._handlers = {'':{}}
        self.dispatcher = dispatcher

    def init(self, disco=None):
        self.dispatcher.registerHandler((MyCommandQuery, self))

        if disco is not None:
            disco.root_info.addFeatures(Feature())

    def __setitem__(self, keys, command):
        if isinstance(keys, basestring):
            node, jid = keys, ''
        else:
            node, jid = keys[0], keys[1]
        if not self._handlers.has_key(jid):
            self._handlers[jid] = {}
        if self._handlers[jid].has_key(node):
            raise KeyError('Command exists')
        else:
            self._handlers[jid][node] = {'execute':command}

    def __delitem__(self, keys):
        if isinstance(keys, basestring):
            node, jid = keys, ''
        else:
            node, jid = keys[0], keys[1]
        if not self._handlers.has_key(jid):
            raise KeyError('JID not found')
        elif not self._handlers[jid].has_key(node):
            raise KeyError('Command not found')
        else:
            del self._handlers[jid][node]

    def __getitem__(self, keys):
        if isinstance(keys, basestring):
            node, jid = keys, ''
        else:
            node, jid = keys[0], keys[1]
        if not self._handlers.has_key(jid):
            raise KeyError('JID not found')
        elif not self._handlers.has_key(node):
            raise KeyError('Command not found')
        else:
            return self._handlers[jid][node]

class BaseCommand(object):
    # need to set self.initial in ancestor for the first form

    name = None #need to be overriden in ancestor
    count = 0

    def __init__(self, jid=''):
        self.sessioncount = 0
        self.sessions = {}
        self._jid = jid

    def init(self, commands):
        self._commands = commands
        self._commands.addCommand(self.name, self.execute, self._jid)

    def getSessionID(self):
        self.count += 1
        return 'cmd-%s-%d' % (self.name, self.count)

    def execute(self, request):
        session = request.command.getattr('sessionid', None)
        action = request.command.getattr('action', 'execute')
        if self.session.has_key(session):
            if (self.sessions[session]['jid'] == request.from_ and
                    self.sessions[session]['actions'].has_key(action)):
                self.sessions[session]['actions'][action](request)
            else:
                raise BadRequestException
        elif session:
            raise BadRequestException
        else:
            self.initial[action](request)
