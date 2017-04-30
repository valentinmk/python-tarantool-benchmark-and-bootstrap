"""Main app to launch benchmarks."""
import argparse
import asyncio
import logging
import sys
import traceback
from contextlib import suppress
if sys.platform == 'win32':
    import win_unicode_console
    win_unicode_console.enable()


def aiohttp_tarantool_multi(port=None, uvloop_enable=False):
    """TBD."""
    if uvloop_enable:
        logging.info("start aiohttp_tarantool_multi_uvloop")
        if sys.platform == 'win32':
            logging.error("D'oh! UVLoop is not support Windows!")
            sys.exit()
        else:
            import uvloop
        loop = uvloop.new_event_loop()
        asyncio.set_event_loop(loop)
    else:
        logging.info("start aiohttp_tarantool_multi")
        if sys.platform == 'win32':
            loop = asyncio.ProactorEventLoop()
        else:
            loop = asyncio.get_event_loop()
        asyncio.set_event_loop(loop)

    from data_interface.tarantool_driver import TarantoolDriver
    from aiohttp_server.aiohttpmulticonnect import AiohttpTarantoolMulti
    db = TarantoolDriver
    web_server = AiohttpTarantoolMulti(loop=loop, port=port, db=db)
    loop.create_task(web_server.start())
    loop.create_task(web_server.listner_for_statistics())
    return loop


def aiohttp_tarantool_one(port=None, uvloop_enable=False):
    """TBD."""
    if uvloop_enable:
        logging.info("start aiohttp_tarantool_one_uvloop")
        if sys.platform == 'win32':
            logging.error("D'oh! UVLoop is not support Windows!")
            sys.exit()
        else:
            import uvloop
        loop = uvloop.new_event_loop()
        asyncio.set_event_loop(loop)
    else:
        logging.info("start aiohttp_tarantool_one")
        if sys.platform == 'win32':
            loop = asyncio.ProactorEventLoop()
        else:
            loop = asyncio.get_event_loop()
        asyncio.set_event_loop(loop)

    from data_interface.tarantool_driver import TarantoolDriver
    from aiohttp_server.aiohttponeconnect import AiohttpUniversalOne
    db = TarantoolDriver()
    web_server = AiohttpUniversalOne(loop=loop, port=port, db=db)
    loop.create_task(web_server.start())
    loop.create_task(web_server.listner_for_statistics())
    return loop


def aiohttp_postgres_pool(port=None, uvloop_enable=False):
    """TBD."""
    if uvloop_enable:
        logging.info("start aiohttp_postgres_pool_uvloop")
        if sys.platform == 'win32':
            logging.error("D'oh! UVLoop is not support Windows!")
            sys.exit()
        else:
            import uvloop
        loop = uvloop.new_event_loop()
        asyncio.set_event_loop(loop)
    else:
        logging.info("start aiohttp_postgres_pool")
        if sys.platform == 'win32':
            loop = asyncio.ProactorEventLoop()
        else:
            loop = asyncio.get_event_loop()
        asyncio.set_event_loop(loop)
    from data_interface.postgres_driver import PostgresDriver
    from aiohttp_server.aiohttponeconnect import AiohttpUniversalOne
    pd = PostgresDriver(loop)
    db = loop.run_until_complete(pd.open())
    web_server = AiohttpUniversalOne(loop=loop, port=port, db=db)
    loop.create_task(web_server.start())
    loop.create_task(web_server.listner_for_statistics())
    return loop


def sanic_tarantool_one(port=None, uvloop_enable=False):
    """TBD."""
    if uvloop_enable:
        logging.info("start sanic_tarantool_one_uvloop")
        if sys.platform == 'win32':
            logging.error("D'oh! UVLoop is not support Windows!")
            sys.exit()
        else:
            import uvloop
        loop = uvloop.new_event_loop()
        asyncio.set_event_loop(loop)
    else:
        logging.info("start sanic_tarantool_one")
        if sys.platform == 'win32':
            loop = asyncio.ProactorEventLoop()
        else:
            loop = asyncio.get_event_loop()
        asyncio.set_event_loop(loop)

    from sanic_server.saniconeconnect import SanicTarantoolOne
    from data_interface.tarantool_driver import TarantoolDriver
    db = TarantoolDriver()
    web_server = SanicTarantoolOne(loop=loop, port=port, db=db)
    loop.create_task(web_server.start())
    loop.create_task(web_server.listner_for_statistics())
    return loop


def japronto_tarantool_one(port=None, uvloop_enable=False):
    """TBD."""
    if uvloop_enable:
        logging.info("start japronto_tarantool_one_uvloop")
        if sys.platform == 'win32':
            logging.error("D'oh! UVLoop is not support Windows!")
            sys.exit()
        else:
            import uvloop
        loop = uvloop.new_event_loop()
        asyncio.set_event_loop(loop)
    else:
        logging.info("start japronto_tarantool_one")
        if sys.platform == 'win32':
            loop = asyncio.ProactorEventLoop()
        else:
            loop = asyncio.get_event_loop()
        asyncio.set_event_loop(loop)

    from japronto_server import janprontooneconnect
    from data_interface.tarantool_driver import TarantoolDriver
    db = TarantoolDriver()
    janprontooneconnect.init(loop_param=loop, port_param=port, db_driver=db)
    loop.create_task(janprontooneconnect.listner_for_statistics())
    janprontooneconnect.start()
    # Return false for compatibility japronto implementation with other
    # servers
    # Japronto hard coded to create own loop and run_forever it :(
    return False  # It will raise Exeptions


def main():
    """Parsing arguments from cmd."""
    parser = argparse.ArgumentParser(
        description='This is launcher for benchmark exotarium.\n',
        epilog="And that's how you'd foo a bar")
    parser.add_argument("-l", "--logging",
                        help='Level of debugging messages',
                        required=False,
                        choices=['DEBUG',
                                 'INFO',
                                 'WARNING',
                                 'ERROR',
                                 'CRITICAL'])
    parser.add_argument("-p", "--port",
                        help='Web server port',
                        required=True)
    parser.add_argument("-e", "--engine",
                        help='select what server and db will be launched',
                        required=True,
                        choices=['aiohttp-tarantool-multi',
                                 'aiohttp-tarantool-one-uvloop',
                                 'aiohttp-tarantool-one',
                                 'aiohttp-postgres-pool',
                                 'aiohttp-postgres-pool-uvloop',
                                 'sanic-tarantool-one',
                                 'sanic-tarantool-one-uvloop',
                                 'japronto-tarantool-one',
                                 'japronto-tarantool-one-uvloop'])
    args = parser.parse_args()
    start_server(args.port, args.engine, args.logging)


def start_server(port=None, engine=None, logging_level='DEBUG'):
    """TBD."""
    if not logging_level:
        logging_level = 'DEBUG'
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s',
        level=logging.getLevelName(logging_level))  # just for visualisation
    logging.info("port={0}, engine={1}, logging level = {2}".format(
        str(port),
        str(engine),
        logging_level))
    switch_engine = {
        "aiohttp-tarantool-multi":
        {
            "engine": aiohttp_tarantool_multi,
            "uvloop": False
        },
        "aiohttp-tarantool-one-uvloop":
        {
            "engine": aiohttp_tarantool_one,
            "uvloop": True
        },
        "aiohttp-tarantool-one": {
            "engine": aiohttp_tarantool_one,
            "uvloop": False
        },
        "aiohttp-postgres-pool": {
            "engine": aiohttp_postgres_pool,
            "uvloop": False
        },
        "aiohttp-postgres-pool-uvloop": {
            "engine": aiohttp_postgres_pool,
            "uvloop": True
        },
        "sanic-tarantool-one": {
            "engine": sanic_tarantool_one,
            "uvloop": False
        },
        "sanic-tarantool-one-uvloop": {
            "engine": sanic_tarantool_one,
            "uvloop": True
        },
        "japronto-tarantool-one": {
            "engine": japronto_tarantool_one,
            "uvloop": False
        },
        "japronto-tarantool-one-uvloop": {
            "engine": japronto_tarantool_one,
            "uvloop": True
        },
    }

    try:
        loop = switch_engine[engine]["engine"](
            port=port,
            uvloop_enable=switch_engine[engine]["uvloop"])
    except KeyError as e:
        raise ValueError('Undefined unit: {}'.format(e.args[0]))

    try:
        logging.info("  --> Start main loop.")
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info("  < Stopping loop.")
        pass
    except:
        logging.error(traceback.format_exc())
    finally:
        loop.stop()
        pending = asyncio.Task.all_tasks(loop=loop)
        for task in pending:
            task.cancel()
            with suppress(asyncio.CancelledError):
                loop.run_until_complete(task)
        logging.info("   <- Main loop stopped.")
    loop.close()
    logging.info("  <-- Main loop closed.")


if __name__ == "__main__":
    main()
