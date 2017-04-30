import asyncio
from japronto import Application
# from sanic.response import html
# from sanic_compress import Compress
# from sanic_session import InMemorySessionInterface


class JaprontoHelper:
    """Helper class that do all sanic start stop manipulation
    """
    port = 8080  # Default port
    loop = None  # By default loop is not set

    def __init__(self, loop=None, port=None):
        self.loop = loop
        self.port = port

    async def handle(request):
        """Simple handler that answer http request get with port and name."""
        text = 'Japronto server running on {0} port. Hello, {1}'.format(
            str('??????'), str(request.match_dict['name']))
        return request.Response(text=text)

    async def handle_index(request):
        """Simple handler that answer http request get with port and name."""
        text = 'Sanic server running on {0} port.'.format(str('??????'))
        text2 = '\nLoop is {}'.format(str(asyncio.get_event_loop()))
        return request.Response(text=text+text2)

    def add_routes(self):
        # self.app.router.add_route('*', '/', self.handle)
        # self.app.router.add_route('*', '/{name}', self.handle)

        self.app.router.add_route('/', self.handle_index)
        self.app.router.add_route('/{name}', self.handle)
        print("add routes: \n {0}".format(self.app.router))

    # @app.middleware('request')
    # async def add_session_to_request(self, request):
        # before each request initialize a session
        # using the client's request
    #    await self.session_interface.open(request)

    # @self.app.middleware('response')
    # async def save_session(self, request, response):
        # after each request save the session,
        # pass the response to set client cookies
    #    await self.session_interface.save(request, response)

    def start(self):
        """Start japronto web server."""

        self.app = Application()
        self.app._loop = self.loop
        self.add_routes()
        self.app.run(port=int(self.port),
                     worker_num=None,
                     reload=False,
                     debug=False)
        # GZip support
        # Compress(self.app)
        # self.app.config['COMPRESS_MIMETYPES'] = {'text/html',
        #                                         'application/json'}
        # self.app.config['COMPRESS_LEVEL'] = 4
        # self.app.config['COMPRESS_MIN_SIZE'] = 300
        # Session support
        # self.session_interface = InMemorySessionInterface()
        # self.app.response_middleware.appendleft(self.save_session)
        # self.app.request_middleware.append(self.add_session_to_request)

        # self.add_routes()
        # return await self.app.create_server(loop=self.loop,
        #                                     host='0.0.0.0',
        #                                     port=self.port,
        #                                     debug=False)

    async def stop(self):
        """Stop sanic server."""
        print('Sanic stop.')
