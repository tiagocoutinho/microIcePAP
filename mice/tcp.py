import re
import time
import logging
import functools

import gevent
from gevent import socket, event, queue, lock

"""
connect
close
raw_read
read
readline
write
write_read
write_readline
flush
"""


def try_connect_socket(fu):
    @functools.wraps(fu)
    def rfunc(self, *args, **kwarg):
        write_func = fu.func_name.startswith('write')
        if(not self._connected and (not self._data or write_func)):
            self.connect()

        if not self._connected:
            prev_timeout = kwarg.get('timeout', None)
            kwarg.update({'timeout': 0.})
            try:
                return fu(self, *args, **kwarg)
            except RuntimeError:
                self.connect()
                kwarg.update({'timeout': prev_timeout})
        return fu(self, *args, **kwarg)
    return rfunc


class Socket:

    def __init__(self, host, port,
                 eol='\n',      # end of line for each rx message
                 timeout=5.,    # default timeout for read write
                 ):
        self._log = logging.getLogger('Sock({0}:{1})'.format(host, port))
        self._host = host
        self._port = port
        self._fd = None
        self._timeout = timeout
        self._connected = False
        self._eol = eol
        self._data = ''
        self._event = event.Event()
        self._raw_read_task = None
        self._lock = lock.Semaphore()

    def connect(self, host=None, port=None):
        local_host = host or self._host
        local_port = port or self._port

        if self._connected:
            self._fd.close()
            if self._raw_read_task:
                self._raw_read_task.join()
                self._raw_read_task = None

        self._fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._fd.connect((local_host, local_port))
        self._fd.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._log.debug('Connected!')
        self._connected = True
        self._host = local_host
        self._port = local_port
        self._data = ''
        self._raw_read_task = gevent.spawn(self._raw_read)
        return True

    def close(self):
        if self._connected:
            self._fd.shutdown(socket.SHUT_RDWR)
            self._fd.close()
            if self._raw_read_task:
                self._raw_read_task.join()
                self._raw_read_task = None
            self._data = ''

    @try_connect_socket
    def raw_read(self, maxsize=None, timeout=None):
        timeout_errmsg = "timeout on socket(%s, %d)" % (self._host, self._port)
        with gevent.Timeout(timeout or self._timeout,
                            RuntimeError(timeout_errmsg)):
            while not self._data:
                self._event.wait()
                self._event.clear()
        if maxsize:
            msg = self._data[:maxsize]
            self._data = self._data[maxsize:]
        else:
            msg = self._data
            self._data = ''
        return msg

    @try_connect_socket
    def read(self, size=1, timeout=None):
        timeout_errmsg = "timeout on socket(%s, %d)" % (self._host, self._port)
        with gevent.Timeout(timeout or self._timeout,
                            RuntimeError(timeout_errmsg)):
            while len(self._data) < size:
                self._event.wait()
                self._event.clear()
        msg = self._data[:size]
        self._data = self._data[size:]
        return msg

    @try_connect_socket
    def readline(self, eol=None, timeout=None):
        timeout_errmsg = "timeout on socket(%s, %d)" % (self._host, self._port)
        with gevent.Timeout(timeout or self._timeout,
                            RuntimeError(timeout_errmsg)):
            #local_timeout = timeout or self._timeout
            local_eol = eol or self._eol
            #start_time = time.time()
            eol_pos = self._data.find(local_eol)
            while eol_pos == -1:
                self._event.wait()
                self._event.clear()
                eol_pos = self._data.find(local_eol)

        msg = self._data[:eol_pos]
        self._data = self._data[eol_pos + len(local_eol):]
        return msg

    def _sendall(self, msg):
        self._log.debug("Tx: %r", msg)
        self._fd.sendall(msg)

    @try_connect_socket
    def write(self, msg, timeout=None):
        with self._lock:
            self._sendall(msg)

    @try_connect_socket
    def write_read(self, msg, write_synchro=None, size=1, timeout=None):
        with self._lock:
            self._sendall(msg)
            if write_synchro:
                write_synchro.notify()
            return self.read(size=size, timeout=timeout)

    @try_connect_socket
    def write_readline(self, msg, write_synchro=None, eol=None, timeout=None):
        with self._lock:
            with gevent.Timeout(timeout or self._timeout,
                                RuntimeError("write_readline timed out")):
                self._sendall(msg)
                if write_synchro:
                    write_synchro.notify()
                return self.readline(eol=eol, timeout=timeout)

    @try_connect_socket
    def write_readlines(
            self, msg, nb_lines, write_synchro=None, eol=None, timeout=None):
        with self._lock:
            with gevent.Timeout(timeout or self._timeout,
                                RuntimeError("write_readline timed out")):
                self._sendall(msg)
                if write_synchro:
                    write_synchro.notify()

                start_time = time.time()
                str_list = []
                for ii in range(nb_lines):
                    str_list.append(self.readline(eol=eol, timeout=timeout))

                    # Reduces timeout by duration of previous readline command.
                    if timeout:
                        timeout = timeout - (time.time() - start_time)
                        if timeout < 0:
                            timeout = 0

                    start_time = time.time()

                return str_list

    def flush(self):
        self._data = ''

    def _raw_read(self):
        try:
            while(1):
                raw_data = self._fd.recv(16 * 1024)
                self._log.debug("Rx: %r", raw_data)
                if raw_data:
                    self._data += raw_data
                    self._event.set()
                else:
                    break
        except:
            pass
        finally:
            self._connected = False
            self._fd.close()
            self._fd = None
