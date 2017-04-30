"""Data interface class for PostgreSQL."""
import asyncpg
import logging
import random
import time
import ujson as json


class PostgresDriver:
    """Interface class to PostgreSQL database for stickers."""

    def __init__(self, loop=None):
        """Initialize connection pool. Make sure that we run in same loop."""
        self.loop = loop
        self.pool = asyncpg.create_pool(
            min_size=16,
            max_size=32,
            max_queries=50000,
            host='localhost',
            port=5432,
            user='tesla',
            password='secret',
            database='python_benchmark',
            loop=loop
        )

    async def open(self):
        """Patch for __init__ function that couldn't be coroutine."""
        self.db = await self.pool
        return self

    async def close(self):
        """Gracefully close all connections in the pool."""
        print('Close {}'.format(str(self.__hash__)))
        await self.db.close()

    async def create_random_vote(self):
        """Create secrrets for voting."""
        """This is done for prevent automatic or robotic voting."""
        random_number = random.randrange(0, 100000)
        current_time = int(time.time())
        result = await self.db.fetchrow(
            # 'select * from stickers order by random() limit 1;'
            'SELECT * FROM stickers TABLESAMPLE SYSTEM_ROWS(1);'
        )
        random_sticker = json.loads(result[1])
        token = await self.db.fetchval(
            "select md5('{}');".format(random_number))
        await self.db.fetch(
            "insert into secret (data) values"
            "('{}')".format(json.dumps([
                token,
                current_time,
                random_sticker[0],
                random_sticker[2]
            ])))
        return (random_sticker[2], token)

    async def update_votes(self, id, up, down):
        """Update vote counter in sticker record."""
        # update stickers set
        # data =
        # jsonb_set(
        #     jsonb_set(
        #         data,
        #         '{5}',
        #         (select (((data->>5)::int+1)::text)::jsonb from stickers
        #           where data->>0 = '61015')
        #         ),
        #         '{6}',
        #         (select (((data->>6)::int+1)::text)::jsonb from stickers
        #           where data->>0 = '61015')
        #         )
        # where data->>0 = '61015';
        result = await self.db.fetchval((
            'select data->>5 from stickers where data->>0 = \'{0}\''
            ).format(id)
        )
        if result:
            sql = ("update stickers set"
                   " data ="
                   " jsonb_set("
                   "     jsonb_set("
                   "         data,"
                   "         '{{4}}',"
                   "         (select "
                   "            (((data->>4)::int+{1})::text)::jsonb "
                   "            from stickers where data->>0 = '{0}')"
                   "         ),"
                   "         '{{5}}',"
                   "         (select "
                   "            (((data->>5)::int+{2})::text)::jsonb "
                   "            from stickers where data->>0 = '{0}')"
                   "         )"
                   " where data->>0 = '{0}';")
            sql = sql.format(id, up, down)
        else:
            sql = ("update stickers set "
                   " data = data || '[1,1]'"
                   " where data->>0 = '{0}';").format(id)
        await self.db.execute(sql)

    async def update_stats(self, user, vote, click):
        """Update server table to add new vote and click on sticker."""
        """Generally this function called from first page."""
        # update server set
        # data =
        # jsonb_set(
        #     jsonb_set(
        #         data,
        #         '{1}',
        #         (select (((data->>1)::int+1)::text)::jsonb
        #            from server limit 1)
        #         ),
        #         '{2}',
        #         (select (((data->>2)::int+1)::text)::jsonb
        #            from server limit 1)
        #         )
        # where true;
        sql = ("update server set"
               " data ="
               " jsonb_set("
               "   jsonb_set("
               "     jsonb_set("
               "         data,"
               "         '{{1}}',"
               "         (select (((data->>1)::int+{0})::text)::jsonb"
               "          from server limit 1)"
               "         ),"
               "       '{{2}}',"
               "       (select (((data->>2)::int+{1})::text)::jsonb"
               "        from server limit 1)"
               "       ),"
               "       '{{3}}',"
               "       (select (((data->>3)::int+{2})::text)::jsonb"
               "        from server limit 1)"
               "       )")
        sql = sql.format(int(user), int(vote), int(click))
        await self.db.execute(sql)

    async def update_user(self, cookie, remote_addr, user_agent):
        """Update visit count sessions record or insert new session."""
        # SELECT uuid_in(md5(random()::text || now()::text)::cstring);
        # CREATE UNIQUE INDEX session_uuid_idx ON sessions(((data->>0)::uuid));
        if not cookie:
            sql = ('SELECT '
                   'uuid_in(md5(random()::text || now()::text)'
                   '::cstring)::text')
            result = await self.db.fetchval(sql)
            # result = await self.md5.fetchrow()
            uuid = result
            await self.update_stats(1, 0, 0)
        else:
            uuid = cookie
        current_time = int(time.time())
        # -- UPSERT is PAIN
        # INSERT INTO sessions (data) VALUES
        # ('["983f2816-6ed2-4c4c-a13a-5432b67b6125", 1489337990,
        # 0, "00.00.00.00", "Not detected"]')
        # on conflict (((data ->> 0)::uuid))
        # do update set data = jsonb_set(SESSIONS.data, '{2}','1');
        sql = (
            " INSERT INTO sessions (data) VALUES"
            " ('[\"{0}\", {1}, {2}, \"{3}\", \"{4}\"]') "
            " on conflict (((data ->> 0)::uuid)) "
            " do update set data = "
            " jsonb_set("
            "    jsonb_set("
            "     jsonb_set("
            "      jsonb_set(SESSIONS.data, '{{1}}','{1}'),"
            "       '{{2}}',(select (((data->>2)::int+1)::text)::jsonb"
            "                from sessions where data->>0 = '{0}')),"
            "      '{{3}}', '\"{3}\"'),"
            "   '{{4}}', '\"{4}\"');")
        sql = sql.format(
            uuid, current_time, 0, remote_addr, user_agent)
        await self.db.execute(sql)
        return uuid

    async def do_post(self, vote_plus, vote_minus,
                      UPDATE_PLUS, UPDATE_MINUS, NO_UPDATE):
        """Check secret keys for vote and update rating and stats."""
        tuple_plus = await self.db.fetchrow((
            "select (data) from secret where data->>0 = '{}'"
        ).format(vote_plus))
        tuple_minus = await self.db.fetchrow((
             "select (data) from secret where data->>0 = '{}'"
        ).format(vote_minus))
        id_plus = json.loads(tuple_plus[0])[2]
        id_minus = json.loads(tuple_minus[0])[2]
        if vote_plus and vote_minus:
            await self.db.execute((
                "delete from secret where data->>0 = '{}'"
            ).format(vote_plus))
            await self.db.execute((
                "delete from secret where data->>0 = '{}'"
            ).format(vote_minus))

        if id_plus and id_minus:
            await self.update_rating(id_plus, +1)
            await self.update_rating(id_minus, -1)

            await self.update_votes(id_plus,  UPDATE_PLUS, NO_UPDATE)
            await self.update_votes(id_minus, NO_UPDATE,  UPDATE_MINUS)

            await self.update_stats(0, NO_UPDATE, UPDATE_PLUS)

    async def update_rating(self, id, direction):
        """Update stickers rating."""
        # update stickers set
        # data = jsonb_set(
        #   data,
        #   '{1}',
        #   (
        #       (select (data->>1)::int+1
        #           from stickers where data->>0 = '61000')::text)::jsonb)
        #   where data->>0 = '61000'
        sql = (
            "update stickers set"
            " data = jsonb_set("
            "   data,"
            "   '{{1}}',"
            "   ("
            "       (select (data->>1)::int+{1}"
            "           from stickers where data->>0 = '{0}')::text)::jsonb)"
            "   where data->>0 = '{0}'"
        ).format(id, direction)
        await self.db.execute(sql)

    async def get_top(self, limit, iterator):
        """Misnamed. Get top or bottom of stickers by rating."""
        if iterator == 'ITERATOR_LE':
            iterator = 'DESC'
        if iterator == 'ITERATOR_GE':
            iterator = 'ASC'
        sql = (
            "select data from stickers order by (data->>1)::int {} limit {}"
            ).format(iterator, limit)
        result = await self.db.fetch(sql)
        ret = []
        for i in result:
            ret.append(json.loads(i[0]))
        return ret

    async def get_statistics(self):
        sql = "select data from server"
        server = await self.db.fetchrow(sql)
        server = json.loads(server[0])
        sql = "SELECT count (data) FROM stickers"
        stickers_count = await self.db.fetchval(sql)
        sql = "SELECT count (data) FROM packs"
        packs_count = await self.db.fetchval(sql)
        statistics = {
            "users": server[1],
            "clicks": server[2],
            "votes": server[3],
            "packs_count": packs_count,
            "stickers_count": stickers_count,
        }
        logging.debug('Get statistics: {}'.format(str(statistics)))
        return statistics

    # Bellow functions related to Stickers API and don't using by main site

    async def get_all_packs(self):
        sql = "Select data from packs;"
        result = await self.db.fetch(sql)
        result_array = []
        for row in result:
            result_array.append(json.loads(row[0]))
        return result_array

    async def get_all_stickers_in_pack(self, pack_url):
        sql = "Select data from stickers where data->>3 = '{}';".format(pack_url)
        result = await self.db.fetch(sql)
        result_array = []
        for row in result:
            result_array.append(json.loads(row[0]))
        return result_array

    async def get_stickers_by_name(self, name):
        sql = "Select data from stickers where data->>0 = '{}';".format(name)
        result = await self.db.fetch(sql)
        result_array = []
        for row in result:
            result_array.append(json.loads(row[0]))
        return result_array
        return result.data
