-- This is default tarantool initialization file
-- with easy to use configuration examples including
-- replication, sharding and all major features
-- Complete documentation available in:  http://tarantool.org/doc/
--
-- To start this instance please run `systemctl start tarantool@example` or
-- use init scripts provided by binary packages.
-- To connect to the instance, use "sudo tarantoolctl enter example"
-- Features:
-- 1. Database configuration
-- 2. Binary logging and snapshots
-- 3. Replication
-- 4. Automatinc sharding
-- 5. Message queue
-- 6. Data expiration

-----------------
-- Configuration
-----------------
box.cfg {
    ------------------------
    -- Network configuration
    ------------------------

    -- The read/write data port number or URI
    -- Has no default value, so must be specified if
    -- connections will occur from remote clients
    -- that do not use “admin address”
    listen = 'localhost:3311';
    -- listen = '*:3301';

    -- The server is considered to be a Tarantool replica
    -- it will try to connect to the master
    -- which replication_source specifies with a URI
    -- for example konstantin:secret_password@tarantool.org:3301
    -- by default username is "guest"
    -- replication_source="127.0.0.1:3102";

    -- The server will sleep for io_collect_interval seconds
    -- between iterations of the event loop
    io_collect_interval = nil;

    -- The size of the read-ahead buffer associated with a client connection
    readahead = 16320;

    ----------------------
    -- Memtx configuration
    ----------------------

    -- An absolute path to directory where snapshot (.snap) files are stored.
    -- If not specified, defaults to /var/lib/tarantool/INSTANCE
    -- memtx_dir = nil;

    -- How much memory Memtx engine allocates
    -- to actually store tuples, in bytes.
    memtx_memory = 384 * 1024 * 1024; -- 384Mb

    -- Size of the smallest allocation unit, in bytes.
    -- It can be tuned up if most of the tuples are not so small
    memtx_min_tuple_size = 16;

    -- Size of the largest allocation unit, in bytes.
    -- It can be tuned up if it is necessary to store large tuples
    memtx_max_tuple_size = 1 * 1024 * 1024; -- 1Mb

    ----------------------
    -- Vinyl configuration
    ----------------------

    -- An absolute path to directory where Vinyl files are stored.
    -- If not specified, defaults to /var/lib/tarantool/INSTANCE
    -- vinyl_dir = nil;

    -- How much memory Vinyl engine can use for in-memory level, in bytes.
    vinyl_memory = 256 * 1024 * 1024; -- 256Mb

    -- How much memory Vinyl engine can use for caches, in bytes.
    vinyl_cache = 128 * 1024 * 1024; -- 128Mb

    -- The maximum number of background workers for compaction.
    vinyl_threads = 2;

    ------------------------------
    -- Binary logging and recovery
    ------------------------------

    -- An absolute path to directory where write-ahead log (.xlog) files are
    -- stored. If not specified, defaults to /var/lib/tarantool/INSTANCE
    -- wal_dir = nil;

    -- Specify fiber-WAL-disk synchronization mode as:
    -- "none": write-ahead log is not maintained;
    -- "write": fibers wait for their data to be written to the write-ahead log;
    -- "fsync": fibers wait for their data, fsync follows each write;
    wal_mode = "write";

    -- How many log records to store in a single write-ahead log file
    rows_per_wal = 5000000;

    -- The interval between actions by the snapshot daemon, in seconds
    checkpoint_interval = 15 * 60; -- 15 minutes

    -- The maximum number of snapshots that the snapshot daemon maintans
    checkpoint_count = 4 * 24; -- store snapshots for last 24 hours

    -- Reduce the throttling effect of box.snapshot() on
    -- INSERT/UPDATE/DELETE performance by setting a limit
    -- on how many megabytes per second it can write to disk
    snap_io_rate_limit = nil;

    -- Don't abort recovery if there is an error while reading
    -- files from the disk at server start.
    force_recovery = true;

    ----------
    -- Logging
    ----------

    -- How verbose the logging is. There are six log verbosity classes:
    -- 1 – SYSERROR
    -- 2 – ERROR
    -- 3 – CRITICAL
    -- 4 – WARNING
    -- 5 – INFO
    -- 6 – DEBUG
    log_level = 5;

    -- By default, the log is sent to /var/log/tarantool/INSTANCE.log
    -- If logger is specified, the log is sent to the file named in the string
    -- logger = "example.log";

    -- If true, tarantool does not block on the log file descriptor
    -- when it’s not ready for write, and drops the message instead
    log_nonblock = true;

    -- If processing a request takes longer than
    -- the given value (in seconds), warn about it in the log
    too_long_threshold = 0.5;

    -- Inject the given string into server process title
    -- custom_proc_title = 'example';
}

local function bootstrap()
    box.schema.user.create('tesla', { password = 'secret' })
    box.schema.user.grant('tesla', 'replication')
    box.schema.user.grant('tesla', 'read,write,execute', 'universe')
    -- Sticker space
    -- p_ stands for primary index
    local stickers = box.schema.create_space('stickers')
    stickers:create_index('p_name', {
      type = 'TREE', parts = {1, 'string'}
    })

    -- Rating index
    -- s_ stands for secondary index
    stickers:create_index('s_rating', {
      type = 'TREE',
      unique = false,
      parts = {2, 'integer'}
    })

    -- Name stickers index
    -- stickers:create_index('s_names', {
    --     type ='HASH', parts = {3, 'string', 4, 'string'}
    -- })
    -- Packs url for stickers
    stickers:create_index('s_pack_url', {
        type ='TREE',
        unique = false,
        parts = {4,'string'}
    })

    -----------------------------------

    -- Sticker pack space
    local packs = box.schema.create_space('packs')
    -- Sticker pack index
    packs:create_index('p_name', {
        type = 'HASH', parts = {1, 'string'}
    })

    -- Pack rating index
    packs:create_index('s_rating', {
        type = 'TREE',
        unique = false,
        parts = {2, 'integer'}
    })

    -----------------------------------
    -- Secret links space
    local secret = box.schema.create_space('secret')

    -- Secret key index
    secret:create_index('p_md5', {
        type = 'HASH', parts = {1, 'string'}
    })

    -- Secret time index
    secret:create_index('s_time', {
        type = 'TREE',
        unique = false,
        parts = {2, 'integer'}
    })

    -----------------------------------
    -- Session space
    local sessions = box.schema.create_space('sessions')

    -- Unique user index
        sessions:create_index('p_uuid', {
        type = 'HASH', parts = {1, 'string'}
    })

    -- User time creation index
    sessions:create_index('s_time', {
        type = 'TREE',
        unique = false,
        parts = {2, 'integer'}
    })

    -----------------------------------
    -- Server statistics space
    local server = box.schema.create_space('server')

    -- Just index
        server:create_index('p_id', {
        type = 'TREE', parts = {1, 'unsigned'}
    })
    -- Create tuple (it will be just one in space)
    server:insert{1, 0, 0, 0}

end

-- for first run create a space and add set up grants
box.once('stickers-1.1', bootstrap)

-----------------------
-- Automatinc sharding
-----------------------
-- N.B. you need install tarantool-shard package to use shadring
-- Docs: https://github.com/tarantool/shard/blob/master/README.md
-- Example:
--  local shard = require('shard')
--  local shards = {
--      servers = {
--          { uri = [[host1.com:4301]]; zone = [[0]]; };
--          { uri = [[host2.com:4302]]; zone = [[1]]; };
--      };
--      login = 'tester';
--      password = 'pass';
--      redundancy = 2;
--      binary = '127.0.0.1:3301';
--      monitor = false;
--  }
--  shard.init(shards)

-----------------
-- Message queue
-----------------
-- N.B. you need to install tarantool-queue package to use queue
-- Docs: https://github.com/tarantool/queue/blob/master/README.md
-- Example:
--  local queue = require('queue')
--  queue.start()
--  queue.create_tube(tube_name, 'fifottl')

-------------------
-- Data expiration
-------------------
-- N.B. you need to install tarantool-expirationd package to use expirationd
-- Docs: https://github.com/tarantool/expirationd/blob/master/README.md
-- Example (deletion of all tuples):
--  local expirationd = require('expirationd')
--  local function is_expired(args, tuple)
--    return true
--  end
--  expirationd.start("clean_all", space.id, is_expired {
--    tuple_per_item = 50,
--    full_scan_time = 3600
--  })
