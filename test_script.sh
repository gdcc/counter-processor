#!/bin/bash

# This script was to test running against some sample files to get times and optimize.
# May be a good example for the future.

#rm state/counter_db_2025-01.sqlite3 || true
rm state/statefile.json || true
STARTTIME=$(date +%s)
echo "Starting"
rm -rf log
mkdir log
for i in $(seq 1 30); do
  cp test/fixtures/counter_2025-01-00.log log/counter_2025-01-$(printf "%02d" "$i").log
done
cp test/fixtures/counter_2025-01-31.log log/counter_2025-01-31.log

# Processing daily
for i in $(seq 1 8); do
  s=$((i + 1))
  YEAR_MONTH="2025-01" LOG_NAME_PATTERN="log/counter_2025-01-0$i.log" UPLOAD_TO_HUB=False SIMULATE_DATE="2025-01-0$s" OUTPUT_FILE='tmp/make-data-count-report' python3.11 main.py
done
YEAR_MONTH="2025-01" LOG_NAME_PATTERN="log/counter_2025-01-09.log" UPLOAD_TO_HUB=False SIMULATE_DATE="2025-01-10" OUTPUT_FILE='tmp/make-data-count-report' python3.11 main.py
for i in $(seq 11 30); do
  s=$((i + 1))
  YEAR_MONTH="2025-01" LOG_NAME_PATTERN="log/counter_2025-01-$i.log" UPLOAD_TO_HUB=False SIMULATE_DATE="2025-01-$s" OUTPUT_FILE='tmp/make-data-count-report' python3.11 main.py
done
YEAR_MONTH="2025-01" LOG_NAME_PATTERN="log/counter_2025-01-31.log" UPLOAD_TO_HUB=False SIMULATE_DATE="2025-02-01" OUTPUT_FILE='tmp/make-data-count-report' python3.11 main.py

# Process monthly
#YEAR_MONTH="2025-01" LOG_NAME_PATTERN="log/counter_(yyyy-mm-dd).log" UPLOAD_TO_HUB=False SIMULATE_DATE="2025-02-01" OUTPUT_FILE='tmp/make-data-count-report' python3.11 main.py

echo "Done"
ENDTIME=$(date +%s)
echo "It took $(($ENDTIME - $STARTTIME)) seconds to complete..."
date
