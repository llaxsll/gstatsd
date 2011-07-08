import sys
import time
import collections
import json

import SocketServer
import BaseHTTPServer
import CGIHTTPServer
import threading
import sys
import threading
from gevent import socket

# local
from sink import Sink

# Aggregate
class StatAggregate(object):
    """
        A class to perform logging and aggrigation of log data
    """
    def __init__(self):
        self.stat_window = collections.deque(maxlen=15)
        self.current_frame = {}
        self.stat_window.append(self.current_frame)        
        self.last_frame_time = time.time()
        self.frame_interval = 60

    def _move_frame_forward(self):
        self.last_frame_time += self.frame_interval
        self.stat_window.append({})
        self.current_frame = self.stat_window[len(self.stat_window)-1]

    def _ensure_dict(self, dictionary, prop):
        if prop not in dictionary:
            dictionary[prop] = {}

    def _ensure_counter(self, dictionary, prop):
        if prop not in dictionary:
            dictionary[prop] = collections.Counter()

    def _adjust_stat_frame(self):
        current_frame_time = time.time()

        while (current_frame_time - self.last_frame_time > self.frame_interval):
            self._move_frame_forward()

    def _handle_number_count(self, current_namespace, stat_category, stat):
        self._ensure_counter(current_namespace, stat_category)

        current_namespace[stat_category].update({stat_category:stat})

    def _handle_str_count(self, current_namespace, stat_category, stat):
        self._ensure_counter(current_namespace, stat_category)

        current_namespace[stat_category].update({stat:1})

    def _handle_func_stat(self, current_namespace, stat_category, stat, func):
        self._ensure_counter(current_namespace, stat_category)

        current_namespace[stat_category]['function'] = func

        if func == 'max':
            current_namespace[stat_category][stat_category] = max( current_namespace[stat_category][stat_category], stat)
        if func == 'max':
            current_namespace[stat_category][stat_category] = min( current_namespace[stat_category][stat_category], stat)
        elif func == 'avg':
            current_namespace[stat_category].update( {stat_category:stat, 'count':1})
        elif func == 'sum':
            current_namespace[stat_category].update( {stat_category:stat, 'count':1})
        elif func == 'count':
            current_namespace[stat_category].update({stat:1})

    def _combine_frames(self, frame_count, full_only):
        frame_start = max(len(self.stat_window)-frame_count,0)
        frame_end = len(self.stat_window)
        
        if full_only:
            frame_start-=1
            frame_end-=1
            
        frames_to_combine = list(self.stat_window)[frame_start:frame_end]

        total_frame = {}
        for frame in frames_to_combine:
            for namespace_key in frame:
                self._ensure_dict(total_frame, namespace_key)

                for stat_key in frame[namespace_key]:
                    self._ensure_counter(total_frame[namespace_key], stat_key)

                    stat = frame[namespace_key][stat_key]
                    total_stat = total_frame[namespace_key][stat_key]

                    if stat['function'] in ['max']:
                       total_stat[stat_key] = max( total_stat[stat_key], stat[stat_key] )
                    elif stat['function'] in ['min']:
                       total_stat[stat_key] = min( total_stat[stat_key], stat[stat_key] )
                    elif stat['function'] in ['avg','sum']:
                       total_stat.update(stat)
                    elif stat['function'] in ['count']:
                        total_stat.update(stat)
                    else:
                        raise ValueError('Unsupported function')

                    total_stat['function'] = stat['function']
        return total_frame

    def _format_numeric(self, value):
        if isinstance(value,int):
            return value
        else:
            return round(value,2)
            
    def _dump_frames(self):
        i = 0
        for frame in list(self.stat_window):
            i = 0
            print "{0}: {1}".format(i, frame)

    def stat(self, namespace, **kwargs):
        self._adjust_stat_frame()

        if namespace not in self.current_frame :
            self.current_frame[namespace] = {}
        current_namespace =self.current_frame[namespace]

        for item in kwargs.items():
            stat_category = item[0]
            stat = item[1]

            if isinstance(stat, str):
                self._handle_func_stat(current_namespace, stat_category, stat, 'count')
            elif isinstance(stat, tuple):
                if len(stat) is not 2:
                    raise ValueError('Formula stat is in the form of (number, function)')

                if not isinstance(stat[0],int) and not isinstance(stat[0],float):
                    raise ValueError('Stat is not numeric')

                self._handle_func_stat(current_namespace, stat_category, stat[0], stat[1])
            elif isinstance(stat, int) or isinstance(stat, float):
                self._handle_func_stat(current_namespace, stat_category, stat, 'sum')

            else:
                raise ValueError('Dont know how to handle stat arg')

    def collect(self, frames = 1, full_only = False):
        self._adjust_stat_frame()

        frame = {'last_frame_time':int(self.last_frame_time)}
        combined_frame = self._combine_frames(frames, full_only)
        for namespace in combined_frame:
            frame[namespace] = {}

            for stat in combined_frame[namespace].items():
                stat_counter = stat[1]
                stat_key = stat[0]

                if stat_counter['function'] in ['sum', 'max','min']:
                    frame[namespace][stat_key] =  self._format_numeric(stat_counter[stat_key])
                elif stat_counter['function'] in ['avg']:
                    frame[namespace][stat_key] =  self._format_numeric(float(stat_counter[stat_key]) / stat_counter['count'])
                elif stat_counter['function'] in ['count']:
                    frame[namespace][stat_key] = {}

                    for item in stat_counter.items():
                        if item[0] in ['function']:
                            continue

                        frame[namespace][stat_key][item[0]] = item[1]
        return frame

# Reporting Interface
class ThreadingCGIServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass

class ReportStatRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def __init__(self,req,client_addr,server):
        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self,req,client_addr,server)
        self.server = server

    def do_GET(self):
            args = self.path.split('/')
            frames = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1
            full_only = True if len(args) > 2 and args[2] == 'full' else False
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(json.dumps(self.server.sink.aggregate.collect(frames, full_only)))

class ReportStatThread(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port

    def run( self ):
        server = ThreadingCGIServer(('', self.port), ReportStatRequestHandler)
        server.sink = self.sink

        server.serve_forever()

# vendor sink
class LoadSink(Sink):
    """
    Keeps a load track of the service
    """

    def __init__(self):
        self._hosts = []
        self.aggregate = StatAggregate()
        
    def add(self, spec):
        self._hosts.append(self._parse_hostport(spec))

        self.report = ReportStatThread(self._parse_hostport(spec)[1])
        self.report.setDaemon(True)
        self.report.sink = self
        self.report.start()


    def send(self, stats):
        "Format stats and send to one or more Graphite hosts"
        now = int(time.time())
        num_stats = 0

        # timer stats
        pct = stats.percent
        timers = stats.timers
        for key, vals in timers.iteritems():
            if not vals:
                continue

            # compute statistics
            num = len(vals)
            vals = sorted(vals)
            vmin = vals[0]
            vmax = vals[-1]
            mean = vmin
            vsum = sum(vals)
            max_at_thresh = vmax
            if num > 1:
                idx = round((pct / 100.0) * num)
                tmp = vals[:int(idx)]
                if tmp:
                    max_at_thresh = tmp[-1]
                    mean = sum(tmp) / idx

            key = 'stats.timers.%s' % key

            self.aggregate.stat('Stat',**{'%s.sum' % (key): (vsum,'sum')})
            self.aggregate.stat('Stat',**{'%s.upper' % (key): (vmax,'max')})
            self.aggregate.stat('Stat',**{'%s.lower' % (key): (vmin,'min')})
            self.aggregate.stat('Stat',**{'%s.count' % (key): (num,'sum')})
            self.aggregate.stat('Stat',**{'%s.mean' % (key): (mean,'avg')})
            num_stats += 1

    
        # counter stats
        counts = stats.counts
        for key, val in counts.iteritems():
            self.aggregate.stat('Stat',**{'%s' % (key): val})
            num_stats += 1

