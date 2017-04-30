from japronto import Application
import time
# from time import time
import aiotarantool
import tarantool
from tarantool import const
import traceback
import asyncio
import uvloop


loop = uvloop.new_event_loop()
asyncio.set_event_loop(loop)
app = Application()
app._loop = loop


class TarantoolDriver():
    def __init__(self, host=None, port=None):
        if host and port:
            self.taran = aiotarantool.connect(
                str(host),
                int(port),
                user='tesla',
                password="secret"
                )
        else:
            self.taran = aiotarantool.connect(
                "127.0.0.1",
                3311,
                user='tesla',
                password="secret"
                )

    async def close(self):
        print('Close {}'.format(str(self.__hash__)))
        await self.taran.close()

    async def update_user(self, cookie, remote_addr, user_agent):
        if not cookie:
            result = await self.taran.eval(
                "uuid = require('uuid')"
                "return (uuid.str())"
            )
            uuid = result[0]
        else:
            uuid = cookie
        current_time = int(time.time())
        result = await self.taran.call(
            'box.space.sessions:upsert',
            (uuid, current_time, 0, remote_addr, user_agent),
            (
                ("=", 2, current_time),
                ("+", 3, 1),
                ("=", 4, remote_addr),
                ("=", 5, user_agent)
            )
        )
        return uuid

    async def get_top(self, limit, iterator):
        if iterator == 'ITERATOR_LE':
            iterator = const.ITERATOR_LE
        result = await self.taran.select(
             space_name='stickers',
             key=[],
             index=1,
             offset=0,
             limit=limit,
             iterator=iterator
        )
        return result.data

    async def get_top_lite(self, limit, iterator):
        if iterator == 'ITERATOR_LE':
            iterator = const.ITERATOR_LE
        result = await self.taran.select(
            space_name='stickers',
            key=[],
            index=1,
            offset=0,
            limit=limit
        )
        return result.data


class TarantoolDriverPool():
    def __init__(self, n=0):
        self.pool = []
        self.nconnnection = n
        self.i = 0
        print(range(0, n))
        for i in range(0, n):
            print(i)
            self.pool.append(TarantoolDriver())

    def next(self):
        j = self.i % self.nconnnection
        self.i += 1
        # print(self.i)
        # print(j)
        return self.pool[j]


class TarantoolDriverServerPool():
    def __init__(self, servers=None):
        self.pool = []
        self.npool = len(servers)
        self.servers = servers
        self.i = 0
        print(servers)
        print(len(servers))
        for i in servers:
            print(i)
            self.pool.append(
                TarantoolDriver(
                    host=i['host'],
                    port=i['port']
                    )
                )
        print(self.pool)

    def next(self):
        j = self.i % self.npool
        self.i += 1
        # print(self.i)
        # print(self.pool[j])
        return self.pool[j]


db = TarantoolDriver()
db_pool = TarantoolDriverPool(n=32)
db_pool_server = TarantoolDriverServerPool(
    servers=(
        {'host': '127.0.0.1', 'port': 3311},
        # {'host': '127.0.0.1', 'port': 3321},
        # {'host': '127.0.0.1', 'port': 3322},
        # {'host': '127.0.0.1', 'port': 3323}
    ))
db_sync = tarantool.connect(
    host='127.0.0.1',
    port='3311',
    user='tesla',
    password='secret')
stickers = db_sync.space('stickers')


async def select_async(request):
    top = await db.get_top(10, 'ITERATOR_LE')
    # return request.Response(text='Hello world!\n'+str(top))
    return request.Response(text='Hello world!\n')


async def select_async_lite(request):
    top = await db.get_top_lite(9, 'ITERATOR_LE')
    # return request.Response(text='Hello world!\n'+str(top))
    return request.Response(text='Hello world!\n')


async def update_async(request):
    top = await db.update_user(cookie=False,
                               remote_addr='0.0.0.0',
                               user_agent='TESTING')
    # return request.Response(text='Hello world!\n'+str(top))
    return request.Response(text='Hello world!\n')


async def select_async_pool(request):
    top = await db_pool.next().get_top(10, 'ITERATOR_LE')
    # return request.Response(text='Hello world!\n'+str(top))
    return request.Response(text='Hello world!\n')


async def select_async_pool_lite(request):
    top = await db_pool.next().get_top_lite(9, 'ITERATOR_LE')
    # return request.Response(text='Hello world!\n'+str(top))
    return request.Response(text='Hello world!\n')


async def update_async_pool(request):
    top = await db_pool.next().update_user(cookie=False,
                                           remote_addr='0.0.0.0',
                                           user_agent='TESTING')
    # return request.Response(text='Hello world!\n'+str(top))
    return request.Response(text='Hello world!\n')


async def select_async_pool_server(request):
    top = await db_pool_server.next().get_top(10, 'ITERATOR_LE')
    # return request.Response(text='Hello world!\n'+str(top))
    return request.Response(text='Hello world!\n')


async def update_async_pool_server(request):
    top = await db_pool_server.next().update_user(cookie=False,
                                                  remote_addr='0.0.0.0',
                                                  user_agent='TESTING')
    # return request.Response(text='Hello world!\n'+str(top))
    return request.Response(text='Hello world!\n')


def select_sync(request):
    top = stickers.select(
         key=[],
         index=1,
         offset=0,
         limit=10,
         iterator=tarantool.const.ITERATOR_LE
    )
    # return request.Response(text='Hello world!\n'+str(top))
    return request.Response(text='Hello world!\n')


app.router.add_route('/select_async', select_async)
app.router.add_route('/select_async_lite', select_async_lite)
# app.router.add_route('/select_async_pool', select_async_pool)
# app.router.add_route('/select_async_pool_lite', select_async_pool_lite)
# app.router.add_route('/select_async_pool_server', select_async_pool_server)
app.router.add_route('/update_async', update_async)
# app.router.add_route('/update_async_pool', update_async_pool)
# app.router.add_route('/update_async_pool_server', update_async_pool_server)
app.router.add_route('/select_sync', select_sync)
app.run(port=1717, debug=False)
