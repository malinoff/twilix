"""
Module provides an XMPP protocol extension for data forms. (XEP-0004)
"""
import copy

from twilix.base.velement import VElement
from twilix.base.myelement import MyElement
from twilix.base.exceptions import ElementParseError
from twilix import fields as f

class ValidationError(Exception):
    """
    Raises when some form's data was not validated.
    """
    pass

class FormField(f.NodeProp):
    """
    Class to represent any form field.
    """

    def __init__(self, var, field_type, label=None, default=None, initial=None,
                 required=False, *args, **kwargs):
        """
        Creates form field.

        :param var: identifier of the field

        :param field_type: type of data stored in the field

        :param label: label associated with field

        :param default: default value of data

        :param initial: initial value of data

        :param required: is field required
        """
        self.var = var
        self.field_type = field_type
        self.initial = initial
        default = field_type(label=label, value=initial, var=var,
                             required=required, **kwargs)
        self.kwargs = kwargs
        super(FormField, self).__init__(field_type.elementName,
                                        listed=False, default=default,
                                        required=False)

    def __unicode__(self):
        return '%s %s FormField' % (self.var, self.field_type.fieldType)

    def get_from_el(self, el):
        r = filter(lambda r: \
                   not isinstance(r, (str, unicode)) and \
                   r.attributes.get('var', None) == self.var and \
                   getattr(r, 'name', None) == self.xmlnode,
                el.children)
        if r:
            return r[0]

    def to_python(self, value):
        if value is None:
            pass
        elif isinstance(value, VElement):
            pass
        else:
            value = self.field_type.createFromElement(value, **self.kwargs)
        return value

class Form(VElement):
    """
    Class to represent a form.

    Attributes:
        title -- used to label a whole form

        instructions -- natural-language instructions to be followed
    """

    elementName = 'x'
    elementUri = 'jabber:x:data'

    type_ = f.StringAttr('type')
    title = f.StringNode('title', required=False)
    instructions = f.StringNode('instructions', required=False)

    def clean_type_(self, value):
        if value not in ('form', 'submit', 'cancel', 'result'):
            raise ElementParseError
        return value

    def clean(self):
        if self.type_ != 'submit':
            return
        for fname in self.fields:
            field = getattr(self, fname)
            value = field.fclean(field.value)
            field.value = value

    @property
    def fields(self):
        fields = []
        for name, attr in self.nodesProps.items():
            if isinstance(attr, FormField):
                fields.append(name)
        return fields

    def make_submit_form(self):
        assert self.type_ == 'form'
        sform = copy.deepcopy(self)
        fields = sform.fields
        for name in fields:
            field = getattr(sform, name)
            field.prepare_to_submit()
            setattr(sform, name, field)
        sform.type_ = 'submit'
        sform.title = None
        sform.instructions = None
        return sform

    def make_cancel_form(self):
        assert self.type_ == 'form'
        sform = copy.deepcopy(self)
        sform.children = []
        sform.type_ = 'cancel'
        return sform

# TODO: ReportedForm
