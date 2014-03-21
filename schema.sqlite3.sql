-- Schema required for the Job Queue Manager
-- SQLite3 Specific, notable changes
--  - BOOLEAN  = INTEGER (0=false, 1=true)
--  - VARCHAR  = TEXT (no limit can be imposed)
--  - DATETIME = TEXT (no date/time data type 'YYYY-MM-DD HH:MM:SS.SSS' format)
--  - SERIAL   = INTEGER (psql specific thing is just an int)

---
--- Remove previous schema and data
---

-- Drop tables
DROP TABLE job_history;
DROP TABLE job_queue;
DROP TABLE media_package_files;
DROP TABLE media_package_availability;
DROP TABLE clients;
DROP TABLE media_files;
DROP TABLE media_package_links;
DROP TABLE media_packages;
DROP TABLE media_package_types;
DROP TABLE client_types;
DROP TABLE actions;


--
-- Create skeleton schema
--

-- Create tables for data
-- The verb:
--  - We 'push' from a server to a client
--  - We 'delete' a package off a client
--  - We 'pull' a package from a client to the server
CREATE TABLE actions (
    action_id INTEGER PRIMARY KEY AUTOINCREMENT
    , name TEXT NOT NULL
    , system_name TEXT NOT NULL
);

-- Either a Server or a Client really...
CREATE TABLE client_types (
    client_type_id INTEGER PRIMARY KEY AUTOINCREMENT
    , name TEXT NOT NULL
);

-- Media Packages are either Movies, TV Base Folder or TV Season (potentially more)
CREATE TABLE media_package_types (
    package_type_id INTEGER PRIMARY KEY AUTOINCREMENT
    , name TEXT NOT NULL
);

-- Can be servers, clients, etc. They are the end points.
CREATE TABLE clients (
    client_id INTEGER PRIMARY KEY AUTOINCREMENT
    , client_type_id INTEGER NOT NULL
    , name TEXT NOT NULL
    , hostname TEXT NOT NULL
    , port INTEGER NOT NULL
    , username TEXT NOT NULL
    , base_path TEXT NOT NULL DEFAULT '/'
    , max_download INTEGER NOT NULL DEFAULT 0
    , max_upload INTEGER NOT NULL DEFAULT 0
    , FOREIGN KEY(client_type_id) REFERENCES client_types(client_type_id) ON DELETE RESTRICT
);

-- Media package is of a certain type and contains files, descriptions and metadata in XML format
CREATE TABLE media_packages (
    package_id INTEGER PRIMARY KEY AUTOINCREMENT
    , package_type_id INTEGER NOT NULL
    , name TEXT NOT NULL
    , folder_name TEXT
    , metadata_json TEXT
    , date_created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    , date_last_index TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    , is_archived INTEGER DEFAULT 0
    , FOREIGN KEY(package_type_id) REFERENCES media_package_types(package_type_id) ON DELETE RESTRICT
);

-- Each file belongs to a package (hash is sha256)
CREATE TABLE media_files (
    file_id INTEGER PRIMARY KEY AUTOINCREMENT
    , hash TEXT NOT NULL
    , relative_path TEXT NOT NULL
    , date_last_index TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Links a media package to another media package (parent/child)
CREATE TABLE media_package_links (
    parent_id INTEGER NOT NULL
    , child_id INTEGER NOT NULL
    , FOREIGN KEY(parent_id) REFERENCES media_packages(package_id) ON DELETE RESTRICT
    , FOREIGN KEY(child_id) REFERENCES media_packages(package_id) ON DELETE CASCADE
);

-- Each package contains the following files
-- TODO: Trigger that when a package_id is deleted, we also delete the row in media_files(file_id)
CREATE TABLE media_package_files (
    package_id INTEGER NOT NULL
    , file_id INTEGER NOT NULL
    , FOREIGN KEY(package_id) REFERENCES media_packages(package_id) ON DELETE CASCADE
    , FOREIGN KEY(file_id) REFERENCES media_files(file_id) ON DELETE CASCADE
);

-- Each client has the following packages
CREATE TABLE media_package_availability (
    client_id INTEGER NOT NULL
    , package_id INTEGER NOT NULL
    , date_last_index TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    , is_missing_files INTEGER DEFAULT 0
    , FOREIGN KEY(client_id) REFERENCES clients(client_id) ON DELETE RESTRICT
    , FOREIGN KEY(package_id) REFERENCES media_packages(package_id) ON DELETE CASCADE
);

-- Contains jobs! Suprise Suprise!
CREATE TABLE job_queue (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT
    , package_id INTEGER NOT NULL
    , src_client_id INTEGER NOT NULL
    , dst_client_id INTEGER NOT NULL
    , action_id INTEGER NOT NULL
    , date_queued TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    , date_started TEXT DEFAULT NULL
    , date_finished TEXT DEFAULT NULL
    , pid INTEGER DEFAULT NULL
    , FOREIGN KEY(package_id) REFERENCES media_packages(package_id) ON DELETE RESTRICT
    , FOREIGN KEY(src_client_id) REFERENCES clients(client_id) ON DELETE RESTRICT
    , FOREIGN KEY(dst_client_id) REFERENCES clients(client_id) ON DELETE RESTRICT
    , FOREIGN KEY(action_id) REFERENCES actions(action_id) ON DELETE RESTRICT
);

-- Contains old jobs! Suprise Suprise!
CREATE TABLE job_history (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT
    , package_id INTEGER NOT NULL
    , src_client_id INTEGER NOT NULL
    , dst_client_id INTEGER NOT NULL
    , action_id INTEGER NOT NULL
    , date_queued TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    , date_started TEXT NOT NULL
    , date_finished TEXT NOT NULL
    , pid INTEGER NOT NULL
    , outcome TEXT NOT NULL
    , FOREIGN KEY(package_id) REFERENCES media_packages(package_id) ON DELETE RESTRICT
    , FOREIGN KEY(src_client_id) REFERENCES clients(client_id) ON DELETE RESTRICT
    , FOREIGN KEY(dst_client_id) REFERENCES clients(client_id) ON DELETE RESTRICT
    , FOREIGN KEY(action_id) REFERENCES actions(action_id) ON DELETE RESTRICT
);


--
-- Initial inserts to get a prototype working
--

-- Type tables, required for data tables
INSERT INTO actions (name, system_name) VALUES ('Sync', 'SYNC');       -- 1
INSERT INTO actions (name, system_name) VALUES ('Delete', 'DELETE');   -- 2
INSERT INTO actions (name, system_name) VALUES ('Reindex', 'REINDEX'); -- 3

INSERT INTO client_types (name) VALUES ('Server'); -- 1
INSERT INTO client_types (name) VALUES ('Client'); -- 2

INSERT INTO media_package_types (name) VALUES ('Movie');     -- 1
INSERT INTO media_package_types (name) VALUES ('TV Base');   -- 2
INSERT INTO media_package_types (name) VALUES ('TV Season'); -- 3

-- Data tables, required for link tables
INSERT INTO clients (
    client_type_id, name, hostname, port, username, base_path
) VALUES (
    1, 'Media Server', 'atlas', 22, 'test', '/data/media/'
); -- 1

INSERT INTO clients (
    client_type_id, name, hostname, port, username, base_path
) VALUES (
    2, 'Media Player', 'prometheus', 22, 'test', '/data/media/'
); -- 2

INSERT INTO media_packages (
    package_type_id, name, folder_name, metadata_json
) VALUES (
    1, 'Movie 1', 'Movie 1 (2009)/', ''
); -- 1

INSERT INTO media_packages (
    package_type_id, name, folder_name, metadata_json
) VALUES (
    1, 'Movie 2', 'Movie 2 (2012)/', ''
); -- 2

INSERT INTO media_packages (
    package_type_id, name, folder_name, metadata_json
) VALUES (
    2, 'TV Show 1 - Base', 'TV Show 1/', ''
); -- 3

INSERT INTO media_packages (
    package_type_id, name, folder_name, metadata_json
) VALUES (
    3, 'TV Show 1 - Season 1', 'Season 1/', ''
); -- 4

INSERT INTO media_packages (
    package_type_id, name, folder_name, metadata_json
) VALUES (
    3, 'TV Show 1 - Season 2', 'Season 2/', ''
); -- 5

INSERT INTO media_files (
    hash
    , relative_path
) VALUES (
    'f793f8029fd2fde733020b6f1aa341e06bf3c222b8c0d46cd867066b4db31623'
    , 'Movie 1 (2009).mkv'
); -- 1

INSERT INTO media_files (
    hash
    , relative_path
) VALUES (
    'f793f8029fd2fde733020b6f1aa341e06bf3c222b8c0d46cd867066b4db31623'
    , 'Movie 1 (2009).xml'
); -- 2

INSERT INTO media_files (
    hash
    , relative_path
) VALUES (
    'f793f8029fd2fde733020b6f1aa341e06bf3c222b8c0d46cd867066b4db31623'
    , 'Movie 2 (2012) 1080p.mkv'
); -- 3

INSERT INTO media_files (
    hash
    , relative_path
) VALUES (
    'f793f8029fd2fde733020b6f1aa341e06bf3c222b8c0d46cd867066b4db31623'
    , 'TV Show 1 - Base.xml'
); -- 4

INSERT INTO media_files (
    hash
    , relative_path
) VALUES (
    'f793f8029fd2fde733020b6f1aa341e06bf3c222b8c0d46cd867066b4db31623'
    , 'TV Show 1 S01E01 - Epp 1.mkv'
); -- 5

INSERT INTO media_files (
    hash
    , relative_path
) VALUES (
    'f793f8029fd2fde733020b6f1aa341e06bf3c222b8c0d46cd867066b4db31623'
    , 'TV Show 1 S02E02 - Epp 2.mkv'
); -- 6

INSERT INTO media_files (
    hash
    , relative_path
) VALUES (
    'f793f8029fd2fde733020b6f1aa341e06bf3c222b8c0d46cd867066b4db31623'
    , 'TV Show 1 S02E02 - Epp 2.xml'
); -- 7

-- Link tables
INSERT INTO media_package_files (package_id, file_id) VALUES (1, 1);
INSERT INTO media_package_files (package_id, file_id) VALUES (1, 2);
INSERT INTO media_package_files (package_id, file_id) VALUES (2, 3);
INSERT INTO media_package_files (package_id, file_id) VALUES (3, 4);
INSERT INTO media_package_files (package_id, file_id) VALUES (4, 5);
INSERT INTO media_package_files (package_id, file_id) VALUES (5, 6);
INSERT INTO media_package_files (package_id, file_id) VALUES (5, 7);

INSERT INTO media_package_availability (client_id, package_id) VALUES (1, 1);
INSERT INTO media_package_availability (client_id, package_id) VALUES (1, 2);
INSERT INTO media_package_availability (client_id, package_id) VALUES (1, 3);
INSERT INTO media_package_availability (client_id, package_id) VALUES (1, 4);
INSERT INTO media_package_availability (client_id, package_id) VALUES (1, 5);
INSERT INTO media_package_availability (client_id, package_id) VALUES (2, 1);
INSERT INTO media_package_availability (client_id, package_id) VALUES (2, 3);
INSERT INTO media_package_availability (client_id, package_id) VALUES (2, 5);

INSERT INTO media_package_links (parent_id, child_id) VALUES (3, 4);
INSERT INTO media_package_links (parent_id, child_id) VALUES (3, 5);


-- Create a test job, pushing a media package to the Client from the Server
-- package(2) from client(1) to client(2) with action(1)
-- Sync (action) TV Show - Base (Package) from Media Server (client) to Media Player (client)
INSERT INTO job_queue (package_id, src_client_id, dst_client_id, action_id) VALUES (2, 1, 2, 1);

