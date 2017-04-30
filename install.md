```bash
sudo apt update
sudo apt upgrade -y
#
# Get machine info
#
sudo cat /proc/cpuinfo
sudo apt install mbw
  sudo mbw 128 | grep AVG
sudo hdparm -t /dev/sda1  # Disk may be vary
#
# Some usefull staff
#
sudo apt install htop mc wrk -y
#
# libs to install python pip
#
sudo apt install git make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev -y
#
# nginx
#
sudo apt install nginx -y
#
# Pyenv part
#
curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash
echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
source ~/.bashrc
# echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bash_profile
# echo 'eval "$(pyenv init -)"' >> ~/.bash_profile
# echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bash_profile
# source ~/.bash_profile
pyenv update
pyenv install 3.5.3
pyenv rehash
#
# Load our benchmark
#
git clone https://github.com/valentinmk/python-tarantool-benchmark-and-bootstrap.git
cd taran-python-benchmark/
pyenv local 3.5.3
pip install -r requerments.txt
#
# Tarantool part
#
curl http://download.tarantool.org/tarantool/1.7/gpgkey | sudo apt-key add -
release=`lsb_release -c -s`
# install https download transport for APT
sudo apt-get -y install apt-transport-https
# append two lines to a list of source repositories
sudo rm -f /etc/apt/sources.list.d/*tarantool*.list
sudo tee /etc/apt/sources.list.d/tarantool_1_7.list <<- EOF
deb http://download.tarantool.org/tarantool/1.7/ubuntu/ $release main
deb-src http://download.tarantool.org/tarantool/1.7/ubuntu/ $release main
EOF
# install
sudo apt-get update
sudo apt-get -y install tarantool
#
# Stop and remove from autostart example instance Tarantool
#
sudo tarantoolctl stop example
sudo rm /etc/tarantool/instances.enabled/example.lua
#
# Load our instance
#
sudo cp pygbu.lua /etc/tarantool/instances.available/pygbu.lua
sudo ln -s /etc/tarantool/instances.available/pygbu.lua /etc/tarantool/instances.enabled/pygbu.lua
sudo tarantoolctl start pygbu
tarantoolctl connect 'tesla:secret@*:3311'
#check that all spaces in place
# box.space
# example output
# ---
# - stickers:
#     temporary: false
#     engine: memtx
#   secret:
#     temporary: false
#     engine: memtx
#   sessions:
#     temporary: false
#     engine: memtx
#   packs:
#     temporary: false
#     engine: memtx
#   server:
#     temporary: false
#    engine: memtx
# ...
#
# Postgres
#
sudo add-apt-repository "deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main"
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update
sudo apt install postgresql postgresql-contrib # by default it must select and install 9.6 version
# otherwise use postgresql-9.6 postgresql-contrib-9.6
sudo -u postgres createuser --interactive
# user name tesla
# superuser Y
sudo -u postgres psql
postgres=# \password tesla
# provide password 'secret'
postgres=# \q
#test
psql -U tesla -d postgres -h 127.0.0.1 -W
sudo -u postgres createdb python_benchmark
psql -U tesla -h 127.0.0.1 -d postgres -f python_benchmark.backup
# DB done
# load data from Tarantool to Postgres
python tests/pgtotarantool.py
```

TODO simple service to load all stickers and packs
