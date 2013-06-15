-- Schema required for the Job Queue Manager

---
--- Remove previous schema and data
---

-- Drop tables
DROP TABLE job_queue;
DROP TABLE media_package_files;
DROP TABLE media_package_availability;
DROP TABLE clients;
DROP TABLE media_files;
DROP TABLE media_tv_links;
DROP TABLE media_packages;
DROP TABLE media_package_types;
DROP TABLE client_types CASCADE;
DROP TABLE actions;

--
-- Create skeleton schema
--

-- Create tables for data
CREATE TABLE actions (
    -- The verb, we 'push' from a server to a client, we 'delete' a package off a client, we 'pull' a package from a client to the server
    action_id SERIAL PRIMARY KEY
    , name VARCHAR(64) NOT NULL
    , system_name VARCHAR(64) NOT NULL
);

CREATE TABLE client_types (
    -- Either a Server or a Client really...
    client_type_id SERIAL PRIMARY KEY
    , name VARCHAR(64) NOT NULL
);

CREATE TABLE media_package_types (
    -- Media Packages are either Movies, TV Base Folder or TV Season (potentially more)
    package_type_id SERIAL PRIMARY KEY
    , name VARCHAR(256) NOT NULL
);

CREATE TABLE clients (
    -- Can be servers, clients, etc. They are the end points.
    client_id SERIAL PRIMARY KEY
    , client_type_id INTEGER NOT NULL REFERENCES client_types(client_type_id) ON DELETE RESTRICT
    , name VARCHAR(64) NOT NULL
    , sync_hostname VARCHAR(64) NOT NULL
    , sync_port INTEGER NOT NULL
    , base_path VARCHAR(256) NOT NULL DEFAULT '/'
);

CREATE TABLE media_packages (
    -- Media package is of a certain type and contains files, descriptions and metadata in XML format
    package_id SERIAL PRIMARY KEY NOT NULL
    , package_type_id INTEGER NOT NULL REFERENCES media_package_types(package_type_id) ON DELETE RESTRICT
    , name VARCHAR(256) NOT NULL
    , folder_name VARCHAR(256)
    , metadata_xml VARCHAR(1024)
    , date_created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    , date_last_index TIMESTAMP WITH TIME ZONE
    , is_archived BOOLEAN DEFAULT false
);

CREATE TABLE media_files (
    -- Each file belongs to a package
    file_id SERIAL PRIMARY KEY
    , relative_path VARCHAR(256) NOT NULL -- This is relative to the clients base_path
    , date_last_index TIMESTAMP WITH TIME ZONE DEFAULT NOW() -- Time the file was last indexed
);

CREATE TABLE media_tv_links (
    -- Links a TV Base folder with its Season folders
    base_id INTEGER NOT NULL REFERENCES media_packages(package_id) ON DELETE RESTRICT
    , season_id INTEGER NOT NULL REFERENCES media_packages(package_id) ON DELETE CASCADE
);

CREATE TABLE media_package_files (
    -- Each package contains the following files
    -- TODO: Trigger that when a package_id is deleted, we also delete the row in media_files(file_id)
    package_id INTEGER NOT NULL REFERENCES media_packages(package_id) ON DELETE CASCADE
    , file_id INTEGER NOT NULL REFERENCES media_files(file_id) ON DELETE CASCADE
);

CREATE TABLE media_package_availability (
    -- Each client has the following packages
    client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE RESTRICT
    , package_id INTEGER NOT NULL REFERENCES media_packages(package_id) ON DELETE CASCADE
    , date_last_index TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    , is_missing_files BOOLEAN DEFAULT false
);

CREATE TABLE job_queue (
    -- Contains jobs! Suprise Suprise!
    job_id SERIAL PRIMARY KEY
    , package_id INTEGER NOT NULL REFERENCES media_packages(package_id) ON DELETE RESTRICT
    , src_client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE RESTRICT
    , dst_client_id INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE RESTRICT
    , action_id INTEGER NOT NULL REFERENCES actions(action_id) ON DELETE RESTRICT
    , date_queued TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    , date_started TIMESTAMP WITH TIME ZONE
    , date_completed TIMESTAMP WITH TIME ZONE
);

--
-- Initial inserts to get a prototype working
--

-- Type tables, required for data tables
INSERT INTO actions VALUES (DEFAULT, 'Sync', 'SYNC');       -- 1
INSERT INTO actions VALUES (DEFAULT, 'Delete', 'DELETE');   -- 2
INSERT INTO actions VALUES (DEFAULT, 'Reindex', 'REINDEX'); -- 3

INSERT INTO client_types VALUES (DEFAULT, 'Server');    -- 1
INSERT INTO client_types VALUES (DEFAULT, 'Client');    -- 2

INSERT INTO media_package_types VALUES (DEFAULT, 'Movie');      -- 1
INSERT INTO media_package_types VALUES (DEFAULT, 'TV Base');    -- 2
INSERT INTO media_package_types VALUES (DEFAULT, 'TV Season');  -- 3

-- Data tables, required for link tables
INSERT INTO clients VALUES (DEFAULT, 1, 'Media Server', 'filer-server.dalmura.private.lan', 22, '/data/media'); -- 1
INSERT INTO clients VALUES (DEFAULT, 2, 'Prometheus'  , 'prometheus.dalmura.private.lan'  , 22, '/data/media'); -- 2

INSERT INTO media_packages VALUES (DEFAULT, 1, 'Avatar', 'Avatar (2009)', '', NOW(), NULL, false);                   -- 1
INSERT INTO media_packages VALUES (DEFAULT, 1, 'Prometheus', 'Prometheus (2012)', '', NOW(), NULL, false);           -- 2
INSERT INTO media_packages VALUES (DEFAULT, 2, 'Game of Thrones', 'Game of Thones', '', NOW(), NULL, false);         -- 3
INSERT INTO media_packages VALUES (DEFAULT, 3, 'Game of Thrones - Season 1', 'Season 1', '', NOW(), NULL, false);    -- 4
INSERT INTO media_packages VALUES (DEFAULT, 3, 'Game of Thrones - Season 2', 'Season 2', '', NOW(), NULL, false);    -- 5

INSERT INTO media_files VALUES (DEFAULT, 'Avatar (2009).mkv', NOW());                       -- 1
INSERT INTO media_files VALUES (DEFAULT, 'Avatar (2009).xml', NOW());                       -- 2
INSERT INTO media_files VALUES (DEFAULT, 'Prometheus (2012) 1080p.mkv', NOW());             -- 3
INSERT INTO media_files VALUES (DEFAULT, 'Game of Thrones Base.xml', NOW());                -- 4
INSERT INTO media_files VALUES (DEFAULT, 'Game of Thrones S01E01 - The Wall.mkv', NOW());   -- 5
INSERT INTO media_files VALUES (DEFAULT, 'Game of Thrones S02E02 - The Climb.mkv', NOW());  -- 6
INSERT INTO media_files VALUES (DEFAULT, 'Game of Thrones S02E02 - The Climb.xml', NOW());  -- 7

-- Link tables
INSERT INTO media_package_files VALUES (1, 1);
INSERT INTO media_package_files VALUES (1, 2);
INSERT INTO media_package_files VALUES (2, 3);
INSERT INTO media_package_files VALUES (3, 4);
INSERT INTO media_package_files VALUES (4, 5);
INSERT INTO media_package_files VALUES (5, 6);
INSERT INTO media_package_files VALUES (5, 7);

INSERT INTO media_package_availability VALUES (1, 1);
INSERT INTO media_package_availability VALUES (1, 2);
INSERT INTO media_package_availability VALUES (1, 3);
INSERT INTO media_package_availability VALUES (1, 4);
INSERT INTO media_package_availability VALUES (1, 5);
INSERT INTO media_package_availability VALUES (2, 1);
INSERT INTO media_package_availability VALUES (2, 3);
INSERT INTO media_package_availability VALUES (2, 5);

INSERT INTO media_tv_links VALUES (3, 4);
INSERT INTO media_tv_links VALUES (3, 5);

-- Create a test job, pushing Prometheus to the Client from the Server
-- INSERT INTO job_queue VALUES (DEFAULT, 2, 1, 2, 1, NOW(), NULL, NULL); -- package(2) from client(1) to client(2) with action(1)

