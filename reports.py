import sys
import glob
import gzip
import pwd
import json

def find_previous_log_file():
    return max(glob.glob('/var/log/maillog-*.gz'))

def log_stream(regular_file, gzip_file):
    for line in open(regular_file):
        yield line
    for line in gzip.open(gzip_file):
        yield line

def extract_queued_as(line):
    return line.split('queued as ')[1][:-2]

def lines_with_ids(ids, log_file, line_parser):
    bids = frozenset(ids)
    for line in log_file:
        try:
            connection_id = line_parser(line)
            if connection_id in bids:
                yield line
        except IndexError:
            continue

def find_ids(lines):
    for line in lines:
        yield line.split(':', 5)[3].strip()

def extract_uid(line):
    if 'uid=' not in line:
        raise IndexError(0)
    return line.split(':', 5)[3].strip()

def find_uids(lines):
    for line in lines:
        yield line.split('uid=')[1].split()[0]

def lookup_binding_ids(uids):
    for uid in uids:
        try:
            yield pwd.getpwuid(int(uid)).pw_name
        except KeyError:
            continue

def lookup_site_infos(binding_ids):
    cache = {}
    for binding_id in binding_ids:
        try:
            yield cache[binding_id]
        except KeyError:
            pass
        else:
            continue
        try:
            j = json.load(open('/srv/bindings/%s/metadata.json' % binding_id))
        except IOError:
            continue
        cache[binding_id] = output = j.get('service_level', 'unknown'), j['site'], j.get('label', 'empty').encode('utf-8')
        yield output

def report_site_infos(site_infos):
    for info in site_infos:
        print ' '.join(info)

def main():
    id_list_file = sys.argv[1]
    main_log_file = '/var/log/maillog'
    previous_log_file = find_previous_log_file()

    original_line_ids = lines_with_ids(open(id_list_file).read().split('\n'), log_stream(main_log_file, previous_log_file), extract_queued_as)
    original_ids = find_ids(original_line_ids)

    uid_lines = lines_with_ids(original_ids, log_stream(main_log_file, previous_log_file), extract_uid)
    uids = find_uids(uid_lines)

    binding_ids = lookup_binding_ids(uids)
    site_infos = lookup_site_infos(binding_ids)

    report_site_infos(site_infos)

if __name__ == '__main__':
    main()
