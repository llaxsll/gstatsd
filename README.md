
gstatsd - A statsd service implementation in Python + gevent.

If you are unfamiliar with statsd, you can read [why statsd exists][etsy post],
or look at the [NodeJS statsd implementation][etsy repo].

License: [Apache 2.0][license]

Requirements
------------

 * [Python][python] - I'm testing on 2.6/2.7 at the moment.
 * [gevent][gevent] - A libevent wrapper.
 * [distribute][distribute] - (or setuptools) for builds.


Using gstatsd
-------------

Show gstatsd help:

    % gstatsd -h

Options:

    Usage: gstatsd [options]

     A statsd service in Python + gevent.

    Options:
      --version             show program's version number and exit
      -b BIND_ADDR, --bind=BIND_ADDR
                            bind [host]:port (host defaults to '')
      -s SINK, --sink=SINK  a graphite service to which stats are sent
                            ([host]:port).
      -t SINK_TYPE, --type=SINK_TYPE
                            sink type graphite, load (default graphite)
      -v                    increase verbosity (currently used for debugging)
      -f INTERVAL, --flush=INTERVAL
                            flush interval, in seconds (default 10)
      -p PERCENT, --percent=PERCENT
                            percent threshold (default 90)
      -D, --daemonize       daemonize the service
      -h, --help

Start gstatsd listening on the default port 8125, and send stats to graphite
server on port 2003 every 5 seconds:

    % gstatsd -s 2003 -f 5

Bind listener to host 'foo' port 8126, and send stats to the Graphite server
on host 'bar' port 2003 every 20 seconds:

    % gstatsd -b foo:8126 -s bar:2003 -f 20

To send the stats to multiple graphite servers, specify '-s' multiple times:

    % gstatsd -b :8125 -s stats1:2003 -s stats2:2004

You can also use a sink type different than graphite. Right now the other
supported option is a custom internal aggregator(load), that can be queried
via HTTP for aggregated stats over a period of time. It is SNMP friendly 
and can be used by a stateless SNMP script that can extract and emit OIDs over
a period of time. It can also be used to report load-style stats - that is 
report ( 1 min, 5 min, 15 min ) stat aggregates. 

    % gstatsd -b :8125 -s localhost:8082 -t load

Request aggregate stats over period of time :

    % curl "http://localhost:8082/1"   # last 1 minute
    % curl "http://localhost:8082/5"   # last 5 minutes
    % curl "http://localhost:8082/15"  # last 15 minutes

    % curl "http://localhost:8082/1/full" # last full frame ( complete 60 sec of data)
      

Using the client
----------------

The code example below demonstrates using the low-level client interface:

    from gstatsd import client

    # location of the statsd server
    hostport = ('', 8125)

    raw = client.StatsClient(hostport)

    # add 1 to the 'foo' bucket
    raw.increment('foo')

    # timer 'bar' took 25ms to complete
    raw.timer('bar', 25)


You may prefer to use the stateful client:

    # wraps the raw client
    cli = client.Stats(raw)

    timer = cli.get_timer('foo')
    timer.start()

    ... do some work ..

    # when .stop() is called, the stat is sent to the server
    timer.stop()


[python]: http://www.python.org/
[gevent]: http://www.gevent.org/
[license]: http://www.apache.org/licenses/LICENSE-2.0
[distribute]: http://pypi.python.org/pypi/distribute
[etsy repo]: https://github.com/etsy/statsd
[etsy post]: http://codeascraft.etsy.com/2011/02/15/measure-anything-measure-everything/

