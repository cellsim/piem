#!/usr/bin/python
import argparse
import json
import os
import subprocess

# settings
DRY_RUN = 0

INGRESS_INF = "wlan0"
EGRESS_INF = "eth0"
MAX_NUM_IFBS = 64

CONFIG_PATH = '/etc/piem/config.json'
RULE_PATH = '/etc/piem/piem.rules'

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as e:
        import errno
        if e.errno != errno.EEXIST or not os.path.isdir(path):
            print(e)
            raise

def exec_shell(command):
    print(command)
    ret = True
    if not DRY_RUN:
        try:
            output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            output = str(e.output)
            print(output)
            ret = False
    return ret

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return None
    with open(CONFIG_PATH, 'r') as f:
        content = f.read()
        config = json.loads(content)
        print('loads config from %s' % CONFIG_PATH)
        return config

def save_config(args):
    config = {
        'ingress': args.ingress,
        'egress': args.egress,
        'numifbs': args.numifbs
    }
    config_dir = os.path.dirname(CONFIG_PATH)
    mkdir_p(config_dir)
    with open(CONFIG_PATH, 'w') as f:
        content = json.dumps(config, indent=4)
        print('save config from %s\n%s\n' % (CONFIG_PATH, content))
        f.write(content)

def init():
    if gConfig is None:
        print('Configuration not found at %s, please configure first' % CONFIG_PATH)
        return False
    init_cmd = '''
        modprobe ifb numifbs=%(numifbs)d

        # uplink
        tc qdisc add dev %(ingress)s ingress
        tc qdisc add dev %(egress)s root handle 1: htb default 1
        tc class add dev %(egress)s parent 1: classid 1:1 htb rate 1000mbit

        # downlink
        tc qdisc add dev %(egress)s ingress
        tc qdisc add dev %(ingress)s root handle 1: htb default 1
        tc class add dev %(ingress)s parent 1: classid 1:1 htb rate 1000mbit
    ''' % gConfig
    return exec_shell(init_cmd)

def uninit():
    if os.path.exists(RULE_PATH):
        print('Clear all rules in %s' % RULE_PATH)
        os.remove(RULE_PATH)

    if gConfig is None:
        print('Configuration not found at %s, please configure first' % CONFIG_PATH)
        return False
    uninit_cmd = '''
        # downlink
        tc qdisc del dev %(egress)s ingress
        tc qdisc del dev %(ingress)s root

        # uplink
        tc qdisc del dev %(ingress)s ingress
        tc qdisc del dev %(egress)s root

        modprobe -r ifb
    ''' % gConfig
    return exec_shell(uninit_cmd)

def load_rules():
    if not os.path.exists(RULE_PATH):
        print("no rules file found at %s!" % RULE_PATH)
        return []
    with open(RULE_PATH, 'r') as f:
        content = f.read()
        rules = json.loads(content)
        for r in rules:
            global gHandleManager
            gHandleManager.add_handle(r['handle'])
        print('loads rules from %s\n%s\n' % (RULE_PATH, content))
        return rules

def save_rules(rules):
    rule_dir = os.path.dirname(RULE_PATH)
    mkdir_p(rule_dir)
    with open(RULE_PATH, 'w') as f:
        content = json.dumps(rules, indent=4)
        print('save rules to %s\n%s\n' % (RULE_PATH, content))
        f.write(content)

class HandleManager(object):

    '''
    htb handles, 1 is reserved, so at least start with 2
    '''

    def __init__(self, handle_min, handle_max):
        self.handle_set = set()
        assert handle_min < handle_max
        self.valid_handles = range(handle_min, handle_max+1)

    def add_handle(self, handle):
        self.handle_set.add(handle)

    def remove_handle(self, handle):
        self.handle_set.remove(handle)

    def get_available_handle(self):
        for h in self.valid_handles:
            if h not in self.handle_set:
                return h
        return None

HANDLE_MIN = 2
HANDLE_MAX = HANDLE_MIN + MAX_NUM_IFBS - 1
gHandleManager = HandleManager(HANDLE_MIN, HANDLE_MAX)
gConfig = load_config()

get_ifb_idx = lambda handle: handle - HANDLE_MIN

class Rule(object):

    def __init__(self, emfilter, bw, loss, qdelay, delay, direction, burst, handle=None):
        self.emfilter = emfilter
        self.bw = bw
        self.loss = loss
        self.qdelay = qdelay
        self.delay = delay
        self.burst = burst
        self.direction = direction
        self.handle = handle

    def exists(self, rules):
        for idx, r in enumerate(rules):
            if r['emfilter'] == self.emfilter and \
                r['direction'] == self.direction:
                return idx
        return -1

    def set_handle(self, handle):
        self.handle = handle

    def _get_tc_params(self):
        if self.direction == 'uplink':
            in_inf = gConfig['ingress']
            out_inf = gConfig['egress']
            target = 'src'
        else:
            in_inf = gConfig['egress']
            out_inf = gConfig['ingress']
            target = 'dst'

        ifb_idx = get_ifb_idx(self.handle)

        params = {
            'in_inf': in_inf,
            'out_inf': out_inf,
            'target': target,
            'ifb_idx': ifb_idx,
            'ipfilter': self.emfilter,
            'bw': self.bw,
            'delay': self.delay,
            'tb_qsize': self.bw * 1000 * self.qdelay / 8000,
            'handle': self.handle
        }

        if self.burst is not None:
            floss = self.loss / 100.0
            params['gemodel_p'] = 100.0 * floss / self.burst / (1 - floss)
            params['gemodel_r'] = 100.0 / self.burst
        else:
            params['loss'] = self.loss

        return params

    def add(self):
        params = self._get_tc_params()
        add_cmd = '''
        ip link set dev ifb%(ifb_idx)d up
        tc filter add dev %(in_inf)s parent ffff: protocol ip prio 1 u32 match ip %(target)s %(ipfilter)s flowid 1:1 action mirred egress redirect dev ifb%(ifb_idx)d
        ''' % params

        if self.burst is not None:
            add_cmd += 'tc qdisc add dev ifb%(ifb_idx)d root handle 1: netem loss gemodel %(gemodel_p)s%% %(gemodel_r)s%% delay %(delay)dms\n' % params
        else:
            add_cmd += 'tc qdisc add dev ifb%(ifb_idx)d root handle 1: netem loss random %(loss)s%% delay %(delay)dms' % params

        add_cmd += '''
        tc class add dev %(out_inf)s parent 1:1 classid 1:%(handle)d htb rate %(bw)skbit
        tc filter add dev %(out_inf)s protocol ip parent 1:0 prio 1 u32 match ip %(target)s %(ipfilter)s flowid 1:%(handle)d
        tc qdisc add dev %(out_inf)s parent 1:%(handle)d bfifo limit %(tb_qsize)d
        ''' % params

        return exec_shell(add_cmd)

    def remove(self):
        params = self._get_tc_params()
        remove_cmd = '''
        tc filter del dev %(out_inf)s protocol ip parent 1:0 prio 1 u32 match ip %(target)s %(ipfilter)s flowid 1:%(handle)d
        tc class del dev %(out_inf)s parent 1:1 classid 1:%(handle)d
        tc qdisc del dev ifb%(ifb_idx)d root
        tc filter del dev %(in_inf)s parent ffff: protocol ip prio 1 u32 match ip %(target)s %(ipfilter)s flowid 1:1 action mirred egress redirect dev ifb%(ifb_idx)d
        ip link set dev ifb%(ifb_idx)d down
        ''' % params

        return exec_shell(remove_cmd)


def add_rule(r):
    rules = load_rules()
    idx = r.exists(rules)
    if idx != -1:
        Rule(**rules[idx]).remove()
        gHandleManager.remove_handle(rules[idx]['handle'])
        del rules[idx]
    h = gHandleManager.get_available_handle()
    if h is None:
        print('add rule, no handle available')
        return
    r.set_handle(h)
    rules.append({
        'emfilter': r.emfilter,
        'direction': r.direction,
        'bw': r.bw,
        'loss': r.loss,
        'qdelay': r.qdelay,
        'delay': r.delay,
        'burst': r.burst,
        'handle': r.handle
    })
    save_rules(rules)
    r.add()

def remove_rule(r):
    print('removing rule for %s %s...' % (r.emfilter, r.direction))
    rules = load_rules()
    idx = r.exists(rules)
    if idx != -1:
        Rule(**rules[idx]).remove()
        gHandleManager.remove_handle(rules[idx]['handle'])
        del rules[idx]
        save_rules(rules)
    else:
        print('rule not found!\n')

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--dryrun', action='store_true', help='Dry run', default=False)

    subparsers = arg_parser.add_subparsers(dest='subcommand')

    # config command
    config_parser = subparsers.add_parser('config')

    config_parser.add_argument('--ingress', '-i',
        action='store',
        help='ingress network interface',
        default='wlan'
    )

    config_parser.add_argument('--egress', '-e',
        action='store',
        help='egress network interface',
        default='eth0'
    )

    config_parser.add_argument('--numifbs', '-n',
        action='store',
        help='number of ifb devices',
        default=64
    )

    # list command
    list_parser = subparsers.add_parser('list')

    # init command
    init_parser = subparsers.add_parser('init')

    # uninit command
    uninit_parser = subparsers.add_parser('uninit')

    # add command
    add_parser = subparsers.add_parser('add')
    add_parser.add_argument('--bw', '-b', type=int, help="rate limit in kbps", default=8000)
    add_parser.add_argument('--loss', '-l', type=int, help="loss ratio in percentage, 5 is 5%%", default=0)
    add_parser.add_argument('--burst', type=int, help="burst length in packets", default=None)
    add_parser.add_argument('--delay', '-d', type=int, help="delay in ms", default=10)
    add_parser.add_argument('--qdelay', '-q', type=int, help="maxinum queuing delay in ms", default=100)
    add_parser.add_argument('--filter', '-f', help="src(uplink) or dst(downlink) ip filter", required=True)
    add_parser.add_argument('--direction', '-c', choices=['uplink', 'downlink'], required=True)

    # remove command
    remove_parser = subparsers.add_parser('remove')
    remove_parser.add_argument('--filter', '-f', help="src(uplink) or dst(downlink) ip filter", required=True)
    remove_parser.add_argument('--direction', '-c', choices=['uplink', 'downlink'])

    args = arg_parser.parse_args()
    global DRY_RUN
    DRY_RUN = args.dryrun

    if args.subcommand == 'config':
        save_config(args)
    elif args.subcommand == 'list':
        print(json.dumps(gConfig, indent=4))
        load_rules()
    elif args.subcommand == 'init':
        init()
    elif args.subcommand == 'uninit':
        uninit()
    elif args.subcommand == 'add':
        add_rule(
            Rule(args.filter, args.bw, args.loss, args.qdelay, args.delay, args.direction, args.burst)
        )
    elif args.subcommand == 'remove':
        if args.direction is not None:
            remove_rule(
                Rule(args.filter, 0, 0, 0, 0, args.direction, 0)
            )
        else:
            remove_rule(
                Rule(args.filter, 0, 0, 0, 0, 'uplink', 0)
            )
            remove_rule(
                Rule(args.filter, 0, 0, 0, 0, 'downlink', 0)
            )
    else:
        arg_parser.error('subcommand not found!')

if __name__ == "__main__":
    main()
