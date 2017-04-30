from aiohttp import web
import jinja2
import aiohttp_jinja2
import aiohttp_session


class AiohttpHelper:
    """Helper class that do all aiohttp start stop manipulation
    """
    port = 8080  # Default port
    loop = None  # By default loop is not set

    def __init__(self, loop, port):
        self.loop = loop
        self.port = port

    async def handle(self, request):
        """Simple handler that answer http request get with port and name."""
        name = request.match_info.get('name', "Anonymous")
        text = 'Aiohttp server running on {0} port. Hello, {1}'.format(
            str(self.port), str(name))
        return web.Response(text=text)

    def add_routes(self):
        self.app.router.add_route('*', '/', self.handle)
        self.app.router.add_route('*', '/{name}', self.handle)

    async def start(self):
        """Start aiohttp web server."""

        self.app = web.Application()

        aiohttp_jinja2.setup(
            self.app,
            loader=jinja2.PackageLoader('aiohttp_server', 'templates'),
            # enable_async=False,
            auto_reload=False)
        aiohttp_session.setup(self.app, aiohttp_session.SimpleCookieStorage())
        self.add_routes()
        self.handler = self.app.make_handler()
        self.f = self.loop.create_server(self.handler,
                                         host='0.0.0.0',
                                         port=self.port)
        # Event loop is already running, so we await create server instead
        # of run_until_complete
        self.srv = await self.f

    async def stop(self):
        """Stop aiohttp server."""
        self.srv.close()
        await self.srv.wait_closed()
        await self.app.shutdown()
        await self.handler.shutdown(60.0)
        await self.app.cleanup()
