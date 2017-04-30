"""TBD."""
import asyncio
import logging
import os
import sys
from .helper import SanicHelper
from sanic.response import html, json
from sanic_jinja2 import SanicJinja2
from urllib import parse


class SanicTarantoolOne (SanicHelper):
    """TBD."""

    MIN_VOTES = 20                  # Number of votes to show the ugly
    UPDATE_PLUS = 1                 # Increment for positive update
    UPDATE_MINUS = -1               # Increment for negative update
    NO_UPDATE = 0
    HIDDEN = '/img/Question.svg'    # Picture for hidden element

    def __init__(self, loop=None, port=None, db=None):
        super().__init__(loop=loop, port=port)
        self.db = db
        self.statistics = {
            "packs_count": "empty",
            "stickers_count": "empty",
            "clicks": "empty",
            "votes": "empty",
            "users": "empty"}

    async def listner_for_statistics(self):
        self.statistics = await self.db.get_statistics()
        await asyncio.sleep(5)
        await self.listner_for_statistics()

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
        return self.jinja.render('good.html', request,
                                 title=data['title'],
                                 active_good=data['active_good'],
                                 active_bad=data['active_bad'],
                                 top=data['top'],
                                 )

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
        return self.jinja.render('bad.html', request,
                                 title=data['title'],
                                 active_good=data['active_good'],
                                 active_bad=data['active_bad'],
                                 top=data['top'],
                                 )

    async def action_ugly(self, request):
        """TBD."""
        return html("UGLY")

    async def action_about(self, request):
        """TBD."""
        data = {"title": "About and statistics"}
        data.update(self.statistics)
        return self.jinja.render('about.html', request,
                                 title=data['title'],
                                 packs_count=data['packs_count'],
                                 stickers_count=data['stickers_count'],
                                 clicks=data['clicks'],
                                 votes=data['votes'],
                                 users=data['users'])

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
        if len(request.body) > 0:
            if request.form['vote_plus'] and request.form['vote_minus']:
                logging.debug("{} {}".format(
                    str(request.form['vote_plus']),
                    str(request.form['vote_minus'])
                ))
                await self.db.do_post(
                    request.form['vote_plus'],
                    request.form['vote_minus'],
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
        return self.jinja.render('index.html',
                                 request,
                                 super='hot',
                                 title=data['title'],
                                 random_image=data['random_image'],
                                 )

    async def session_handler(self, request):
        session = request['session']
        if request.transport.get_extra_info('peername') is not None:
            host, port = request.transport.get_extra_info('peername')
            remote_addr = host
        else:
            remote_addr = None
        try:
            user_agent = request.headers['User-Agent']
        except:
            user_agent = 'Not detected'
        if session.get('new') is None:
            new_cookie = await self.db.update_user(
                None,
                remote_addr,
                user_agent)
            session['new'] = 'False'
        else:
            new_cookie = await self.db.update_user(
                session.get('stickers'),
                remote_addr,
                user_agent)
        session['stickers'] = new_cookie
        return session

    # API to stickers data

    async def stickers_api(self, request):
        """TBD."""
        resp = {"packs": None,
                "stickers": None}
        resp["packs"] = "Empty in request"
        resp["stickers"] = "Empty in request"
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
        return json(resp)

    async def stickers_api_packs(self, request, packs):
        """TBD."""
        #packs = parse.unquote(packs)
        resp = {"packs": None,
                "stickers": None}
        resp["packs"] = packs
        resp["stickers"] = "Empty in request"
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
        return json(resp)

    async def stickers_api_packs_stickers(self, request, packs, stickers):
        #packs = parse.unquote(packs)
        #stickers = parse.unquote(stickers)
        resp = {"packs": None,
                "stickers": None}
        resp["packs"] = packs
        resp["stickers"] = stickers
        resp.update({"comment": "Get sticker info"})
        resp.update({"name": resp["stickers"]})
        print(resp["stickers"])
        sticker = await self.db.get_stickers_by_name(resp["stickers"])
        print(sticker)
        resp.update({"url": sticker[0][2]})
        resp.update({"id": sticker[0][0]})
        resp.update({"rating": sticker[0][1]})
        resp.update({"pack_url": sticker[0][3]})
        return json(resp)

    def add_routes(self):
        """TBD."""
        self.jinja = SanicJinja2(self.app,
                                 # enable_async=False,
                                 auto_reload=False)
        self.app.static(
            '/static',
            os.path.dirname(
                os.path.abspath(sys.modules['__main__'].__file__))+'/static')
        self.app.add_route(self.handle, '/', methods=['GET', 'POST'])
        self.app.add_route(self.async_good, '/good', )
        self.app.add_route(self.action_bad, '/bad', )
        self.app.add_route(self.action_ugly, '/ugly', )
        self.app.add_route(self.action_about, '/about', )
        self.app.add_route(self.stickers_api, '/stickers')
        self.app.add_route(self.stickers_api_packs, '/stickers/<packs>')
        self.app.add_route(
            self.stickers_api_packs_stickers, '/stickers/<packs>/<stickers>')
