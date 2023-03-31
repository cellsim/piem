# This tool translates a network trace as produced by the mari_pcap_decode tool in MARI library to a network trace in a format compatible with the TA specification pattern.
import argparse
import json


def parse_section(section):
    par = section.split('-')
    for k in range(6):
        assert(len(par[k]) > 0)
        par[k] = par[k].strip()
    return tuple(par)


def write_dynamic_format(prefix, ta_format, direction, ip):
    # Format as https://sqbu-github.cisco.com/jianfu/piem#emulate-network-dynamics
    sections = ta_format.split('_')
    time0, loss0, latency0, bw0, burst0, qdelay0 = parse_section(sections[0])
    assert(time0 == 'S' or time0 == '0')

    fileOut = prefix + '_dynamic_trace.json'
    with open(fileOut, 'w') as f:
        f.write('{\n')
        f.write('\t"qdelay": ' + qdelay0 + ',\n')
        f.write('\t"loss": ' + loss0 + ',\n')
        f.write('\t"bw": ' + bw0 + ',\n')
        f.write('\t"handle": 2,\n')                 # What is this?
        f.write('\t"delay": ' + latency0 + ',\n')
        f.write('\t"burst": ' + burst0 + ',\n')
        f.write('\t"emfilter": {\n')
        f.write('\t\t"direction": "' + direction + '",\n')
        f.write('\t\t"ip": "' + ip + '",\n')
        f.write('\t\t"srcport": null,\n')
        f.write('\t\t"ptype": null,\n')
        f.write('\t\t"tos": null,\n')
        f.write('\t\t"dstport": null\n')
        f.write('\t},\n')
        f.write('\t"sls": null,\n')

        f.write('\n')
        f.write('\t"dynamics": [\n')

        lastbw = bw0
        lasttime = 0
        for k in range(1, len(sections)):
            time, loss, latency, bw, burst, qdelay = parse_section(sections[k])
            assert(loss == loss0 and latency == latency0 and burst == burst0 and qdelay == qdelay0)
            duration = int(time) - lasttime
            if duration > 0:
                f.write('\t\t{\n')
                f.write('\t\t\t"bw": ' + lastbw + ',\n')
                f.write('\t\t\t"duration": ' + str(duration) + ',\n')
                f.write('\t\t\t"interval": 0\n')
                if k == len(sections) - 1:
                    f.write('\t\t}\n')
                else:
                    f.write('\t\t},\n')
            lasttime = int(time)
            lastbw = bw

        f.write('\t]\n')
        f.write('}\n')

    return fileOut


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("PatternFile", help = "Text file containing the TA netwotk specification to simplify.")

    parser.add_argument("-s", "--StartTimeOffsetSec", help = "[OPTIONAL] Insert seconds at start. Useful for aligning audio playout with interesting network changes.")

    parser.add_argument("-d", "--Direction", help = "[OPTIONAL] Specify 'uplink' or 'downlink' drection. Defaults to 'uplink'.")

    parser.add_argument("-i", "--ip", help = "[OPTIONAL] The source IP to write to JSON output. Defaults to 'x.x.x.x'.")

    args = parser.parse_args()

    prefix = args.PatternFile.removesuffix('.txt')
    prefix = prefix.removesuffix('_simplified_trace')

    with open(args.PatternFile, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 1

    direction = 'uplink'
    if (args.Direction):
        assert(args.Direction == 'uplink' or args.Direction == 'downlink')
        direction = args.Direction

    ip = 'x.x.x.x'
    if (args.ip):
        octets = args.ip.split('.')
        assert(len(octets) == 4)
        ip = args.ip

    fileOut = write_dynamic_format(prefix, lines[0], direction, ip)

    try:
        with open(fileOut, 'r') as f:
            data = json.load(f)
    except:
        print('Error: Output file failed JSON parsing.')


if __name__ == "__main__":
    main()



