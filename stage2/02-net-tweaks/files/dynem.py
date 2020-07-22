#!/usr/bin/python
import argparse
import json
import signal
import sys
import time
import emulator as em

'''
emulate timeseries network dynamics loading from file with format below:

{
    "qdelay": 600, 
    "loss": 2, 
    "bw": 2000, 
    "handle": 2, 
    "delay": 200, 
    "burst": 4, 
    "emfilter": {
        "direction": "uplink", 
        "ip": "10.34.12.3", 
        "srcport": null, 
        "ptype": null, 
        "tos": null, 
        "dstport": null
    }, 
    "sls": null,

    "dynamics": [
        {
            "bw": 500,
            "duration": 2,
            "interval": 10
        },
        {
            "bw": 300,
            "duration": 1,
            "interval": 20,
        },
        {
            "bw": 1000,
            "duration": 3,
            "interval": 0
        }
    ]
}

The bandwidth is 2 mbps normally, and will

1. 10 seconds later, drop to 500 kbps, and last for 2 seconds, then the bandwidth goes back to 2 mbps;
2. 20 seconds later, the bandwidth drops to 300 and last for 1 second, then the bandwidth goes back to 2 mbps;
3. 0 seconds later, the bandwidth goes back to 1 mbps, and last for 3 seconds, then the bandwidth goes back to 2 mbps;
4. loop back above phases.

For those network parameters not specified in the 'dynamics' section, it will remain the same as before.
'''

def parse_config(cfg):
    try:
        with open(cfg, 'r') as f:
            content = f.read()
            try:
                config = json.loads(content)
            except ValueError as error:
                print("invalid json: %s" % error)
            return config
    except IOError:
        print('error reading file') 

def validate_config(cfg):
    if 'emfilter' not in cfg:
        print('error, no filter specified!')
        return False

    if 'ip' not in cfg['emfilter']:
        print('error, no ip specified!')
        return False

    if 'direction' not in cfg['emfilter']:
        print('error, no direction specified!')
        return False

    if 'dynamics' not in cfg:
        print('error, no dynamics specified!')
        return False

    for item in cfg['dynamics']:
        if 'duration' not in item:
            print('error, no duration specified')
            return False
        if 'interval' not in item:
            print('error, no interval specified')
            return False

    return True

def run(config):
    dire = config['emfilter']['direction']
    ip = config['emfilter']['ip']
    tos = config['emfilter'].get('tos', None)
    protocol = config['emfilter'].get('protocol', 'all')
    srcport = config['emfilter'].get('srcport', None)
    dstport = config['emfilter'].get('dstport', None)
    ptype = config['emfilter'].get('ptype', None)
    bw = config.get('bw', 8000)
    loss = config.get('loss', 0)
    qdelay = config.get('qdelay', 100)
    jitter = config.get('jitter', 0)
    delay = config.get('delay', 10)
    burst = config.get('burst', None)
    sls = config.get('sls', None)

    f = em.Filter(dire, ip, tos, srcport, dstport, ptype, protocol)
    r = em.Rule(f, bw, loss, qdelay, jitter, delay, dire, burst, sls)
    em.add_rule(r)

    rlist = []
    for dyn in config['dynamics']:
        dyn_bw = dyn.get('bw', bw)
        dyn_loss = dyn.get('loss', loss)
        dyn_qdelay = dyn.get('qdelay', qdelay)
        dyn_jitter = dyn.get('jitter', jitter)
        dyn_delay = dyn.get('delay', delay)
        dyn_burst = dyn.get('burst', burst)
        dyn_sls = dyn.get('sls', sls)
        dyn_r = em.Rule(f, dyn_bw, dyn_loss, dyn_qdelay, dyn_jitter, dyn_delay, dire, dyn_burst, dyn_sls)
        rlist.append({'rule': dyn_r, 'interval': dyn['interval'], 'duration': dyn['duration']})
 
    idx = 0
    signal.signal(signal.SIGINT, signal.default_int_handler)
    while True:
        try:
            next_rule = rlist[idx]['rule']
            wait_sec = rlist[idx]['interval']
            last_sec = rlist[idx]['duration']

            print('sleep for %s seconds ...' % wait_sec)
            time.sleep(wait_sec)
            em.change_rule(next_rule)

            print('unstable for %s seconds ...' % last_sec)
            time.sleep(last_sec)

            idx += 1
            if idx >= len(rlist):
                idx = 0

            if rlist[idx]['interval'] != 0:
                print('rollback')
                em.change_rule(r)
        except KeyboardInterrupt:
            print('\n\nclear rules')
            em.remove_rule(r)
            sys.exit()

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--dryrun', action='store_true', help='Dry run', default=False)
    arg_parser.add_argument('--cfg', '-f', help='configuration file', required=True)

    args = arg_parser.parse_args()
    em.DRY_RUN = args.dryrun
    if em.DRY_RUN:
        em.CONFIG_PATH = './config.json'
        em.RULE_PATH = './piem.rules'

    em.gConfig = em.load_config(em.CONFIG_PATH)

    config = parse_config(args.cfg)
    if validate_config(config):
        run(config)
    else:
        print('invalid configure')


if __name__ == "__main__":
    main()
