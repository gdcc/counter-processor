#!/usr/bin/env python3
import config
from models import *
import input_processor as ip
import output_processor as op
from upload import upload
import os
import glob
import sys
import datetime

# import ipdb; ipdb.set_trace()
def main():
    if not os.path.isfile(config.Config().processing_database):
        DbActions.create_db()
    else:
        DbActions.vacuum() # cleans up DB indices for speed

    # if re-running a particular month then remove the db and entry in the state file
    if config.Config().clean_for_rerun == True:
        config.Config().delete_log_processed_date()
        DbActions.create_db()

    the_filenames = config.Config().filenames_to_process()

    print(f'Running report for {config.Config().start_time().isoformat()} to {config.Config().end_time().isoformat()}')

    # process the log lines into a sqlite database
    print(f'{len(the_filenames)} log file(s) will be added to the database')
    print(f'Last processed date: {config.Config().last_processed_on()}')
    starttime = datetime.datetime.now()
    for lf in the_filenames:
        day = config.Config().get_day_from_filename(lf)
        with open(lf, 'r') as infile:
            print(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  importing {lf}')
            lc = 0
            for line in infile:
                ip.LogLine(line).populate()
                lc += 1
                if lc % 100 == 0:
                    print(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  lines imported {lc}')
            print(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  lines imported {lc}')
        delta = datetime.datetime.now() - starttime
        print(f'process time {delta}')
        DbActions.vacuum() # cleanup indices, etc, maybe makes queries faster
        config.Config().copy_db_to_disk()
        config.Config().update_log_processed_date(day)
        # only deleting reports if processing new log files, so we can re-run the upload without re-creating the reports
        config.Config().write_batch_index(-1)

    print('')
    DbActions.vacuum() # cleanup indices, etc, maybe makes queries faster
    # output for each unique identifier (that isn't robots)
    my_report = op.JsonReport()
    my_report.output()

    if config.Config().upload_to_hub == True:
        upload.send_to_datacite()

    # Clean up - delete db only after all the month's reports are generated and uploaded successfully
    print(f'Month Complete {config.Config().month_complete()}')
    if os.path.isfile(config.Config().processing_database) and config.Config().month_complete():
        print(f'Deleting Database {config.Config().processing_database}')
        os.remove(config.Config().processing_database)

    if 'test_mode' not in globals():
        sys.exit(0) # this is causing the tests to fail

if __name__ == '__main__':
    main()
