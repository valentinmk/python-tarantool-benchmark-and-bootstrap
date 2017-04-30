from sanic import Sanic
from sanic.response import html
# from sanic_compress import Compress
from sanic_session import InMemorySessionInterface


class SanicHelper:
    """Helper class that do all sanic start stop manipulation
    """
    port = 8080  # Default port
    loop = None  # By default loop is not set

    def __init__(self, loop=None, port=None):
        self.loop = loop
        self.port = port

    async def handle(self, request, name):
        """Simple handler that answer http request get with port and name."""
        text = 'Sanic server running on {0} port. Hello, {1}'.format(
            str(self.port), str(name))
        return html(text)

    async def handle_index(self, request):
        """Simple handler that answer http request get with port and name."""
        text = 'Sanic server running on {0} port.'.format(str(self.port))
        return html(text)

    def add_routes(self):
        # self.app.router.add_route('*', '/', self.handle)
        # self.app.router.add_route('*', '/{name}', self.handle)
        self.app.add_route(self.handle_index, '/')
        self.app.add_route(self.handle, '/<name>')

    # @app.middleware('request')
    async def add_session_to_request(self, request):
        # before each request initialize a session
        # using the client's request
        await self.session_interface.open(request)

    # @self.app.middleware('response')
    async def save_session(self, request, response):
        # after each request save the session,
        # pass the response to set client cookies
        await self.session_interface.save(request, response)

    async def start(self):
        """Start sanic web server."""

        self.app = Sanic('sanic_server')

        # GZip support
        # Compress(self.app)
        # self.app.config['COMPRESS_MIMETYPES'] = {'text/html',
        #                                          'application/json'}
        # self.app.config['COMPRESS_LEVEL'] = 4
        # self.app.config['COMPRESS_MIN_SIZE'] = 300
        # Session support
        self.session_interface = InMemorySessionInterface()
        self.app.response_middleware.appendleft(self.save_session)
        self.app.request_middleware.append(self.add_session_to_request)

        self.add_routes()
        return await self.app.create_server(loop=self.loop,
                                            host='0.0.0.0',
                                            port=self.port,
                                            debug=False)

    async def stop(self):
        """Stop sanic server."""
        print('Sanic stop.')
