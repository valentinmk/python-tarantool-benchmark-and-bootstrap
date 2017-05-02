"""TBD."""
import asyncio
import logging
import os
import traceback
from http.cookies import SimpleCookie
from mimetypes import guess_type
from jinja2 import PackageLoader, Environment
from .helper import loop, port, app
from .helper import init as japronto_helper_init
from .helper import start as japronto_helper_start
from japronto.request import cookies


MIN_VOTES = 20                  # Number of votes to show the ugly
UPDATE_PLUS = 1                 # Increment for positive update
UPDATE_MINUS = -1               # Increment for negative update
NO_UPDATE = 0
HIDDEN = '/img/Question.svg'    # Picture for hidden element
db = None
jinja = Environment(loader=PackageLoader('japronto_server', 'templates'),
                    # enable_async=False,
                    auto_reload=False)

helper_app = app
helper_loop = loop
helper_port = port
statistics = {
    "packs_count": "empty",
    "stickers_count": "empty",
    "clicks": "empty",
    "votes": "empty",
    "users": "empty"}


def init(loop_param=None, port_param=None, db_driver=None):
    """TBD."""
    global db
    db = db_driver
    japronto_helper_init(loop_param=loop_param, port_param=port_param)


async def listner_for_statistics():
    global statistics
    global db
    statistics = await db.get_statistics()
    await asyncio.sleep(5)
    await listner_for_statistics()


async def async_good(request):
    """Good page handler."""
    global db
    global jinja
    data = {
        "title": "Top of the best stikers for Telegram",
        "active_good": "class=\"active\"",
        "active_bad": "",
        "top": {}
    }
    session = await session_handler(request=request)
    cookies_for_responce = SimpleCookie()
    cookies_for_responce['new'] = session['new']
    cookies_for_responce['stickers'] = session['stickers']
    data["top"] = await db.get_top(12, 'ITERATOR_LE')
    text = jinja.get_template('good.html').render(
        title=data["title"],
        active_good=data["active_good"],
        active_bad=data["active_bad"],
        top=data["top"]
    )
    return request.Response(
        text=text,
        mime_type='text/html',
        cookies=cookies_for_responce)


async def action_bad(request):
    """Bad page handler."""
    global db
    global jinja
    data = {
        "title": "Top of bad stikers for Telegram",
        "active_good": "",
        "active_bad": "class=\"active\"",
        "top": {}
    }
    session = await session_handler(request=request)
    cookies_for_responce = SimpleCookie()
    cookies_for_responce['new'] = session['new']
    cookies_for_responce['stickers'] = session['stickers']
    data["top"] = await db.get_top(9, 'ITERATOR_GE')
    text = jinja.get_template('good.html').render(
        title=data["title"],
        active_good=data["active_good"],
        active_bad=data["active_bad"],
        top=data["top"]
    )
    return request.Response(
        text=text,
        mime_type='text/html',
        cookies=cookies_for_responce)


async def action_ugly(request):
    """TBD."""
    return request.Response(text="UGLY")


async def action_about(request):
    """About page handler."""
    global jinja
    global statistics
    data = {"title": "About and statistics"}
    data.update(statistics)
    text = jinja.get_template('about.html').render(
        title=data['title'],
        packs_count=data['packs_count'],
        stickers_count=data['stickers_count'],
        clicks=data['clicks'],
        votes=data['votes'],
        users=data['users']
    )
    return request.Response(
        text=text,
        mime_type='text/html'
    )


async def handle(request):
    """Index page handler."""
    global db
    global jinja
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
    session = await session_handler(request=request)
    cookies_for_responce = SimpleCookie()
    cookies_for_responce['new'] = session['new']
    cookies_for_responce['stickers'] = session['stickers']
    if request.form:
        if request.form['vote_plus'] and request.form['vote_minus']:
            logging.debug("{} {}".format(
                str(request.form['vote_plus']),
                str(request.form['vote_minus'])
            ))
            await db.do_post(
                request.form['vote_plus'],
                request.form['vote_minus'],
                UPDATE_PLUS,
                UPDATE_MINUS,
                NO_UPDATE)

    data["random_image"]["left"]["url"], \
        data["random_image"]["left"]["token_plus"] \
        = await db.create_random_vote()
    data["random_image"]["right"]["url"], \
        data["random_image"]["right"]["token_plus"] \
        = await db.create_random_vote()
    data["random_image"]["right"]["token_minus"] \
        = data["random_image"]["right"]["token_plus"]
    data["random_image"]["left"]["token_minus"] \
        = data["random_image"]["left"]["token_plus"]
    await db.update_stats(0, UPDATE_PLUS, NO_UPDATE)
    text = jinja.get_template('index.html').render(
        title=data["title"],
        random_image=data["random_image"],
    )
    return request.Response(
        text=text,
        mime_type='text/html',
        cookies=cookies_for_responce)


# API to stickers data

async def stickers_api(request):
    """TBD."""
    global db
    resp = {"packs": None,
            "stickers": None
            }
    resp["packs"] = request.match_dict.get("packs",
                                           "Empty in request")
    resp["stickers"] = request.match_dict.get("stickers",
                                              "Empty in request")

    if resp["stickers"] != "Empty in request":
        resp.update({"comment": "Get sticker info"})
        resp.update({"name": resp["stickers"]})
        sticker = await db.get_stickers_by_name(resp["stickers"])
        if not sticker:
            return request.Response(code=404)
        resp.update({"url": sticker[0][2]})
        resp.update({"id": sticker[0][0]})
        resp.update({"rating": sticker[0][1]})
        resp.update({"pack_url": sticker[0][3]})
    elif resp["packs"] != "Empty in request":
        resp.update({"comment": "Get pack info"})
        resp.update({"stickers": {}})
        packs_url = "https://tlgrm.eu/stickers/" + resp["packs"]
        resp.update({"url": packs_url})
        stickers = await db.get_all_stickers_in_pack(packs_url)
        number_of_stickers = len(stickers)
        if not number_of_stickers:
            return request.Response(code=404)
        resp.update({"number_of_stickers": number_of_stickers})
        for sticker in stickers:
            resp["stickers"].update(
                {
                    sticker[0]: {
                        "id": sticker[0],
                        "name": sticker[0],
                        "rating": sticker[1],
                        "link": sticker[2],
                        "api":
                            # Not working on 80 port until
                            # https://github.com/squeaky-pl/japronto/issues/69
                            # have been fixed.
                            # You have to using your custom port.
                            "http://" +
                            request.hostname + ":" + str(request.port) +
                            request.path +
                            "/" +
                            str(sticker[0])
                    }
                }
            )
    else:
        resp.update({"comment": "Get list of stickers packs"})
        resp.update({"packs": {}})
        packs = await db.get_all_packs()
        for pack in packs:
            resp["packs"].update(
                {
                    pack[0]: {
                        "name": pack[0],
                        "rating": pack[1],
                        "link": pack[2],
                        "api":
                            # Not working on 80 port until
                            # https://github.com/squeaky-pl/japronto/issues/69
                            # have been fixed.
                            # You have to using your custom port.
                            "http://" +
                            request.hostname + ":" + str(request.port) +
                            request.path +
                            "/" +
                            pack[2].split("/")[-1]
                    }
                }
            )
        resp.update({
            "Number of stickers packs": len(packs)
        })
    return request.Response(json=resp)


def add_routes():
    """TBD."""
    from .helper import app
    app.router.add_route('/', handle, methods=['GET', 'POST'])
    app.router.add_route('/good', async_good)
    app.router.add_route('/bad', action_bad)
    app.router.add_route('/ugly', action_ugly)
    app.router.add_route('/about', action_about)
    app.router.add_route('/stickers', stickers_api)
    app.router.add_route('/stickers/{packs}', stickers_api)
    app.router.add_route('/stickers/{packs}/{stickers}', stickers_api)


def start():
    """TBD."""
    add_routes()
    add_static(path='static/')
    japronto_helper_start(add_default_route=False)


async def session_handler(request):
    """TBD."""
    global db
    session = cookies(request)
    if request.remote_addr is not None:
        host = request.remote_addr
        remote_addr = host
    else:
        remote_addr = None
    try:
        user_agent = request.headers.items()['User-Agent']
    except:
        user_agent = 'Not detected'
    if 'new' not in session:
        new_cookie = await db.update_user(
            None,
            remote_addr,
            user_agent)
        session['new'] = 'False'
    else:
        new_cookie = await db.update_user(
            session.get('stickers'),
            remote_addr,
            user_agent)
        session['new'] = 'False'
    session['stickers'] = new_cookie
    return session


def add_static(path=None):
    """TBD."""
    global static_files
    if not path:
        raise "path is empty"

    if os.path.isfile(path):
        raise "path is file, please, provide directory"

    static_files_names = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        static_files_names.extend(filenames)
    static_files = {}
    for filename in static_files_names:
        static_files.update(
            {filename: {}})
        static_files[filename].update(
            {'path': path + filename})
        static_files[filename].update(
            {'mime_type': guess_type(path + filename)})
        static_files[filename].update(
            {'file_size': os.stat(path + filename).st_size})
    from .helper import app
    app.router.add_route('/static/{file}', static, methods=['GET', 'HEAD'])


def static(request):
    """TBD."""
    global static_files
    try:
        f = open(
            static_files[request.match_dict['file']]['path'],
            mode='r')
        text = f.read()
        # with open(static_files[request.match_dict['file']]['path']) as f:
        #     text = f.read()
        return request.Response(
            text=text,
            mime_type=static_files[request.match_dict['file']]['mime_type'][0]
        )
    except:
        logging.error(traceback.format_exc())
        return request.Response(code=404)
