Example Job:
"""
{
    'id': 3,
    'action': 'SYNC',
    'state': 'PEND',
    'package': {
        'relative_path': 'Package 1/',
        'id': 1,
        'is_base_package': False,
        'name': 'Package #1',
        'category': 1,
        'parent_package': None,
        'date_created': '2014-10-30T22:01:00.558Z',
        'metadata': ''
        'files': {
            '834': {'name': 'file_834.zip', 'hash': '23498236472846398273'},
            '12': {'name': 'foo/file_12.avro', 'hash': '12983719847089173498'},
            '977': {'name': 'bar/file_977.bz2', 'hash': '21308723098409283408'},
            '9': {'name': 'file_9.gz', 'hash': '23984029374908273498'}
        }
    },
    'source_client': {
        'base_path': '/foo/',
        'host_port': 22,
        'host_hostname': '',
        'id': 1,
        'name': 'Client #1',
        'max_download': 0,
        'max_upload': 0,
        'host_username': ''
    },
    'destination_client': {
        'base_path': '/foo/bar/',
        'host_port': 22,
        'host_hostname': 'foo.bar.domain',
        'id': 2,
        'name': 'Client #2',
        'max_download': 0,
        'max_upload': 0,
        'host_username': 'foobar'
    }
}
"""

The Jobqueue Manager will:
* Be running on each server (Client), be it a storage server (Source/Destination) or a remote server (Destination)
* Be responsible for Jobs where it is the 'Source'
* Be able to remotely authenticate into any configured destination server  
* Talk REST to an API that will provide Jobs for a given Authentication Token (API Key)
    * Accept jobs from the API
    * Process jobs from the API
    * Provide updates (started/progress/completed/failed) to the API for a given job
* Able to recover gracefully given an unexpected shutdown/startup
* Trust the API as the source of truth for Jobs and only keep a temporary cache of which Jobs are currently being worked on


Workflow of an end user requesting a Package send to their Client:
* The end user will submit a job (to the Frontend exposing an API) to send a package to their Client from the storage Client
  * Source: Client A
  * Destination: Client B
  * Package: Package A
* The Source Client (Client A) will periodically query the API for a Job listing
  * Client A queries API for Job list where Client A is the Source
  * Client A loops through each Job attempting to kick it off and ignoring the ones it cannot or is already processing
  * Provide updates to the API of each Job's progress from Client A's PoV
* For each Job that is kicked off from a Client
  * Inform the API that the Job has been started
  * Inform the API of progress for the Job
  * Inform the API of success/failure of the Job


API Interactions:
* Client requesting Job listing (/jobs)
  1. The API layer associates the Authentication Token from the requesting client to an internal Client
  2. Filter down the list of Jobs to just ones that contain the Client as the Source
  3. Blank out the host name/port/user of the client's side (source and/or destination)
  4. Return the filtered and blanked list to the client
* Client providing a status update (/jobs/<job_id>/update)
  1. Client will post to the API endpoint with an appropriate status update and a percentage completed

