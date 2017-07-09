#!/bin/bash

echo "Gathering statistics from mail-relays"
truncate -s 0 /tmp/bounced-connections
now=$(date +%s)
pantheon endpoints | grep mail-relay | cut -f2 -d' ' | while read server; do
  echo "  from $server" >/dev/tty
  scp -q -o 'StrictHostKeyChecking no' match.py $server:/tmp
  ssh -n -o 'StrictHostKeyChecking no' $server sudo python /tmp/match.py $now status=bounced
done >/tmp/bounced-connections

rm -rf hosts
mkdir hosts
cd hosts
cat /tmp/bounced-connections | awk '{ print $2 >> $1 }'

echo "Looking up mail at appservers"
truncate -s 0 /tmp/bounced-reports
for ip in *; do
  echo " at $ip" >/dev/tty
  scp -q -o 'StrictHostKeyChecking no' $ip $ip:/tmp/bounced-ids
  scp -q -o 'StrictHostKeyChecking no' ../reports.py $ip:/tmp/reports.py
  ssh -n -o 'StrictHostKeyChecking no' $ip sudo python /tmp/reports.py /tmp/bounced-ids >>/tmp/bounced-reports
done

cd -

sort /tmp/bounced-reports | uniq -c | sort -n | while read count level uuid label; do
    echo '"'$count'","'$level'","'$uuid'","'$label'"'
done | tee report.csv
