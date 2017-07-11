import sys
import glob
import gzip
import datetime
from collections import defaultdict

def find_previous_log_file():
    return max(glob.glob('/var/log/maillog-*.gz'))

def log_stream(regular_file, gzip_file):
    """ Sorted by datetime."""

    for line in gzip.open(gzip_file):
        yield line
    for line in open(regular_file):
        yield line

def filtered_connections(log_file, newer_than):
    clients = {}
    this_year = datetime.date.today().year
    ignored = set()
    statuses = defaultdict(set)
    for line in log_file:
        try:
            mail_id = line.split(':', 5)[3].strip()
        except IndexError:
            continue

        if mail_id in ignored:
            continue
        try:
            ignored.add(line.split('sender non-delivery notification:', 1)[1].strip())
        except IndexError:
            pass
        else:
            continue

        try:
            clients[mail_id] = line.split('client=', 1)[1].split('[', 1)[1].split(']', 1)[0]
        except IndexError:
            pass
        else:
            continue

        try:
            status = line.split('status=',1)[1].split(' ')[0]
        except IndexError:
            continue

        if datetime.datetime.strptime(line[:15], '%b %d %H:%M:%S').replace(year=this_year) < newer_than:
            if status in ['bounced', 'sent', 'expired,']:
                continue

        statuses[status].add(mail_id)

    for mail_ids in statuses.itervalues():
        mail_ids -= ignored

    statuses['bounced_immediately'] = statuses['bounced'] - statuses['deferred']
    statuses['bounced'] &= statuses['deferred']
    statuses['deferred'] -= statuses['bounced']

    statuses['sent_immediately'] = statuses['sent'] - statuses['deferred']
    statuses['sent'] &= statuses['deferred']
    statuses['deferred'] -= statuses['sent']

    statuses['deferred'] -= statuses['expired,']

    return statuses, clients

def report_connections(statuses, clients):
    for status, ids in statuses.iteritems():
        for id in ids:
            print status, id, clients.get(id, 'none')

def main():
    timestamp = int(sys.argv[1])
    main_log_file = '/var/log/maillog'
    previous_log_file = find_previous_log_file()

    statuses, clients = filtered_connections(log_stream(main_log_file, previous_log_file), datetime.datetime.fromtimestamp(timestamp) - datetime.timedelta(days=1))
    report_connections(statuses, clients)

if __name__ == '__main__':
    main()
