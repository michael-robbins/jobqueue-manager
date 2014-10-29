================
Job Queue Manager
================

Takes care of the Frontend requests.

Connects to the Frontend REST API and retrieves the list of jobs available.

Client is pre-configured with an API key that it uses to identify itself to the Frontend with.

For each type of action the client will perform, the client is allowed to perform one action type at once.
Eg. One sync, one index and one delete all at once.


Client will perform as follows:
1. Retrieve job task list for client (HTTPS API call)
2. For each job in the task list
    2.1. Check there's an available job slot (only want the client doing a few things at once)
    2.2. Check if the job's already being worked on
    2.3. Start processing the job
        2.3.1. Report that we started the jobs (HTTPS API call)
        2.3.2. Process the job
            2.3.2.1. Update the job progress (HTTPS API call)
        2.3.3. Report that we (finished/failed) the job (HTTPS API call)
    2.4. Sleep for the allotted time between job queue checks


Job tasks are:
* Sync Job (syncing a package between clients)
    1. Get the package details (HTTPS API call)
    2. For each file
        2.1. Verify if it exists (Local file operations)
        2.2. If not, sync it across (Rsync call server -> client)
        2.3. Verify if it exists (Local file operations)
    3. Report back success
* Index Job (refresh the packages that are on the client with the frontend)
    1. Get the package details (HTTPS API call)
    2. For each file
        2.1. Verify it exists (Local file operations)
    3. Report back its existence
* Delete Job (remove a package off the client)
    1. Get the package details (HTTPS API call)
    2. For each file
        2.1. Delete the file (Local file operations)
        2.2. Verify the file (Local file operations)
    3. Report back success


API endpoints are:
* /clients
* /jobs
* /packages
* /categories