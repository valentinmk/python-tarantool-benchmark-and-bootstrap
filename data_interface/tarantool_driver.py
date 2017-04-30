"""Data source class implement unified interface for webservers views."""
import aiotarantool
# import asyncio
import logging
import random
import time
# import traceback
from tarantool import error, const


class TarantoolDriver:
    """Interface class to manipulate data in Tarantool DB."""

    def __init__(self):
        """Initiate creating a connection string."""
        """Connection to Tarantool will be opened at first query."""
        """We keep connection opened. Only one connection will used for """
        """all queries."""
        self.taran = aiotarantool.connect(
            # 'db.teslarnd.ru',
            "127.0.0.1",
            3311,
            user='tesla',
            password="secret"
        )

    async def close(self):
        """Close tarantool connection."""
        logging.debug('Close {}'.format(str(self.taran)))
        await self.taran.close()

    async def create_random_vote(self):
        """Hide link in secret space and return md5 for it."""
        random_number = random.randrange(0, 1000)
        random_sticker = await self.taran.call(
            "box.space.stickers.index.p_name:random",
            (random_number)
        )
        token = await self.taran.eval(
            "digest = require('digest')"
            "return (digest.md5_hex(digest.urandom(32)))")
        current_time = int(time.time())
        await self.taran.insert(
            'secret',
            (
                token.data[0],
                current_time,
                random_sticker.data[0][0],
                random_sticker.data[0][2]
            )
        )
        return (random_sticker.data[0][2], token.data[0])

    async def update_votes(self, id, up, down):
        try:
            await self.taran.update(
                "stickers",
                id,
                (
                    ('+', 4, up),
                    ('+', 5, down),
                )
            )
        except error.DatabaseError:
            logging.info('New sticker, votes didn\'t set. Create votes.')
            await self.taran.update(
                "stickers",
                1,
                (
                    ('=', 4, up),
                    ('=', 5, down),
                )
            )

    async def update_stats(self, user, vote, click):
        await self.taran.update(
            "server",
            1,
            (
                ('+', 1, int(user)),
                ('+', 2, int(vote)),
                ('+', 3, int(click)),
            )
        )

    async def update_user(self, cookie, remote_addr, user_agent):
        if not cookie:
            result = await self.taran.eval(
                "uuid = require('uuid')"
                "return (uuid.str())"
            )
            uuid = result[0]
            await self.update_stats(1, 0, 0)
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

    async def do_post(self, vote_plus, vote_minus,
                      UPDATE_PLUS, UPDATE_MINUS, NO_UPDATE):
        tuple_plus = await self.taran.select('secret', vote_plus)
        tuple_minus = await self.taran.select('secret', vote_minus)

        if len(tuple_plus) > 0 and len(tuple_minus) > 0:
            id_plus = tuple_plus[0][2]
            id_minus = tuple_minus[0][2]
        else:
            logging.debug(
                "Vote for sticker without secret. Maybe double click?")
            return

        if vote_plus and vote_minus:
            await self.taran.delete('secret', vote_plus)
            await self.taran.delete('secret', vote_minus)

        if id_plus and id_minus:
            await self.update_rating(id_plus, +1)
            await self.update_rating(id_minus, -1)

            await self.update_votes(id_plus, UPDATE_PLUS, NO_UPDATE)
            await self.update_votes(id_minus, NO_UPDATE, UPDATE_MINUS)
            await self.update_stats(0, NO_UPDATE, UPDATE_PLUS)

    async def update_rating(self, id, direction):
        await self.taran.update(
            "stickers",
            id,
            op_list=(
                ('+', 1, direction),
            )
        )

    async def get_top(self, limit, iterator):
        if iterator == 'ITERATOR_LE':
            iterator = const.ITERATOR_LE
        if iterator == 'ITERATOR_GE':
            iterator = const.ITERATOR_GE
        result = await self.taran.select(
            space_name='stickers',
            key=[],
            index=1,
            offset=0,
            limit=limit,
            iterator=iterator
        )
        return result.data

    async def get_statistics(self):
        server = await self.taran.select(
            space_name='server',
            key=[]
        )
        stickers_count = await self.taran.call(
            'box.space.stickers:count',
            ()
        )
        packs_count = await self.taran.call(
            'box.space.packs:count',
            ()
        )
        statistics = {
            "users": server.data[0][1],
            "clicks": server.data[0][2],
            "votes": server.data[0][3],
            "packs_count": packs_count[0][0],
            "stickers_count": stickers_count[0][0],
        }
        logging.debug('Get statistics: {}'.format(str(statistics)))
        return statistics

    # Bellow functions related to Stickers API and don't using by main site

    async def get_all_packs(self):
        result = await self.taran.select(
            space_name='packs',
            key=[],
            index=1,
            offset=0
        )
        return result.data

    async def get_all_stickers_in_pack(self, pack_url):
        result = await self.taran.select(
            space_name='stickers',
            key=pack_url,
            index=2,
            offset=0
        )
        return result.data

    async def get_stickers_by_name(self, name):
        result = await self.taran.select(
            space_name='stickers',
            key=name,
            index=0,
            offset=0
        )
        return result.data
