#!/bin/bash

echo "Gathering statistics from mail-relays"
truncate -s 0 /tmp/connections
now=$(date +%s)
pantheon endpoints | grep mail-relay | cut -f2 -d' ' | while read server; do
  echo "  from $server" >/dev/tty
  scp -q -o 'StrictHostKeyChecking no' match.py $server:/tmp
  ssh -n -o 'StrictHostKeyChecking no' $server sudo python /tmp/match.py $now
done >/tmp/connections

rm -rf hosts
mkdir hosts
cd hosts
cat /tmp/connections | awk '{ print $2 " " $1 >> $3 }'

echo "Looking up mail at appservers"
truncate -s 0 /tmp/reports
for ip in *; do
  echo " at $ip" >/dev/tty
  scp -q -o 'StrictHostKeyChecking no' $ip $ip:/tmp/ids
  scp -q -o 'StrictHostKeyChecking no' ../reports.py $ip:/tmp/reports.py
  ssh -n -o 'StrictHostKeyChecking no' $ip sudo python /tmp/reports.py /tmp/ids >>/tmp/reports
done

cd -

python combine.py /tmp/reports >/tmp/status-reports

cat /tmp/reports | rev | cut -f1 -d' ' | rev | sort | uniq -c | sort -n
