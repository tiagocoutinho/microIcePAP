import inspect
import weakref
import functools
import itertools
import collections

try:
  from collections import OrderedDict
except ImportError:
  from ordereddict import OrderedDict

from tcp import Socket

class IcePAPException(Exception):
  pass

class Attr(object):

  def __init__(self, name=None, dtype=float, read_only=False):
    if name is None:
      name = self.__class__.__name__.upper()
      name = name.replace("ATTR", "")
    self.name = name
    self._dtype = dtype
    self._read_only = read_only

  def __set__(self, device, value):
    if self._read_only:
      raise TypeError("Cannot change read-only attribute '{0}'".format(self.name))
    self.set(device, value)

  def __get__(self, device, owner):
    if device is None:
      return self
    return self.get(device)

  def __delete__(self, device):
    pass

  def set(self, device, value):
    device.socket.write("{0} {1}\n".format(self.name, value))

  def get(self, device):
    r = device.socket.write_readline("?{0}\n".format(self.name))
    return self._dtype(r.split()[1])


MAX_AXIS = 128

def iter_axis(start=None, stop=None, step=None, device=None):
  if start is None: start = 1
  if stop is None: stop = MAX_AXIS+1
  if step is None: step = 1
  for i in xrange(start, stop, step):
    if i % 10 > 8:
      continue
    yield i

_non_seq = str, unicode, buffer, bytes, bytearray

class AxisAttr(Attr):

  class attr:
    def __init__(self, device, parent):
      self.__device = device
      self.__parent = parent

    def __getitem__(self, item):
      if isinstance(item, slice):
        axes = iter_axis(start=item.start, stop=item.stop, step=item.step,
                         device=self.__device)
        self.__parent.get(self.__device, axes=axes)
      else:
        axes = item,
        return self.__parent.get(self.__device, axes=axes)[item]

    def __setitem__(self, item, value):
      return self.__parent.set(self.__device, value, axis=item)

    def __call__(self, *args, **kwargs):
      if kwargs: # a set operation
        pass
      else:
        return self.__parent.get(self.__device, axes=args)        


  def __init__(self, *args, **kwargs):
    Attr.__init__(self, *args, **kwargs)

  def set(self, device, value, axis=None):
    if self._read_only:
      raise TypeError("Cannot change read-only attribute '{0}'".format(self.name))
    if axis is None:
      return self.attr(device, self)
    else:
      device.socket.write("{0} {1} {2}\n".format(self.name, axis, value))

  def get(self, device, axes=None):
    if axes is None:
      return self.attr(device, self)
    axes = tuple(axes)
    axes_str = " ".join(map(str, axes))
    result = device.socket.write_readline("?{0} {1}\n".format(self.name, axes_str))
    try:
      result = map(self._dtype, result.split()[1:])
    except Exception as exc:
      msg = "Error getting {0!r}.{1}[{2}]: {3}".format(device, self.name, 
                                                       axes_str, result)
      raise IcePAPException(msg)
    return OrderedDict(zip(axes, result))


AttrRO = functools.partial(Attr, read_only=True)
AxisAttrInt = functools.partial(AxisAttr, dtype=int)


class IcePAP(object):

  help = Attr("HELP", dtype=str, read_only=True)

  velocity = AxisAttr("VELOCITY")
  acctime = AxisAttr("ACCTIME")
  pos = AxisAttr("POS")
  fpos = AxisAttr("FPOS")

  def __init__(self, host, port=5000):
    self.__s = Socket(host, port)

  @property
  def socket(self):
    return self.__s

  def __repr__(self):
    name, s = self.__class__.__name__, self.__s
    return "{0}({1}:{2})".format(name, s._host, s._port)


class Axis(object):

  def __init__(self, device, axis, name=None):
    self.__dict__.update(dict(device=device, axis=axis, name=name))

  def __get_obj(self, name):
    return getattr(self.device, name)

  def __getattr__(self, name):
    return self.__get_obj(name)[self.axis]

  def __setattr__(self, name, value):
    obj = self.__get_obj(name)
    obj[self.axis] = value

  def __dir__(self):
    return dir(self.device)


def get_axis(icepap, axis, config):
  axis = Axis(icepap, axis)
  for i in range(7):
    for k, v in config.items():
      setattr(axis, k, v)
  return axis
