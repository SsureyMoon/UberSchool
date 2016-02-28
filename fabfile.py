from StringIO import StringIO
from fabric.api import cd, local, env, run
from fabric.colors import green
from fabric.context_managers import lcd, settings, shell_env, prefix
from fabric.contrib import files
from fabric.decorators import task
from fabric.operations import prompt, os, sudo
import fabtools
from fabtools.python import virtualenv
import sys
from fabtools.shorewall import Ping, SSH, HTTP, HTTPS, SMTP

postgres_dir = "/usr/local/var/postgres"
postgres_log = "/usr/local/var/postgres/server.log"

backend_dir = "./backend/"


def run_db_on_mac():
    local("pg_ctl -D {} -l {} start".format(postgres_dir, postgres_log), capture=False)

@task
def launch():
    env.server_name = 'uber_school'
    env.hosts = ['54.191.42.133', ]
    env.user = 'ubuntu'
    env.git_branch = 'master'
    env.project_user = 'ubuntu'
    env.db_user = 'postgres'
    env.db_password = 'postgres'
    env.key_filename = "/Users/ssureymoon/Documents/workspace/lauch2016/{}".format("launch2016_key.pem")

@task
def setup_postgres():

    www = "/home/{user}/www/".format(user=env.project_user)
    venv = www+'venv'
    git_dir = www+'uber_school/'

    with settings(shell="/bin/bash -c"):
        if not fabtools.postgres.user_exists(env.db_user):
            fabtools.require.postgres.user(env.db_user, env.db_password)
        if not fabtools.postgres.database_exists(env.server_name):
            fabtools.require.postgres.database(env.server_name, env.db_user)
    sudo('psql -c "CREATE EXTENSION postgis;"', user='postgres')

@task
def install_packages():
    www = "/home/{user}/www/".format(user=env.project_user)
    venv = www+'venv'
    git_dir = www+'uber_school/'

    git_repo = "https://github.com/SsureyMoon/UberSchool.git"

    if not files.exists(www):
        run("mkdir -p " + www)
    # sudo('apt-get update')
    # sudo('apt-get upgrade')
    # sudo('apt-get install build-essential')


    fabtools.require.nginx.server()
    fabtools.require.deb.packages([
        "postgresql-9.3", "postgresql-9.3-postgis-2.1", "postgresql-server-dev-9.3", "python-psycopg2",
        "libncurses5-dev", "libffi-dev",
        "libxml2-dev", "libxslt-dev", "libxslt1-dev", "libpq-dev", "python-lxml", "git",
    ])
    fabtools.require.python.virtualenv(venv)
    with virtualenv(venv):
        if not fabtools.python.is_pip_installed():
            fabtools.python.install_pip()

    if not files.exists(git_dir):
        fabtools.git.clone(git_repo, path=git_dir)
    else:
        with cd(git_dir):
            fabtools.git.checkout('.')
            run('git fetch origin')
            if env.git_branch != 'master':
                run('git checkout {}'.format(env.git_branch))
                run('git pull origin {}'.format(env.git_branch))


@task
def update_project():
    www = "/home/{user}/www/".format(user=env.project_user)
    venv = www+'venv'
    git_dir = www+'uber_school/'

    git_repo = "https://github.com/SsureyMoon/UberSchool.git"

    if not files.exists(www):
        run("mkdir -p " + www)
    # sudo('apt-get update')
    # sudo('apt-get upgrade')
    # sudo('apt-get install build-essential')

    if not files.exists(git_dir):
        fabtools.git.clone(git_repo, path=git_dir)
    else:
        with cd(git_dir):
            fabtools.git.checkout('.')
            run('git fetch origin')
            if env.git_branch != 'master':
                run('git checkout {}'.format(env.git_branch))
                run('git pull origin {}'.format(env.git_branch))


@task
def install_dependencies():
    www = "/home/{user}/www/".format(user=env.project_user)
    venv = www+'venv'
    git_dir = www+'uber_school/'

    with cd(git_dir), virtualenv(venv):
       fabtools.python.install_requirements('{git_dir}backend/requirements.txt'.format(git_dir=git_dir))