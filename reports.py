import sys
import glob
import gzip
import pwd
import json


def find_previous_log_file():
    try:
        return max(glob.glob('/var/log/maillog-*.gz'))
    except ValueError:
        return None


def log_stream(regular_file, gzip_file):
    if gzip_file:
        for line in gzip.open(gzip_file):
            yield line
    for line in open(regular_file):
        yield line


def read_statuses(f):
    result = {}
    for line in f:
        terms = line.split()[:3]
        result[terms[0]] = terms[1]
    return result


def find_uids(ids, log_file):
    bids = frozenset(ids)
    uids = {}
    result = {}
    for line in log_file:
        try:
            mail_id = line.split(':', 5)[3].strip()
        except IndexError:
            continue

        try:
            uids[mail_id] = line.split('uid=')[1].split()[0]
        except IndexError:
            pass
        else:
            continue

        try:
            queued_id = line.split('queued as ')[1][:-2]
        except IndexError:
            continue

        if queued_id not in ids:
            continue

        try:
            result[queued_id] = uids[mail_id]
        except KeyError:
            continue

    return result


def lookup_bindings(uids):
    result = {}
    cache = {}
    for mail_id, uid in uids.iteritems():
        try:
            binding_id = cache[uid]
        except KeyError:
            try:
                cache[uid] = binding_id = pwd.getpwuid(int(uid)).pw_name
            except KeyError:
                continue
        result[mail_id] = binding_id
    return result


def lookup_site_infos(binding_ids):
    result = {}
    for binding_id in set(binding_ids):
        try:
            j = json.load(open('/srv/bindings/%s/metadata.json' % binding_id))
        except IOError:
            continue
        result[binding_id] = j.get('service_level', 'unknown'), j['site'], j.get('label', 'empty').encode('utf-8')
    return result


def report_infos(bindings, statuses, site_infos):
    for mail_id, status in statuses.iteritems():
        try:
            binding = bindings[mail_id]
        except KeyError:
            continue
        try:
            print ' '.join(site_infos[binding]), status
        except (UnicodeDecodeError, KeyError):
            continue


def main():
    id_list_file = sys.argv[1]
    main_log_file = '/var/log/maillog'
    previous_log_file = find_previous_log_file()

    statuses = read_statuses(open(id_list_file))
    uids = find_uids(statuses, log_stream(main_log_file, previous_log_file))
    bindings = lookup_bindings(uids)
    site_infos = lookup_site_infos(bindings.itervalues())

    report_infos(bindings, statuses, site_infos)

if __name__ == '__main__':
    main()
