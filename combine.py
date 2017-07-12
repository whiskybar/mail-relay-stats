import sys
import csv
import subprocess
from collections import defaultdict

statuses = defaultdict(dict)
for line in open(sys.argv[1]):
    line = line.split()
    service_level, site_uuid, status = line[0], line[1], line[-1]
    name = ' '.join(line[2:-1])
    statuses[site_uuid]['service_level'] = '' if service_level == 'unknown' else service_level
    statuses[site_uuid]['name'] = '' if name == 'none' else name
    s = statuses[site_uuid].get('status', defaultdict(int))
    s[status] += 1
    statuses[site_uuid]['status'] = s

status_list = ['bounced', 'bounced_immediately', 'sent', 'sent_immediately', 'expired,', 'deferred']
lines = []
status_count = defaultdict(int)
for site_uuid, details in statuses.iteritems():
    details['received'] = sum(int(details['status'].get(status, '0')) for status in status_list)
    details['site_uuid'] = site_uuid
    lines.append(details)
    for status, count in details['status'].iteritems():
        status_count[status] += count
lines.sort(key=lambda line: -line['received'])

output = csv.writer(sys.stdout)
output.writerow(['service_level', 'site_uuid', 'site_name'] + status_list + ['received_total', 'guilty_of_abuse'])
for line in lines:
    if line['received'] > 1000:
        guilty = subprocess.check_output('ygg /sites/%s | jq .guilty_of_abuse' % line['site_uuid'], shell=True).strip()
    else:
        guilty = ''
    output.writerow([line['service_level'], line['site_uuid'], line['name']] + [line['status'].get(status, '') for status in status_list] + [line['received'], guilty])

f = open('summary', 'w')    
f.write('||Count||Status||\n')
for status in sorted(status_count, key=lambda s: status_count[s]):
    f.write('|%d|%s|\n' % (status_count[status], status))
f.write('||%d||TOTAL||\n' % sum(status_count.itervalues()))
f.close()
