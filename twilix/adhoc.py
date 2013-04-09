class BaseCommand(VElement):
    elementName = 'command'
    parentClass = Iq

class Command(BaseCommand):

    xmlns = 'http://jabber.org/protocol/commands'

    node = fields.StringAttr('node')
    sessionid = fields.StringAttr('sessionid')
    action = fields.StringAttr('action', required=False)
    status = fields.StringAttr('status', required=False)
    xml_lang = fields.StringAttr('xml:lang', required=False)


class MyCommandQuery(CommandQuery):
    parentClass = MyIQ

    def anyHandler(self):
        try:
            node = self.iq.command.node
        except:
            raise # node not found, send bad request
        if self.host._handlers.has_key(jid):
            if self.host._handlers[jid].has_key(node):
                self.host._handlers[jid][node]['execute'](self)
            else:
                raise #item not found
        elif self.host._handlers[''].has_key(node):
            self._handlers[''][node]['execute'](self)
        else:
            raise #item not found
        return EmptyStanza

class Commands(object):

    def __init__(self, dispatcher):
        self._handlers = {'':{}}
        self.dispatcher = dispatcher

    def init(self, disco=None):
        self.dispatcher.registerHandler((MyCommandQuery, self))

        if disco is not None:
            disco.root_info.addFeatures(Feature())

    def addCommand(self, node, command, jid=''):
        if not self._handlers.has_key(jid):
            self._handlers[jid] = {}
        if self._handlers[jid].has_key(node):
            raise #command exists
        else:
            self._handlers[jid][node] = {'execute':command}

    def delCommand(self, node, jid=''):
        if not self._handlers.has_key(jid):
            raise # JID not found
        elif not self._handlers[jid].has_key(node):
            raise # command not found
        else:
            del self._handlers[jid][node]

    def getCommand(self, node, jid=''):
        if not self._handlers.has_key(jid):
            raise # JID not found
        elif not self._handlers.has_key(node):
            raise # command not found
        else:
            return self._handlers[jid][node]

class CommandPrototype(object):
    # need to set self.initial in ancestor for the first form

    name = None #need to be overriden in ancestor
    count = 0

    def __init__(self, jid=''):
        self.sessioncount = 0
        self.sessions = {}
        self._jid = jid

    def init(self, commands):
        self._commands = commands
        self._commands.addCommand(self.name, self.Execute, self._jid)

    def getSessionID(self):
        self.count += 1
        return 'cmd-%s-%d'%(self.name, self.count)

    def Execute(self, request):
        try:
            session = request.command.sessionid
        except: #no sessionid in command
            session = None
        try:
            action = request.command.action
        except: #no action
            action = None
        if not action:
            action = 'execute'
        if self.session.has_key(session):
            if self.sessions[session]['jid'] == request.from_:
                if self.sessions[session]['actions'].has_key(action):
                    self.sessions[session]['actions'][action](request)
                else:
                    raise # have no such action, bad request
            else:
                raise # jid and sessionid dont match, bad request
        elif session:
            raise # have no session but have sessionid, bad request
        else:
            self.initial[action](request)
