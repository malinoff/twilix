from twilix.errors import NotImplementedError

class Session(object):

    min_sid = 0

    def __init__(self):
        self.info = {}

    def _gen_sid(self):
        self.min_sid += 1 # just for example purposes
        return self.min_sid

    def generate_sid(self, jid):
        if jid not in self.info:
            return Error # already has sid
        sid = self._gen_sid()
        self.info[jid] = (sid, None) # maybe default lifetime?
        return sid

    def set_lifetime(self, jid, time):
        # Should i check http://xmpp.org/extensions/xep-0050.html#impl-session
        # if jid != from attribute return Error # access error
        if jid not in self.info:
            return Error # no sid to set lifetime
        self.info[jid][1] = time

    def get_info(self, jid):
        # Should i check http://xmpp.org/extensions/xep-0050.html#impl-session
        # if jid != from attribute return Error # access error
        if jid not in self.info:
            return Error # no sid
        return self.info[jid]

class BaseCommand(object):

    node = # str
    action = # str
    status = # str

    def __init__(self, session, *args, **kwargs):
        self.session = session
        super(BaseCommand, self).__init__(*args, **kwargs)

    def onSubmit(self, form=None):
        pass

class Command(BaseCommand):

    def onSubmit(self, form=None):
        raise NotImplementedError

    def onNextStep(self, form=None):
        pass

class StaticCommand(Command):

    def __init__(self, session, forms, *args, **kwargs):
        self.forms = forms
        super(StaticCommand, self).__init__(session, *args, **kwargs)

    def onDone(self):
        pass
