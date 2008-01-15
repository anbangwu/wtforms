"""
    wtforms.fields
    ~~~~~~~~~~~~~~
    
    TODO
    
    :copyright: 2007 by James Crasta, Thomas Johansson.
    :license: MIT, see LICENSE.txt for details.
"""
from datetime import datetime
from cgi import escape
from functools import partial

from wtforms.validators import ValidationError

def html_params(**kwargs):
    params = []
    for k,v in kwargs.iteritems():
        if k in ('class_', 'class__'):
            k = k[:-1]
        k = unicode(k)
        v = escape(unicode(v), quote=True)
        params.append(u'%s="%s"' % (k, v))
    return str.join(' ', params)

class Field(object):
    _formfield = True
    def __new__(cls, *args, **kwargs):
        if 'name' not in kwargs:
            x = partial(cls, *args, **kwargs)
            x._formfield = True
            return x
        else:
            return super(Field, cls).__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        form = kwargs['form']
        self.name = kwargs['name']
        self.id = kwargs.get('id', form._idprefix + self.name)
        self._label = args[0]
        self.validators = args[1:]
        self.data = None
        self.errors = []

    def __unicode__(self):
        return self()

    def __call__(self, **kwargs):
        raise NotImplementedError

    def _get_label(self):
        return '<label for="%s">%s</label>' % (self.id, self._label)
    label = property(_get_label)
        
    def _validate(self, *args):
        pass

    def process_data(self, value, has_formdata):
        self.data = value

    def process_formdata(self, valuelist):
        self.data = valuelist[0]

class SelectField(Field):
    def __init__(self, *args, **kwargs):
        super(SelectField, self).__init__(*args, **kwargs)
        self.checker = kwargs.pop('checker', str)
        self.choices = kwargs.pop('choices', None)

    def __call__(self, **kwargs):
        kwargs.setdefault('id', self.id)
        html = u'<select %s>' % html_params(name=self.name, **kwargs)
        for val,title in self.choices:
            options = {'value': val}
            if self._selected(val):
                options['selected'] = u'selected'
            html += u'<option %s>%s</option>' % (html_params(**options), escape(unicode(title)))
        html += u'</select>'
        return html

    def _selected(self, value):
        return (self.checker(value) == self.data)

    def process_data(self, value, has_formdata):
        self.data = self.checker(getattr(value, 'id', value))

    def process_formdata(self, valuelist):
        self.data = self.checker(valuelist[0])

    def _validate(self, *args):
        for v, _ in self.choices:
            if self.data == v:
                break
        else:
            raise ValidationError('Not a valid choice')

class SelectMultipleField(SelectField):
    def __call__(self, **kwargs):
        super(SelectMultipleField, self).__call__(multiple="multiple", **kwargs)

    def _selected(self, value):
        return (self.checker(value) in self.data)
        
    def process_formdata(self, valuelist):
        self.data = list(self.checker(x) for x in valuelist)
        
class TextField(Field):
    def __call__(self, **kwargs):
        kwargs.setdefault('id', self.id)
        kwargs.setdefault('type', 'text')
        return u'<input %s />' % html_params(name=self.name, value=self._value(), **kwargs) 

    def _value(self):
        return self.data and unicode(self.data) or u''

class TextAreaField(TextField):
    def __call__(self, **kwargs):
        kwargs.setdefault('id', self.id)
        return u'<textarea %s>%s</textarea>' % (html_params(name=self.name, **kwargs), escape(unicode(self._value())))

class PasswordField(TextField):
    def __call__(self, **kwargs):
        kwargs.setdefault('type', 'password')
        return super(PasswordField, self).__call__(**kwargs)
        
class IntegerField(TextField):
    """ Can be represented by a text-input """

    def _value(self):
        return self.data and unicode(self.data) or u'0'

    def process_formdata(self, valuelist):
        try:
            self.data = int(valuelist[0])
        except ValueError:
            pass

class BooleanField(Field):
    """ Represents a checkbox."""

    def __call__(self, **kwargs):
        kwargs.setdefault('id', self.id)
        kwargs.setdefault('type', 'checkbox')
        if self.data:
            kwargs['checked'] = u'checked'
        return u'<input %s />' % html_params(name=self.name, value=u'y', **kwargs)
    
    def process_data(self, value, has_formdata):
        self.data = has_formdata and False or value

    def process_formdata(self, valuelist):
        self.data = valuelist[0] == u'y'

class DateTimeField(TextField):
    """ Can be represented by one or multiple text-inputs """
    def __init__(self, *args, **kwargs):
        super(DateTimeField, self).__init__(*args, **kwargs)
        self.format = kwargs.pop('format', '%Y-%m-%d %H:%M:%S')

    def _value(self):
        return self.data and self.data.strftime(self.format) or u''

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            try:
                self.data = datetime.strptime(str.join(' ', valuelist), self.format)
            except ValueError:
                return u'Date is invalid.'

class SubmitField(BooleanField):
    """Allow checking if a given submit button has been pressed"""
    def __call__(self, **kwargs):
        kwargs.setdefault('id', self.id)
        kwargs.setdefault('type', 'submit')
        kwargs.setdefault('value', self._label)
        return u'<input %s />' % html_params(name=self.name, **kwargs) 

    def process_formdata(self, valuelist):
        self.data = (len(valuelist) > 0 and valuelist[0] != u'')

__all__ = ('SelectField', 'SelectMultipleField', 'TextField', 'IntegerField', 'BooleanField', 'DateTimeField', 'PasswordField', 'TextAreaField', 'SubmitField')
