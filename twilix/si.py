"""
Module implements http://jabber.org/protocol/si/profile/file-transfer feature
(XEP-0096), based on stream initiation feature (XEP-0095).

You can use this to send and receive files.
"""

import uuid
from UserDict import UserDict

from twisted.internet import defer, reactor

from twilix.base.velement import VElement
from twilix import fields
from twilix.forms import Form, FormField, fields as ff
from twilix.disco import Feature as DiscoFeature
from twilix.stanzas import Query, Iq
from twilix import errors

class ConnectionAborted(Exception):
    """ Raised when connection was closed unexpectidly by a remote side.
    Usually, it means that remote side aborted a transfer. """

class FeatureForm(Form):
    """
    Extends Form class.
    Use this to assemble x stanza with the type of 'form' contains
    field with all needed stream methods.

    :param methods: All needed stream methods you want to add.

    """
    def __init__(self, methods=(), *args, **kwargs):
        options = [ff.Option(value=method) for method in methods]
        self.nodesProps['stream_method'] = \
            FormField('stream-method', ff.ListSingleField, required=True,
                        options=options)
        super(FeatureForm, self).__init__(*args, **kwargs)

class Feature(VElement):
    """
    Extends VElement class.
    The base class for feature stanzas with the child,
    which is FeatureForm class.
    """
    elementName = 'feature'
    elementUri = 'http://jabber.org/protocol/feature-neg'

    methods = fields.ElementNode(FeatureForm)

class SIElement(Query):
    """
    Extends Query class.
    The base class for si queries.
    """
    elementName = 'si'
    elementUri = 'http://jabber.org/protocol/si'

    feature = fields.ElementNode(Feature)

class SIResponse(SIElement):
    """
    Result class for the si queries.
    """

class SIRequest(SIElement):
    """
    The class for handling si requests.
    """
    result_class = SIResponse
    # TODO: error_class

    mime_type = fields.StringAttr('mime-type', required=False)
    id_ = fields.StringAttr('id')
    profile = fields.StringAttr('profile')

    def make_reply(self, si):
        meta = {}
        streams = si.streams
        allowed = None
        for method in self.feature.methods.stream_method.options:
            if method.value in streams.keys():
                allowed = method.value
                break
        if not allowed:
            # TODO: application specific error
            raise errors.BadRequestException
        reply_form = self.feature.methods.make_submit_form()
        reply_form.stream_method.value = allowed
        feature = Feature(methods=reply_form)
        reply = self.result_class(feature=feature,
                                  parent=self.iq.makeResult())
        si.receive(allowed, self.id_, self.iq.from_, meta)
        sid = self.id_

        def canceller(_):
            stream = si.streams[allowed]
            stream.unregisterSession(sid=sid)

        deferred = defer.Deferred(canceller)
        return reply, deferred, meta
   
class SIProfile(object):
    """
    Defines profile for si protocol.
    """
    handlerClass = SIRequest
    def __init__(self, si):
        self.si = si

class Streams(UserDict):
    def __init__(self):
        UserDict.__init__(self)
        self._keys = []

    def __setitem__(self, key, value):
        self._keys.append(key)
        UserDict.__setitem__(self, key, value)

    def __delitem__(self, key):
        UserDict.__delitem__(self, key)
        self._keys.remove(key)

    def keys(self):
        return self._keys

class SI(object):
    """
    The main class for si-based file transfer.

    :param dispatcher: Dispatcher instance to be used with the service.

    :param streams: Streams to be used in file transfer.
    """
    def __init__(self, dispatcher, streams):
        self.dispatcher = dispatcher
        self.streams = Streams()
        for stream in streams:
            self.streams[stream.NS] = stream

    def init(self, disco=None, iq_validator=None):
        """
        Adds the feature in disco.

        :param disco: Client's disco instance.

        :param iq_validator: Validator for proper parsing.
        """
        self.iq_validator = iq_validator
        if disco is not None:
            disco.root_info.addFeatures(DiscoFeature(var=SIElement.elementUri))
        self.disco = disco

    def register_profile(self, profile, *args, **kwargs):
        """
        Registers profile and it's handler and adds feature in disco.

        :param profile: Profile to be registrated.
        """
        profile = profile(self, *args, **kwargs)

        h_cl = profile.handlerClass
        if self.iq_validator:
            h_cl = h_cl.redefineProperty('parentClass', self.iq_validator)

        self.dispatcher.registerHandler((h_cl, profile))
        self.disco.root_info.addFeatures(DiscoFeature(var=profile.NS))
        return profile

    @defer.inlineCallbacks
    def initiate(self, request, to, from_=None):
        """
        Initiates file transfer.

        :param request: Request to sent.

        :param to: Destination JID.

        :param from_: Source JID.
        """
        fform = FeatureForm(methods=self.streams.keys(), type_='form')
        feature = Feature(methods=fform)
        request.feature = feature

        if from_ is None:
            from_ = self.dispatcher.myjid

        iq = Iq(from_=from_, to=to, type_='set')
        request.id_ = sid = unicode(uuid.uuid4())
        iq.link(request)

        result = yield self.dispatcher.send(iq)
        form = FeatureForm.createFromElement(result.feature.methods,
                                             methods=self.streams.keys())
        form.validate()

        method = form.stream_method.value
        stream = self.streams[method]
        yield stream.requestStream(to, lambda _buf, _meta:None, sid,
                                   from_=from_)
        defer.returnValue((stream, sid))

    def receive(self, method, sid, initiator, meta, timeout=60):
        """
        Receives data.

        :param method: Defines stream to be used.

        :param sid: Transfer's id.

        :param initiator: ???

        :param meta: ???

        :param timeout: Time in seconds.
        """
        stream = self.streams[method]
        stream.registerSession(sid, initiator, self.dispatcher.myjid,
                               self.stream_cb, meta)
        meta['timeout'] = TimeOut(timeout, stream, sid)

    def stream_cb(self, buf, meta):
        count_size = meta.has_key('size')
        if buf is not None:
            if meta.has_key('buf'):
                meta['buf'].write(buf)
            if count_size:
                meta['timeout'].reset()
                meta['bytes_read'] += len(buf)
                if meta['size'] <= meta['bytes_read']:
                    meta['timeout'].cancel()
                    meta['deferred'].callback(meta)
            if meta.has_key('receive_cb'):
                meta['receive_cb'](buf, meta)
        elif count_size and meta['bytes_read'] != meta['size']:
            meta['deferred'].errback(ConnectionAborted)
            meta['timeout'].cancel()
        elif not meta['deferred'].called:
            meta['deferred'].callback(meta)

class TimeOut(object):
    def __init__(self, timeout, stream, sid):
        self.timeout = timeout
        self.stream = stream
        self.sid = sid
        self.__timeout_call = None
    def fire(self):
        self.__timeout_call = None
        self.stream.unregisterSession(sid=self.sid)
    def reset(self):
        if self.__timeout_call is None:
            self.set()
        else:
            self.__timeout_call.reset(self.timeout)
    def set(self):
        self.__timeout_call = reactor.callLater(self.timeout, self.fire)
    def cancel(self):
        if self.__timeout_call:
            self.__timeout_call.cancel()
            self.__timeout_call = None
