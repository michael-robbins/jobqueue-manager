Short Term:
* Redo the Tests to be more 'assert' and less 'just run the functions'
* Getting Ubuntu start-stop daemon working with files
* Add in the ability to stop the live daemon through either the start-stop daemon or a DB queue kill message
* Make SyncManager respect the source & destination clients respective upload & download speeds
* Add test for FilePackage discovery

Long Term:
* Turn the test.py into unit tests
  - Tear up/downs for PSQL/SQLite3
* Look into how it will interact with the frontend
  - What extra DB schema fields/tables will be required?
* Think about adding in multiprocessing to the job processing
  - So we can be running delete/index jobs at the same time as a really long sync job
