import inspect
import weakref
import functools

from tcp import Socket


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


class AxisAttr(Attr):

  class attr:
    def __init__(self, device, parent):
      self.__device = weakref.ref(device)
      self.__parent = weakref.ref(parent)
    def __getitem__(self, item):
      return self.__parent().get(self.__device(), axis=item)
    def __setitem__(self, item, value):
      return self.__parent().set(self.__device(), value, axis=item)

  def __init__(self, *args, **kwargs):
    Attr.__init__(self, *args, **kwargs)

  def set(self, device, value, axis=None):
    if self._read_only:
      raise TypeError("Cannot change read-only attribute '{0}'".format(self.name))
    if axis is None:
      return self.attr(device, self)
    else:
      device.socket.write("{0} {1} {2}\n".format(self.name, axis, value))

  def get(self, device, axis=None):
    if axis is None:
      return self.attr(device, self)
    else:
      r = device.socket.write_readline("?{0} {1}\n".format(self.name, axis))
      return self._dtype(r.split()[1])


AttrRO = functools.partial(Attr, read_only=True)
AxisAttrInt = functools.partial(AxisAttr, dtype=int)


class IcePAP(object):

  help = AttrRO("HELP")

  velocity = AxisAttr("VELOCITY")
  acctime = AxisAttr("ACCTIME")
  position = AxisAttr("FPOS")

  def __init__(self, host, port=5000):
    self.__s = Socket(host, port)

  @property
  def socket(self):
    return self.__s


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


def get_axis(axis, config):
  

icebcu2 = IcePAP('icebcu2')
