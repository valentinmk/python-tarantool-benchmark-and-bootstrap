# Python and Tarantool Benchmark and Bootstrap

This is demo project for my article on [GitBook](https://valentinmk.gitbooks.io/python-tarantool-benchmark/) and [Medium](https://medium.com/@valentinmk/python-and-tarantool-races-in-the-loop-f496b6467ea4).

## Live demo
* [stickers.teslarnd.ru](http://stickers.teslarnd.ru) hosted on AWS.

## Purpose
* The main goal of the project was benchmark Tarantool and Python async web servers performance.
* Minor task was to show how you could write solution with Tarantool and aiohttp, sanic and japronto libraries.

## Installation
You can install the project on your own server by reproducing bash commands described in [install.md](https://github.com/valentinmk/python-tarantool-benchmark-and-bootstrap/blob/master/install.md).

Main steps to setup project is:
* install Python (pyenv used)
* install Python libs (`requerments.txt`)
* install Tarantool
* configure Tarantool (`pygbu.lua` configuration script provided)
* get some stickers' data into you Tarantool (`tests/externalapitotarantool.py`) from API hosted at [stickers.teslarnd.ru/stickers](http://stickers.teslarnd.ru/stickers)
* (optional) install PostgreSQL
* (optional) configure PostgreSQL
* (optional) migrate data from Tarantool to PostgreSQL (`tests/pgtotarantool.py`)

## This is not
* good example of programming style (everything could be code better)
* only one possible way to solve problem, read code comments (there are hints how to make code better)
* well-tested software (there are known errors and issues)

## How it works
Our web site consists of 5 sections.

* `Index` is making the votes and shows 2 images for us to choose one.
We have 9 requests to Tarantool for index page:
  * 2 selects for getting a random picture (2 select, 1 insert for each):
    * select from Tarantool random number (call build in function)
    * select from Tarantool token (eval md5 calculation for previously selected number)
    * insert token in space `secret`
  * create and insert uuid for user session (1 select, 1 upsert):
    * select from Tarantool uuid for session (eval uuid calculation)
    * upsert user information with uuid in `session` space
  * update server statistics (1 update)
* `Good` section showing 9 top rated stickers. We have 3 requests for `Good` page:
  * select top 9 stickers from 16k records (table) space it Tarantool (it like
    `select top(9) from stickers order by rating ASC`)
  * create and insert uuid for user session (1 select, 1 upsert):
    * select from Tarantool uuid for session (eval uuid calculation)
    * upsert user information with uuid in `session` space
* `Bad` section showing us 9 worst rated stickers. `Bad` runs the same as `Good` section. 3 requests in total.
* `Ugly` section writes text "Ugly", there’re no calculations here. So we can benchmark how fast the web server is.
* `About` section renders the template, pastes Title and generates HTML response.

We have stickers api at `http://hostname:port/stickers`.

## License MIT
Project License can be found [here](https://github.com/valentinmk/python-tarantool-benchmark-and-bootstrap/blob/master/LICENSE).
