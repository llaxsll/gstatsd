
# standard
import cStringIO
import sys
import time

# vendor
from gevent import socket

E_BADSPEC = "bad sink spec %r: %s"
E_SENDFAIL = 'failed to send stats to %s %s: %s'


class Sink(object):

    """
    A resource to which stats will be sent.
    """

    def error(self, msg):
        sys.stderr.write(msg + '\n')

    def _parse_hostport(self, spec):
        try:
            parts = spec.split(':')
            if len(parts) == 2:
                return (parts[0], int(parts[1]))
            if len(parts) == 1:
                return ('', int(parts[0]))
        except ValueError, ex:
            raise ValueError(E_BADSPEC % (spec, ex))
        raise ValueError("expected '[host]:port' but got %r" % spec)

