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
    env.hosts = ['52.36.222.205', ]
    env.user = 'ubuntu'
    env.git_branch = 'master'
    env.project_user = 'ubuntu'
    env.db_user = 'ubuntu'
    env.db_password = 'ubuntu'
    env.key_filename = "/home/ubuntu/mike/etc/{}".format("pison.pem")


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
    sudo('psql -c "ALTER ROLE ubuntu SUPERUSER;"', user='postgres')

@task
def install_packages():
    www = "/home/{user}/www/".format(user=env.project_user)
    venv = www+'venv'
    git_dir = www+'uber_school/'

    git_repo = "https://github.com/SsureyMoon/UberSchool.git"

    if not files.exists(www):
        run("mkdir -p " + www)
    sudo('apt-get -y update')
    sudo('apt-get -y upgrade')
    sudo('apt-get -y install build-essential')


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
            # run('git fetch origin')
            if env.git_branch != 'master':
                run('git checkout {}'.format(env.git_branch))
                run('git pull origin {}'.format(env.git_branch))

    front_end = git_dir + 'app_client/'
    if not fabtools.nodejs.version():
        fabtools.nodejs.install_from_source()

    with cd(front_end):
        run('ls')
        run('ls node_modules')
        fabtools.nodejs.install_dependencies()


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
            run('git pull origin {}'.format(env.git_branch))


@task
def install_dependencies():
    www = "/home/{user}/www/".format(user=env.project_user)
    venv = www+'venv'
    git_dir = www+'uber_school/'

    with cd(git_dir), virtualenv(venv):
       fabtools.python.install_requirements('{git_dir}backend/requirements.txt'.format(git_dir=git_dir))

@task
def setup_nginx():
    www = "/home/{user}/www/".format(user=env.project_user)
    config_file = www+'uber_school/nginx/lauch.conf'
    sudo('cp {original} /etc/nginx/sites-available/{target}'\
        .format(original=config_file, target='oddschool.online'))

    if files.exists('/etc/nginx/sites-enabled/{target}'\
        .format(target='oddschool.online')):
        sudo('unlink /etc/nginx/sites-enabled/{target}'\
            .format(target='oddschool.online'))
    sudo('ln -s /etc/nginx/sites-available/{target} /etc/nginx/sites-enabled/{target}'\
        .format(target='oddschool.online'))

    if files.exists('/etc/nginx/sites-enabled/default'):
        sudo('unlink /etc/nginx/sites-enabled/default')


    log_dir = '/etc/nginx/log/'
    if not files.exists(log_dir):
        sudo('mkdir -p ' + log_dir)
        sudo('touch {}local-odds.access.log'.format(log_dir))
        sudo('touch {}local-odds.error.log'.format(log_dir))

    if fabtools.service.is_running('nginx'):
        fabtools.service.restart('nginx')
    else:
        fabtools.service.start('nginx')

@task
def migrate(**kwargs):
    # setup_postgres()

    www = "/home/{user}/www/".format(user=env.project_user)
    venv = www+'venv'
    git_dir = www+'uber_school/'
    # fabtools.python.install_requirements('{git_dir}requirements/{env}.txt'.format(git_dir=git_dir, env=env.git_branch))

    with cd(git_dir+'backend/'), virtualenv(venv):
        #install_dependencies()
        # DJANGO_SETTINGS_MODULE, SECRET_KEY, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, DB_USER, DB_PASSWORD
        with shell_env(**kwargs):
            #run("pip install ")
            run('python manage.py makemigrations')
            run('python manage.py migrate auth')
            run('python manage.py migrate')
            # run('python manage.py migrate')

@task
def run_supervisor(**kwargs):
    www = "/home/{user}/www/".format(user=env.project_user)
    venv = www+'venv'
    git_dir = www+'uber_school/'
    backend_dir = git_dir+'backend/'
    log_dir = git_dir + 'logs/'
    python_vbin = venv + '/bin/gunicorn'
    with settings(user=env.project_user):
        if not files.exists(log_dir):
            run('mkdir -p ' + log_dir)
            run('touch {}django_stdout.log'.format(log_dir))
            run('touch {}django_stderr.log'.format(log_dir))

        # "environment=DJANGO_SETTINGS_MODULE=%(ENV_DJANGO_SETTINGS_MODULE)s,SECRET_KEY=%(ENV_SECRET_KEY)s,DB_USER=%(ENV_DB_USER)s,DB_PASSWORD=%(ENV_DB_PASSWORD)s,AWS_ACCESS_KEY_ID=%(ENV_AWS_ACCESS_KEY_ID)s,AWS_SECRET_ACCESS_KEY=%(ENV_AWS_SECRET_ACCESS_KEY)s " +
        with cd(backend_dir), virtualenv(venv):
            concat = ",".join([key+"=\""+kwargs[key]+"\"" for key in kwargs])
            print concat
            print log_dir + 'django_stdout.log'
            #with prefix(concat):
            with shell_env(**kwargs):
                fabtools.require.supervisor.process('django',
                    environment=concat,#"DJANGO_SETTINGS_MODULE=%(ENV_DJANGO_SETTINGS_MODULE)s,SECRET_KEY=%(ENV_SECRET_KEY)s,DB_USER=%(ENV_DB_USER)s,DB_PASSWORD=%(ENV_DB_PASSWORD)s,AWS_ACCESS_KEY_ID=%(ENV_AWS_ACCESS_KEY_ID)s,AWS_SECRET_ACCESS_KEY=%(ENV_AWS_SECRET_ACCESS_KEY)s",
                    command=python_vbin + ' backend.wsgi:application -w 1 -b 127.0.0.1:8000 -t 300 --max-requests=100',
                    directory=backend_dir,
                    user=env.project_user,
                    stdout_logfile=log_dir + 'django_stdout.log',
                    stderr_logfile=log_dir + 'django_stderr.log',
                    autorestart=True,
                    redirect_stderr=True,
                )

@task
def stop_supervisor(**kwargs):
    www = "/home/{user}/www/".format(user=env.project_user)
    venv = www+'venv'
    git_dir = www+'uber_school/'
    backend_dir = git_dir+'backend/'
    log_dir = git_dir + 'logs/'
    with cd(git_dir), virtualenv(venv):
        with shell_env(**kwargs):
            fabtools.supervisor.stop_process('django')
@task
def front_end():
    www = "/home/{user}/www/".format(user=env.project_user)
    git_dir = www+'uber_school/'
    front_dir = git_dir+'app_client/'
    sudo('apt-get -y install ruby-full')
    sudo('npm install -g grunt-cli')
    sudo('npm -g install grunt')
    sudo('gem install sass')
    with cd(front_dir):
        run('npm update')
        sudo('npm install')
        run('grunt compile --force')
@task
def rerun_server(**kwargs):
    stop_supervisor(**kwargs)
    run_supervisor(**kwargs)

@task
def run_server(**kwargs):
    install_packages()
    update_project()
    setup_nginx()
    install_dependencies()
    migrate(**kwargs)
    front_end()
    run_supervisor(**kwargs)
