import sys
import glob
import gzip
import datetime

def find_previous_log_file():
    return max(glob.glob('/var/log/maillog-*.gz'))

def log_stream(regular_file, gzip_file):
    """ Sorted by datetime."""

    for line in gzip.open(gzip_file):
        yield line
    for line in open(regular_file):
        yield line

def filtered_connections(log_file, newer_than, search_term):
    clients = {}
    this_year = datetime.date.today().year
    for line in log_file:
        try:
            mail_id = line.split(':', 5)[3].strip()
        except IndexError:
            continue
        try:
            clients[mail_id] = line.split('client=', 1)[1].split('[', 1)[1].split(']', 1)[0]
        except IndexError:
            pass
        if search_term in line and datetime.datetime.strptime(line[:15], '%b %d %H:%M:%S').replace(year=this_year):
            try:
                yield clients[mail_id], mail_id
            except KeyError:
                pass

def report_connections(connections):
    for ip, mail_id in connections:
        print ip, mail_id

def main():
    timestamp = int(sys.argv[1])
    search_term = sys.argv[2]
    main_log_file = '/var/log/maillog'
    previous_log_file = find_previous_log_file()

    connections = filtered_connections(log_stream(main_log_file, previous_log_file), datetime.datetime.fromtimestamp(timestamp) - datetime.timedelta(days=1), search_term)
    report_connections(connections)

if __name__ == '__main__':
    main()
