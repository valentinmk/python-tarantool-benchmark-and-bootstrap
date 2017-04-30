import asyncio
import aiotarantool
import ujson as json
import asyncpg
import time
from contextlib import suppress

start = time.time()


async def get_pool():
    pool = await asyncpg.create_pool(
        min_size=1,
        max_size=50,
        max_queries=50000,
        host='localhost',
        port=5432,
        user='tesla',
        password='secret',
        database='python_benchmark'
        )
    return pool


async def pg_request(sql, pool):
    async with pool.acquire() as connection:
        result = await connection.fetch(sql)
        return result


async def tt_request(space=None, request=None):
    if not request:
        request = []
    else:
        request = [request]
    taran = aiotarantool.connect(
        "localhost",
        3311,
        user='tesla',
        password="secret"
        )
    result = await taran.call(
        'box.space.{}:select'.format(space),
        request
    )
    return result


async def yield_num(result, queue, table):
    j = 1
    stop = result.rowcount
    values = ""
    for i in result:
        if (j % 2048) == 0 or j == stop:

            values = '{}(\'{}\') '.format(
                values, json.dumps(i).replace("'", "`"))
            sql = "INSERT INTO {} (data) VALUES {}".format(
                table, values)
            values = ""
            queue.put_nowait(sql)
        else:
            values = '{}(\'{}\'), '.format(
                values, json.dumps(i).replace("'", "`"))
        j = j + 1


class AsyncIterable:
    def __init__(self, queue):
        self.queue = queue
        self.done = []

    def __aiter__(self):
        return self

    async def __anext__(self):
        data = await self.fetch_data()
        if data is not None:
            return data
        else:
            raise StopAsyncIteration

    async def fetch_data(self):
        while not self.queue.empty():
            self.done.append(self.queue.get_nowait())
        if not self.done:
            return None
        return self.done.pop(0)


async def consume_num(queue, pool):
    async for i in AsyncIterable(queue):
        async with pool.acquire() as connection:
            await connection.execute(i)


def main():
    event_loop = asyncio.get_event_loop()
    queue = asyncio.Queue(loop=event_loop)
    pool = event_loop.run_until_complete(get_pool())
    print("Start loading")

    # print("Table trancated")
    result = ('stickers', 'server', 'secret', 'sessions', 'packs')
    sqls = {}

    try:
        for i in result:
            result = event_loop.run_until_complete(pg_request(
                'TRUNCATE TABLE {}'.format(i), pool
                )
            )
            print("-- {} trancated".format(i))
            start_l = time.time()
            sqls[i] = event_loop.run_until_complete(tt_request(i))
            print("<- {} loaded from tarantool in {}s".format(
                i,
                round(time.time() - start_l, 3)
                )
            )
            event_loop.create_task(yield_num(sqls[i], queue, i))
            start_l = time.time()
            event_loop.run_until_complete(consume_num(queue, pool))
            print("-> {} uploaded to postgres in {}s".format(
                i,
                round(time.time()-start_l, 3)
                )
            )
    finally:
        event_loop.stop()
        pending = asyncio.Task.all_tasks(loop=event_loop)
        for task in pending:
            task.cancel()
            with suppress(asyncio.CancelledError):
                event_loop.run_until_complete(task)
        event_loop.close()


if __name__ == '__main__':
    main()
    print('Exec time = {}'.format(round(time.time()-start, 3)))
