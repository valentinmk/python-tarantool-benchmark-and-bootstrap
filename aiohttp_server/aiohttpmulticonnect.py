"""TBD."""
import aiohttp_jinja2
import logging
import os
from aiohttp import web
from aiohttp_session import get_session
from .helper import AiohttpHelper


class AiohttpTarantoolMulti (AiohttpHelper):
    """TBD."""

    MIN_VOTES = 20                  # Number of votes to show the ugly
    UPDATE_PLUS = 1                 # Increment for positive update
    UPDATE_MINUS = -1               # Increment for negative update
    NO_UPDATE = 0
    HIDDEN = '/img/Question.svg'    # Picture for hidden element

    def __init__(self, loop=None, port=None, db=None):
        """Init AiohttpTarantoolOne with loop, port and db."""
        super().__init__(loop=loop, port=port)
        self.db = db

    @aiohttp_jinja2.template('good.html')
    async def async_good(self, request):
        """TBD."""
        data = {'super': 'hot'}
        await self.session_handler(request=request)
        data['active_good'] = 'class="active"'
        data['active_bad'] = ''
        data['active_ugly'] = ''
        data['active_about'] = ''
        data['title'] = 'Top of the best stikers for Telegram'
        try:
            taran = self.db()
            top = await taran.get_top(10, 'ITERATOR_LE')
            data['top'] = top
        except:
            data['top'] = [[0, 'Nan', self.HIDDEN, 3]] * 10
        finally:
            await taran.close()
        return data

    @aiohttp_jinja2.template('bad.html')
    async def action_bad(self, request):
        """TBD."""
        data = {'super': 'hot'}
        await self.session_handler(request=request)
        data['active_good'] = ''
        data['active_bad'] = 'class="active"'
        data['active_ugly'] = ''
        data['active_about'] = ''
        data['title'] = 'Top of the bad stikers for Telegram'
        try:
            taran = self.db()
            top = await taran.get_top(10, 'ITERATOR_LE')
            data['top'] = top
        except:
            data['top'] = [[0, 'Nan', self.HIDDEN, 3]] * 10
        finally:
            await taran.close()
        return data

    async def action_ugly(self, request):
        """TBD."""
        return web.Response(text="UGLY")

    @aiohttp_jinja2.template('about.html')
    async def action_about(self, request):
        """TBD."""
        return {}

    @aiohttp_jinja2.template('index.html')
    async def handle(self, request):
        """TBD."""
        try:
            taran = self.db()
        except:
            await taran.close()
        data = {'super': 'hot'}
        await self.session_handler(request=request)
        await request.post()
        post = await request.post()
        if len(post) > 0:
            if post['vote_plus'] and post['vote_minus']:
                logging.debug("{} {}".format(
                    str(post['vote_plus']),
                    str(post['vote_minus'])
                ))
                await taran.do_post(post['vote_plus'],
                                    post['vote_minus'],
                                    self.UPDATE_PLUS,
                                    self.UPDATE_MINUS,
                                    self.NO_UPDATE)
        left, right = {}, {}
        left['url'], left['token_plus'] = await taran.create_random_vote()
        right['url'], right['token_plus'] = await taran.create_random_vote()
        # right['token_minus'] = left['token_plus']
        # left['token_minus'] = right['token_plus']
        right['token_minus'] = right['token_plus']
        left['token_minus'] = left['token_plus']
        data['random_image'] = {'left': left,
                                'right': right}
        await taran.update_stats(self.UPDATE_PLUS, self.NO_UPDATE)
        await taran.close()
        data['title'] = 'Good and Bad Telegram stickers'
        return data

    async def session_handler(self, request):
        """Handle sessions for request."""
        try:
            taran = self.db()
        except:
            await taran.close()
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
            new_cookie = await taran.update_user(
                None,
                remote_addr,
                user_agent)
        else:
            new_cookie = await taran.update_user(
                session['stickers'],
                remote_addr,
                user_agent)
        session['stickers'] = new_cookie
        await taran.close()
        return session

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
