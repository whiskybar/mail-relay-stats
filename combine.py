import sys
import csv
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
for site_uuid, details in statuses.iteritems():
    details['received'] = sum(int(details['status'].get(status, '0')) for status in status_list)
    details['site_uuid'] = site_uuid
    lines.append(details)
lines.sort(key=lambda line: -line['received'])

output = csv.writer(sys.stdout)
output.writerow(['service_level', 'site_uuid', 'site_name'] + status_list + ['received_total'])
for line in lines:
    output.writerow([line['service_level'], line['site_uuid'], line['name']] + [line['status'].get(status, '') for status in status_list] + [line['received']])
    
