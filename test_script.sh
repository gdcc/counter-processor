#!/bin/bash

# This script was to test running against some sample files to get times and optimize.
# May be a good example for the future.

#rm state/counter_db_2025-01.sqlite3 || true
#rm state/statefile.json || true
STARTTIME=$(date +%s)
echo "Starting"
rm -rf log
mkdir log
for i in $(seq 1 30); do
  cp test/fixtures/counter_2025-01-00.log log/counter_2025-01-$(printf "%02d" "$i").log
done
#cp test/fixtures/counter_2025-01-31.small.log log/counter_2025-01-31.log
#cp test/fixtures/statefile.json state/statefile.json
#cp test/fixtures/statefile1.json state/statefile.json
YEAR_MONTH="2025-01" LOG_NAME_PATTERN="log/counter_(yyyy-mm-dd).log" UPLOAD_TO_HUB=True SIMULATE_DATE="2025-02-01" OUTPUT_FILE='tmp/make-data-count-report' python3.11 main.py
echo "Done"
ENDTIME=$(date +%s)
echo "It took $(($ENDTIME - $STARTTIME)) seconds to complete..."
date
