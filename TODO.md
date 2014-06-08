Retrofit this into just a backend daemon that takes all configuration/commands from a REST API endpoint

Add in an API Manager
* Ability to be configured with an end point
* Consumed by JobQueueManager

Change JobQueueManager
* Obtain Jobs from API
* Work on job (perform its action)
*

Change SyncManager
* Given API instance
* Do the actual work on a job
* Post updates about individual jobs to the API
