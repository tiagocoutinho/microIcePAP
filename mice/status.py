from enum import Enum
from datetime import datetime
from collections import namedtuple


class Presence(Enum):
    NotPresent = 0
    UnResponsive = 1
    ConfigurationMode = 2
    Alive = 3


class Mode(Enum):
    Operation = 0
    Prog = 1
    Test = 2
    Fail = 3


class Disable(Enum):
    PowerEnabled = 0
    NotActive = 1
    Alarm = 2
    RemoteRackDisableInput = 3
    LocalRackDisableSwitch = 4
    RemoteAxisDisableInput = 5
    LocalAxisDisableSwitch = 6
    SoftwareDisable = 7


class Indexer(Enum):
    Internal = 0
    InSystem = 1
    External = 2
    Linked = 3


class StopCode(Enum):
    End = 0
    Stop = 1
    Abort = 2
    PositiveLimit = 3
    NegativeLimit = 4
    Config = 5
    Disabled = 6
    InternalFailure = 8
    MotorFailure = 9
    PowerOverload = 10
    DriverOverheating = 11
    CloseLoopError = 12
    EncoderError = 13
    ExternalAlarm = 15


#                   name          mask  shift  decoder
StatusFields = (('presence',      0b11,   0,  Presence),
                ('mode',          0b11,   2,  Mode),
                ('disable',       0b111,  4,  Disable),
                ('indexer',       0b11,   7,  Indexer),
                ('ready',         0b1,    9,  bool),
                ('moving',        0b1,    10, bool),
                ('settling' ,     0b1,    11, bool),
                ('out_of_window', 0b1,    12, bool),
                ('warning',       0b1,    13, bool),
                ('stopcode',      0b1111, 14, StopCode),
                ('pos_limit',     0b1,    18, bool),
                ('neg_limit',     0b1,    19, bool),
                ('home',          0b1,    20, bool),
                ('aux_power',     0b1,    21, bool),
                ('version_error', 0b1,    22, bool),
                ('power',         0b1,    23, bool),
                ('info',          0xFF,   24, int))

Status = namedtuple('Status', [f[0] for f in StatusFields])


def to_status(status_word):
    status_word = int(status_word, 0)
    fields = {}
    for (name, mask, shift, decode) in StatusFields:
        fields[name] = decode((status_word >> shift) & mask)
    return Status(**fields)


def power(icepap, axis, onoff):
    onoff = 'ON' if str(onoff).lower() in ['1', 'true', 'on', 'yes'] else 'OFF'
    start = datetime.now()
    print '%s [START] power %s' % (start, onoff)
    r = icepap.write_readline('#{0}:POWER {1}\n'.format(axis, onoff))
#    r = icepap.write('{0}:POWER {1}\n'.format(axis, onoff))
    end = datetime.now()
    print '%s [ END ] power %s (%s)' % (end, onoff, (end-start))
    return r

