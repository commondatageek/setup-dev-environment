#!/usr/bin/env python

### requires python 2

###
### TODO
###
### - add jupyter notebook configuration file
### - add htop configuration file
### - think of a good way to get SSH keys and SSH config file in there
### - put tmux configuration in there
### - put .bashrc files in there
###     - aliases
###     - add anaconda to path
###     - automatically connect to tmux if possible
### - shell scripts
###     - launch database applications

from fabric.api import *
import time

def update_image():
    sudo('apt-get -y update')
    sudo('apt-get -y upgrade')
    sudo('reboot')

def wait_for_reboot(retries=12):
    print 'Waiting for host to become available.'
    while True:
        if retries == 0:
            raise Exception('Unable to connect to host.')

        try:
            print 'attempt connection ...'
            run('uname -a')
            break
        except:
            time.sleep(5)
            retries -= 1

def create_user(password=None, public_key_file=None):
    # create user
    sudo('adduser analyst --gecos Analyst --disabled-password')
    sudo('usermod -aG sudo analyst')
    sudo('''echo 'analyst ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers''')
    sudo('''echo 'ubuntu ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers''')

    # create necessary directories
    sudo('mkdir -p /home/analyst/.ssh')
    sudo('mkdir -p /home/analyst/bin')

    # set key
    if public_key_file:
        put(local_path=public_key_file, remote_path='/home/analyst/.ssh/authorized_keys', use_sudo=True)
    else:
        sudo('cp /home/ubuntu/.ssh/authorized_keys /home/analyst/.ssh/authorized_keys')

    # set password
    if password:
        run(''' echo '{}' | sudo passwd --stdin analyst'''.format(password))
    else:
        print 'Please enter a password for user analyst'
        sudo('''passwd analyst''')

    # ensure correct owner, group, and permissions
    sudo('chown -R analyst /home/analyst && chgrp -R analyst /home/analyst')
    sudo('chmod -R 700 /home/analyst/.ssh')

def mount_storage():
    sudo('mkdir -p /storage')
    sudo('mount /dev/xvdf /storage')

    # create symlink from home directory
    run('ln -s /storage')

def install_utils():
    sudo('apt-get -y install tree maven tmux zip unzip htop nload tcptrack build-essential rlwrap graphviz')


def install_git():
    # install prereqs
    sudo('apt-get -y install libcurl4-gnutls-dev libexpat1-dev gettext libz-dev libssl-dev')

    # build git from source code
    run('rm -rf git-2.10.2*')
    run('wget https://www.kernel.org/pub/software/scm/git/git-2.10.2.tar.xz')
    run('tar -xvf git-2.10.2.tar.xz')
    with cd('git-2.10.2'):
        run('./configure')
        run('make -j 8 all')
        sudo('make install')
    run('rm -rf git-2.10.2*')


def install_lein():
    # install prereqs
    sudo('apt-get -y install openjdk-8-jdk')

    # get lein
    with cd('bin'):
        run('rm -f lein')
        run('wget https://raw.githubusercontent.com/technomancy/leiningen/stable/bin/lein')
        run('chmod 755 lein')

    # create temporary project to download main lein dependencies
    run('rm -rf deleteme')
    run('lein new deleteme')
    with cd('deleteme'):
        run('lein deps')
    run('rm -rf deleteme')

def install_anaconda():
    # clean up if necessary
    run('rm -rf anaconda3')

    # install
    run('rm -f ./anaconda.sh')
    run('wget https://repo.continuum.io/archive/Anaconda3-5.0.1-Linux-x86_64.sh -O anaconda.sh')
    run('bash ./anaconda.sh -b -p anaconda3')
    run('anaconda3/bin/conda update -y conda')
    run('rm -f ./anaconda.sh')

def mk_py2_env():
    run('rm -rf anaconda3/envs/py2')

    # everything we can get from anaconda
    run('anaconda3/bin/conda create -y -n py2 python=2 s3fs numpy pandas scipy scikit-learn jupyter pymc beautifulsoup4 bokeh boto3 csvkit curl dask datashader fabric paramiko gensim graphviz ipykernel libpq luigi matplotlib nltk psycopg2 pymongo pytz seaborn spyder sqlalchemy sqlite statsmodels sympy tensorflow terminado tornado wget')
    # everything we need to get through pip
    run('source anaconda3/bin/activate py2 && pip install celery doit==0.29.0')

def mk_py3_env():
    run('rm -rf anaconda3/envs/py3')

    # everything we can get from anaconda
    run('anaconda3/bin/conda create -y -n py3 python=3 s3fs numpy pandas scipy scikit-learn jupyter pymc beautifulsoup4 bokeh boto3 csvkit curl dask datashader        paramiko gensim graphviz ipykernel libpq luigi matplotlib nltk psycopg2 pymongo pytz seaborn spyder sqlalchemy sqlite statsmodels sympy tensorflow terminado tornado wget')
    # everything we need to get through pip
    run('source anaconda3/bin/activate py3 && pip install celery doit')

def install_python():
    install_anaconda()
    mk_py2_env()
    mk_py3_env()

def install_rstudio():
    # install prereqs
    sudo('apt-get -y install r-base gdebi-core')

    # get and install rstudio
    run('rm -f rstudio-server-1*.deb')
    run('wget https://download2.rstudio.org/rstudio-server-1.0.44-amd64.deb')
    sudo('gdebi -n rstudio-server-1.0.44-amd64.deb')
    run('rm -f rstudio-server-1*.deb')

def install_emacs():
    # install prereqs
    sudo('apt-get -y install libncurses5 libncurses5-dev')

    # build emacs from source code
    run('rm -rf emacs-25.1*')
    run('wget ftp://ftp.gnu.org/pub/gnu/emacs/emacs-25.1.tar.xz')
    run('tar -xvf emacs-25.1.tar.xz')
    with cd('emacs-25.1'):
        run('./configure --with-x-toolkit=no --with-xpm=no --with-jpeg=no --with-png=no --with-gif=no --with-tiff=no CFLAGS=-no-pie')
        run('make -j 8')
        sudo('make install')
    run('rm -rf emacs-25.1*')


def install_spacemacs():
    # get spacemacs from github
    run('rm -rf .emacs.d')
    run('git clone https://github.com/syl20bnr/spacemacs .emacs.d')


def install_vim():
    # install prereqs
    sudo('apt-get -y install python-dev python3-dev')

    # get rid of any previous vim configuration
    sudo('rm -rf .vim')

    # build vim 8 from scratch
    sudo('rm -rf vim')
    run('git clone https://github.com/vim/vim.git')
    with cd('vim'):
        sudo('make distclean')
        run('./configure --with-features=huge --enable-pythoninterp=yes --enable-python3interp=yes && make -j 8')
        sudo('make install')
    sudo('rm -rf vim')

    # install Vundle
    run('rm -rf ~/.vim/bundle/Vundle.vim')
    run('git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim')

    # install mustang color theme
    run('rm -rf mustang-vim')
    run('git clone https://github.com/croaker/mustang-vim.git')
    run('mkdir -p ~/.vim/colors')
    run('mv mustang-vim/colors/mustang.vim ~/.vim/colors')
    run('rm -rf mustang-vim')


def install_sqlite():
    sudo('apt-get -y install sqlite3')
    put('.bash_aliases', '/home/analyst')


def install_neo4j():
    run('wget -O - https://debian.neo4j.org/neotechnology.gpg.key | sudo apt-key add -')
    run('''echo 'deb https://debian.neo4j.org/repo stable/' | sudo tee /etc/apt/sources.list.d/neo4j.list''')
    sudo('apt-get -y update')
    sudo('apt-get -y install neo4j')

def install_vaulted():
    run('rm -rf gopath')
    run('mkdir gopath')
    sudo('apt-get -y install golang')
    run('GOPATH=/home/analyst/gopath go get -u github.com/miquella/vaulted')
    run('ln ~/gopath/bin/vaulted ~/bin/vaulted')

def setup_conf_files():
    run('rm -rf setup-dev-environment')
    run('git clone https://github.com/commondatageek/setup-dev-environment.git setup-dev-environment')

    run('rm -rf .tmux.conf')
    run('ln -s setup-dev-environment/config-files/tmux/.tmux.conf')

    run('rm -rf .gitattributes')
    run('ln -s setup-dev-environment/config-files/git/.gitattributes')

    run('rm -rf .gitconfig')
    run('ln -s setup-dev-environment/config-files/git/.gitconfig')

    run('rm -f /home/analyst/bin/ipynb_output_filter.py')
    run('ln -s setup-dev-environment/config-files/git/ipynb_output_filter.py /home/analyst/bin/ipynb_output_filter.py')

    run('rm -f .spacemacs')
    run('ln -s setup-dev-environment/config-files/emacs/.spacemacs')

    run('rm -f .vimrc')
    run('ln -s setup-dev-environment/config-files/vim/.vimrc')

def setup_env():
    mount_storage()
    install_utils()
    install_git()
    install_lein()
    install_python()
    install_rstudio()
    install_emacs()
    install_spacemacs()
    install_vim()
    install_sqlite()
    install_neo4j()

