"""TBD."""
import aiohttp_jinja2
import asyncio
import logging
import os
import traceback
from aiohttp import web
from aiohttp_session import get_session
from jinja2 import PackageLoader, Environment
from .helper import AiohttpHelper


class AiohttpUniversalOne (AiohttpHelper):
    """TBD."""

    MIN_VOTES = 20                  # Number of votes to show the ugly
    UPDATE_PLUS = 1                 # Increment for positive update
    UPDATE_MINUS = -1               # Increment for negative update
    NO_UPDATE = 0
    HIDDEN = 'static/Question.svg'    # Picture for hidden element

    def __init__(self, loop=None, port=None, db=None):
        """Init AiohttpTarantoolOne with loop, port and db."""
        super().__init__(loop=loop, port=port)
        self.db = db
        self.statistics = {
            "packs_count": "empty",
            "stickers_count": "empty",
            "clicks": "empty",
            "votes": "empty",
            "users": "empty"}
        self.jinja = Environment(
            loader=PackageLoader('aiohttp_server', 'templates'),
            # enable_async=False,
            auto_reload=False)

    async def listner_for_statistics(self):
        while True:
            try:
                self.statistics = await self.db.get_statistics()
            except:  # “too broad exception”
                logging.error("Error while db.get_statictics()")
                logging.error(traceback.format_exc())
            await asyncio.sleep(5)
        return
        # Cause RecursionError: maximum recursion depth exceeded
        # return await self.listner_for_statistics()

    @aiohttp_jinja2.template('good.html')
    async def async_good(self, request):
        """TBD."""
        data = {
            "title": "Top of the best stikers for Telegram",
            "active_good": "class=\"active\"",
            "active_bad": "",
            "top": {}
        }
        await self.session_handler(request=request)
        data["top"] = await self.db.get_top(9, 'ITERATOR_LE')
        return web.Response(
            text=self.jinja.get_template('good.html').render(
                title=data["title"],
                active_good=data["active_good"],
                active_bad=data["active_bad"],
                top=data["top"]
                ),
            content_type='text/html')

    # @aiohttp_jinja2.template('bad.html')
    async def action_bad(self, request):
        """TBD."""
        data = {
            "title": "Top of bad stikers for Telegram",
            "active_good": "",
            "active_bad": "class=\"active\"",
            "top": {}
        }
        await self.session_handler(request=request)
        data['top'] = await self.db.get_top(9, 'ITERATOR_GE')
        return web.Response(
            text=self.jinja.get_template('good.html').render(
                title=data["title"],
                active_good=data["active_good"],
                active_bad=data["active_bad"],
                top=data["top"]
            ),
            content_type='text/html')

    async def action_ugly(self, request):
        """TBD."""
        return web.Response(text="UGLY")

    # @aiohttp_jinja2.template('about.html')
    async def action_about(self, request):
        """TBD."""
        data = {"title": "About and statistics"}
        data.update(self.statistics)
        return web.Response(
            text=self.jinja.get_template('about.html').render(
                title=data['title'],
                packs_count=data['packs_count'],
                stickers_count=data['stickers_count'],
                clicks=data['clicks'],
                votes=data['votes'],
                users=data['users']
            ),
            content_type='text/html')

    # @aiohttp_jinja2.template('index.html')
    async def handle(self, request):
        """TBD."""
        data = {
            "super": "hot",
            "random_image": {
                "left": {
                    "url": "",
                    "token_plus": 0,
                    "token_minus": 0
                },
                "right": {
                    "url": "",
                    "token_plus": 0,
                    "token_minus": 0
                },
            },
            "title": "Good and Bad Telegram stickers"
        }
        await self.session_handler(request=request)
        post = await request.post()
        if len(post) > 0:
            if post['vote_plus'] and post['vote_minus']:
                logging.debug("{} {}".format(
                    str(post['vote_plus']),
                    str(post['vote_minus'])
                ))
                await self.db.do_post(
                    post['vote_plus'],
                    post['vote_minus'],
                    self.UPDATE_PLUS,
                    self.UPDATE_MINUS,
                    self.NO_UPDATE)
        data["random_image"]["left"]["url"], \
            data["random_image"]["left"]["token_plus"] \
            = await self.db.create_random_vote()
        data["random_image"]["right"]["url"], \
            data["random_image"]["right"]["token_plus"] \
            = await self.db.create_random_vote()
        data["random_image"]["right"]["token_minus"] = \
            data["random_image"]["right"]["token_plus"]
        data["random_image"]["left"]["token_minus"] = \
            data["random_image"]["left"]["token_plus"]
        await self.db.update_stats(0, self.UPDATE_PLUS, self.NO_UPDATE)
        return web.Response(
            text=self.jinja.get_template('index.html').render(
                title=data["title"],
                random_image=data["random_image"],
            ),
            content_type='text/html')

    async def session_handler(self, request):
        """Handle sessions for request."""
        session = await get_session(request)
        if request.transport.get_extra_info('peername') is not None:
            host, port = request.transport.get_extra_info('peername')
            remote_addr = host
        else:
            remote_addr = None
        try:
            user_agent = request.headers['User-Agent']
        except:
            user_agent = 'Not detected'
        if session.new is True:
            new_cookie = await self.db.update_user(
                None,
                remote_addr,
                user_agent)
        else:
            new_cookie = await self.db.update_user(
                session['stickers'],
                remote_addr,
                user_agent)
        session['stickers'] = new_cookie
        return session

    # API to stickers data

    async def stickers_api(self, request):
        """TBD."""
        resp = {"packs": None,
                "stickers": None
                }
        resp["packs"] = request.match_info.get("packs",
                                               "Empty in request")
        resp["stickers"] = request.match_info.get("stickers",
                                                  "Empty in request")

        if resp["stickers"] != "Empty in request":
            resp.update({"comment": "Get sticker info"})
            resp.update({"name": resp["stickers"]})
            sticker = await self.db.get_stickers_by_name(resp["stickers"])
            resp.update({"url": sticker[0][2]})
            resp.update({"id": sticker[0][0]})
            resp.update({"rating": sticker[0][1]})
            resp.update({"pack_url": sticker[0][3]})
        elif resp["packs"] != "Empty in request":
            resp.update({"comment": "Get pack info"})
            resp.update({"stickers": {}})
            packs_url = "https://tlgrm.eu/stickers/" + resp["packs"]
            resp.update({"url": packs_url})
            stickers = await self.db.get_all_stickers_in_pack(packs_url)
            resp.update({"number_of_stickers": len(stickers)})
            for sticker in stickers:
                resp["stickers"].update(
                    {
                        sticker[0]: {
                            "id": sticker[0],
                            "name": sticker[0],
                            "rating": sticker[1],
                            "link": sticker[2],
                            "api":
                                str(request.url) +
                                "/" +
                                str(sticker[0])
                        }
                    }
                )
        else:
            resp.update({"comment": "Get list of stickers packs"})
            resp.update({"packs": {}})
            packs = await self.db.get_all_packs()
            for pack in packs:
                resp["packs"].update(
                    {
                        pack[0]: {
                            "name": pack[0],
                            "rating": pack[1],
                            "link": pack[2],
                            "api":
                                str(request.url) +
                                "/" +
                                pack[2].split("/")[-1]
                        }
                    }
                )
            resp.update({
                "Number of stickers packs": len(packs)
            })
        return web.json_response(resp)

    def add_routes(self):
        """TBD."""
        self.app.router.add_static(
            '/static/',
            path=os.path.dirname(os.path.abspath(__file__)) + '/../static',
            name='static')
        self.app.router.add_route('*', '/', self.handle)
        self.app.router.add_route('*', '/good', self.async_good)
        self.app.router.add_route('*', '/bad', self.action_bad)
        self.app.router.add_route('*', '/ugly', self.action_ugly)
        self.app.router.add_route('*', '/about', self.action_about)
        self.app.router.add_route('*', '/stickers', self.stickers_api)
        self.app.router.add_route('*', '/stickers/{packs}', self.stickers_api)
        self.app.router.add_route('*',
                                  '/stickers/{packs}/{stickers}',
                                  self.stickers_api)
