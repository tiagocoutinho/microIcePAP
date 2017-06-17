import logging
import argparse

import gevent
import microIcePAP


def parse_args():
    parser = argparse.ArgumentParser(description='micro IcePAP simple example 1')
    parser.add_argument('icepap', nargs=1, type=str)
    parser.add_argument('--log-level', default='WARNING', help='log level',
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'])

    args = parser.parse_args()

    fmt = '%(asctime)-15s %(levelname)-5s %(name)s: %(message)s'
    level = getattr(logging, args.log_level.upper())
    logging.basicConfig(format=fmt, level=level)

    icepap = microIcePAP.IcePAP(args.icepap[0])
    return icepap


def main():
    icepap = parse_args()
    th = microIcePAP.get_axis(icepap, 1, dict(acctime=.25, velocity=10000))
    print '1 status:', icepap.status[1]
    print '3 status:', icepap.status[3]
    print '1,2 status:', icepap.status[1:3]
    print '1,2 pos:', icepap.pos[1:3]


if __name__ == '__main__':
    icepap = main()

