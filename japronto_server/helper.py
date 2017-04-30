import asyncio
from japronto import Application
# from sanic.response import html
# from sanic_compress import Compress
# from sanic_session import InMemorySessionInterface

port = 8080     # Default port
loop = None     # By default loop is not set
app = None      # global for Japronto app


def init(loop_param=None, port_param=None):
    """Init Janpronto server in like-oop style."""
    global loop, port, app
    loop = loop_param
    port = port_param
    app = Application()


async def handle(request):
    global loop, port, app
    """Simple handler that answer http request get with port and name."""
    text = 'Japronto server running on {0} port. Hello, {1}'.format(
        str(port), str(request.match_dict['name']))
    return request.Response(text=text)


def handle_index(request):
    global loop, port, app
    """Simple handler that answer http request get with port and name."""
    text = 'Sanic server running on {0} port.'.format(str(port))
    text2 = '\nLoop is {}'.format(str(asyncio.get_event_loop()))
    return request.Response(text=text+text2)


def add_routes():
    global loop, port, app
    # self.app.router.add_route('*', '/', self.handle)
    # self.app.router.add_route('*', '/{name}', self.handle)

    app.router.add_route('/', handle_index)
    app.router.add_route('/{name}', handle)
    print("add routes: \n {0}".format(app.router))

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


def start(add_default_route=True):
    """Start japronto web server."""
    global loop, port, app
    print("port = {}".format(port))
    app._loop = loop
    if add_default_route:
        add_routes()
    app.run(port=int(port),
            worker_num=None,
            reload=False,
            debug=False)
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
