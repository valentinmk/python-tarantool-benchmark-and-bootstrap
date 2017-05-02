"""Upload Telegram stickers data in your Tarantool pygbu instance."""
import aiohttp
import aiotarantool
import logging
import sys
import time
import asyncio
import uvloop
import ujson as json


class TarantoolDriver():
    """TBD."""

    def __init__(self, host=None, port=None):
        """TBD."""
        self.taran = aiotarantool.connect(
            "127.0.0.1",
            3311,
            user='tesla',
            password="secret"
            )

    async def close(self):
        """TBD."""
        print('Close {}'.format(str(self.__hash__)))
        await self.taran.close()

    async def sudo(self, command):
        """TBD."""
        await self.taran.eval(
            "box.session.su('admin')")
        data = await command
        await self.taran.eval(
            "box.session.su('tesla')")
        return data

    async def truncate(self, space):
        """TBD."""
        command = self.taran.eval(
            "box.space.{}:truncate()".format(str(space))
        )
        await self.sudo(command)

    async def insert_pack(self, name, rating, url):
        """TBD."""
        await self.taran.insert(
            'packs',
            (
                name,
                rating,
                url
            )
        )

    async def insert_stickers(self,
                              id,
                              rating,
                              url,
                              pack_url,
                              vote_plus=0,
                              vote_minus=0):
        """TBD."""
        await self.taran.insert(
            'stickers',
            (
                id,
                rating,
                url,
                pack_url,
                vote_plus,
                vote_minus
            )
        )


class GetExternalData():
    """Class implement full parse of stickers api.

    For faster processing rewrite it to get list of packs from /sticker api
    point, and get all stickers in pack from /stickers/{packs} api point.
    """

    def __init__(self,
                 host="db.teslarnd.ru",
                 port="1717",
                 point="stickers",
                 db=None):
        """TBD."""
        self.api_host = host
        self.api_port = port
        self.api_point = point
        self.cs = None
        self.db = db

    async def get_packs_list(self):
        """TBD."""
        url = (
            "http://" +
            self.api_host + ":" +
            self.api_port + "/" +
            self.api_point
            )

        async with self.cs.get(url) as r:
            packs_list = await r.json(loads=json.loads,
                                      content_type='application/json')
            # logging.debug(packs_list)
        return packs_list

    async def get_pack_info(self, url):
        """TBD."""
        async with self.cs.get(url) as r:
            if r.status == 200:
                pack_info = await r.json(loads=json.loads,
                                         content_type='application/json')
            else:
                logging.error("Empty pack info. Status = {}".format(
                    r.status
                ))
                pack_info = {}
        return pack_info

    async def get_sticker_info(self, url):
        """TBD."""
        async with self.cs.get(url) as r:
            if r.status == 200:
                sticker_info = await r.json(loads=json.loads,
                                            content_type='application/json')
            else:
                logging.error("Empty sticker info. Status = {}".format(
                    r.status
                ))
                sticker_info = {}

        return sticker_info

    async def process(self):
        """TBD."""
        self.cs = aiohttp.ClientSession()
        await self.db.truncate('packs')
        await self.db.truncate('stickers')
        all_packs_list = await self.get_packs_list()
        packs_list = all_packs_list.get('packs', "No data")
        packs_counter = len(packs_list)
        for pack in packs_list:
            logging.debug(packs_list[pack].get('api', {}))
            pack_info = await self.get_pack_info(
                packs_list[pack].get('api', {}))
            if pack_info:
                await self.db.insert_pack(
                    name=pack_info.get('packs'),
                    rating=0,
                    url=pack_info.get('url'))
                logging.info("Insert {} pack - ok, {} left".format(
                    pack_info.get('packs'),
                    packs_counter
                ))
                packs_counter = packs_counter - 1
            sticker_list = pack_info.get('stickers', {})
            stickers_count = 0
            for sticker in sticker_list:
                logging.debug(sticker_list[sticker].get('api'))
                sticker_info = await self.get_sticker_info(
                    sticker_list[sticker].get('api'))
                if sticker_info:
                    await self.db.insert_stickers(
                        id=sticker_info.get('id'),
                        rating=int(sticker_info.get('rating')),
                        url=sticker_info.get('url'),
                        pack_url=sticker_info.get('pack_url'),
                    )
                    stickers_count = stickers_count + 1
                logging.debug(sticker_info.get('id'))
            logging.info("Insert {} - {} stickers - ok".format(
                pack_info.get('packs'),
                stickers_count))
        self.cs.close()


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s',
        level=logging.getLevelName(logging.INFO))  # just for visualisation
    logging.info("Start processing")
    start = time.time()
    if sys.platform == 'win32':
        logging.warning("D'oh! UVLoop is not support Windows!")
        loop = asyncio.ProactorEventLoop()
    else:
        loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(GetExternalData(db=TarantoolDriver()).process())
    logging.info("Total time {}s".format(str(time.time()-start)))
    logging.info("Stop processing")
