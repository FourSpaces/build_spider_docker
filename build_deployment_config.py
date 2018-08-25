# -*- conding:utf-8  -*-

# 自动生成

import os
import logging
import configparser
from string import Template
from traceback import format_exc


class config_stencil(object):

    @classmethod
    def getDockerfile(cls):
        return """
FROM troycube/scrapyd-alpine:py3.6

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories
# add the required dependencies
RUN apk add --no-cache build-base

# cache pip install
COPY ./requirements.txt /root/app/requirements.txt

RUN pip3 install --no-cache-dir -r /root/app/requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

COPY . /root/app/$object_name
WORKDIR /root/app/$object_name
RUN bash .tools/build_egg.sh /root/scrapyd/eggs

CMD ["bash", ".tools/start.sh"]
        """
        pass

    @classmethod
    def getRequirements(cls):
        return """
demjson
pytz
        """

    @classmethod
    def getMakefile(cls):
        return """
build:
	bash -x .tools/build_image.sh

deploy:
	bash -x .tools/deploy.sh
        """

    @classmethod
    def getDockerignore(cls):
        return """
# Created by .ignore support plugin (hsz.mobi)
### Example user template template
### Example user template

# IntelliJ project files
.idea
*.iml
out
gen

### Python template
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/

# Translations
*.mo
*.pot

# Django stuff:
*.log
.static_storage/
.media/
local_settings.py

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# pyenv
.python-version

# celery beat schedule file
celerybeat-schedule

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/

        """

    @classmethod
    def getCircleciConfig(cls):
        return """
version: 2
jobs:
    build:
        machine: true
        working_directory: ~/$object_name
        steps:
            - checkout
            - run:
                name: Build/Push Image
                command: make build
    deploy-test:
        machine: true
        working_directory: ~/$object_name
        steps:
            - checkout
            - run:
                name: Deploy
                command: make deploy
    deploy-production:
        machine: true
        working_directory: ~/$object_name
        steps:
            - checkout
            - run:
                name: Deploy
                command: make deploy

workflows:
    version: 2
    build-to-take-off:
        jobs:
            - build:
                filters:
                    branches:
                        only:
                            - /support\/.*/
                            - /feature\/.*/
                            - develop
                            - master
            - deploy-test:
                requires:
                    - build
                filters:
                    branches:
                        only:
                            - /support\/.*/
                            - /feature\/.*/
                            - develop
            - hold:
                requires:
                    - build
                type: approval
                filters:
                    branches:
                        only:
                            - master
            - deploy-production:
                requires:
                    - hold
                filters:
                    branches:
                        only:
                            - master
        """

    @classmethod
    def getToolsBuild_egg(cls):
        return """
#!/usr/bin/env bash
# Created by paincompiler on 2018/08/25

##########settings##########
set -o errexit
set -o errtrace
#set -o pipefail
set -o xtrace
##########settings##########

function finish {
    # cleanup code here
    echo "cleaning up"
}

trap finish EXIT

source $(dirname $0)/utils.sh
set_basic_env

scrapyd-deploy --build-egg=${GIT_COMMIT}.egg

if [[ $# -ne 0 ]]; then
    # >= 1
    # move egg to scrapyd project dir
    mkdir $1/${PROJECT_NAME}/
    mv ${GIT_COMMIT}.egg $1/${PROJECT_NAME}/
fi
        """

    @classmethod
    def getToolsBuild_image(cls):
        return """
#!/usr/bin/env bash
# Created by paincompiler on 2018/08/25

##########settings##########
set -o errexit
set -o errtrace
set -o xtrace
##########settings##########

function finish {
    # cleanup code here

    if [[ -z "${ZXZL_DOCKER_REGISTRY_HOST// }" ]]; then
        # docker registry not set
        IMAGE_TAG=crawler/${PROJECT_NAME}:${GIT_COMMIT}
        sudo docker rmi -f ${IMAGE_TAG}
    else
        # build docker image
        IMAGE_TAG=${ZXZL_DOCKER_REGISTRY_HOST}/cheng1483/${PROJECT_NAME}:${GIT_COMMIT}
        sudo docker rmi -f ${IMAGE_TAG}
    fi

    NONE_IMAGE=`sudo docker images | grep "^<none>" | awk '{print $3}'`

    echo "$NONE_IMAGE"

    if [[ "$NONE_IMAGE" != "" ]]; then
        sudo docker rmi -f ${NONE_IMAGE}
    fi

    echo "cleaning up"
}

trap finish EXIT

source $(dirname $0)/utils.sh
set_basic_env

# build docker image
if [[ -z "${ZXZL_DOCKER_REGISTRY_HOST// }" ]]; then
    # docker registry not set
    IMAGE_TAG=crawler/${PROJECT_NAME}:${GIT_COMMIT}
    sudo docker build -t ${IMAGE_TAG} .
else
    # build docker image
    sudo docker login -u ${ZXZL_DOCKER_REGISTRY_USERNAME} -p ${ZXZL_DOCKER_REGISTRY_PASSWORD} ${ZXZL_DOCKER_REGISTRY_HOST}
    IMAGE_TAG=${ZXZL_DOCKER_REGISTRY_HOST}/cheng1483/${PROJECT_NAME}:${GIT_COMMIT}
    sudo docker build -t ${IMAGE_TAG} .
    sudo docker push ${IMAGE_TAG}
fi
        """

    @classmethod
    def gerToolsDeoloy(cls):
        return """
#!/usr/bin/env bash
# Created by paincompiler on 2018/08/25

##########settings##########
set -o errexit
set -o errtrace
set -o xtrace
##########settings##########

function finish {
    # cleanup code here
    echo "cleaning up"
}

trap finish EXIT

source $(dirname $0)/utils.sh
set_basic_env
#curl -v http://deployer.io:9001/deploy/${PROJECT_NAME}/${PROJECT_ENV}/${GIT_COMMIT}
        """

    @classmethod
    def getToolsStart(cls):
        return """
#!/usr/bin/env bash
# Created by paincompiler on 2018/08/25

##########settings##########
set -o errtrace
set -o nounset
set -o pipefail
set -o xtrace
##########settings##########

function finish {
    # cleanup code here
    echo "cleaning up"
}

trap finish EXIT

# script here

if [ ! -d "spiderkeeper" ]; then
  mkdir spiderkeeper
fi

# nohup scrapymon --auth='xyx:xyx' --server=http://0.0.0.0:6800 > scrapymon/log &
nohup spiderkeeper --port=6500 --username='xyx'  --password='xyx233' --server=http://0.0.0.0:6800 &
scrapyd
        """

    @classmethod
    def getToolsUtils(cls):
        return """
#!/usr/bin/env bash
# Created by paincompiler on 2018/08/25

##########settings##########
set -o errexit
set -o errtrace
set -o xtrace
##########settings##########

function set_basic_env {
    # 获取分支信息，获取最近一次提交记录
    # export GIT_BRANCH_BASENAME="`git rev-parse --abbrev-ref HEAD`"
    export GIT_BRANCH_BASENAME="${GIT_BRANCH}"

    if [[ ! -n "${GIT_BRANCH_BASENAME}" ]];then
        export GIT_BRANCH_BASENAME="master"
    fi

    echo "${GIT_BRANCH_BASENAME}"

    export GIT_COMMIT="`git log | head -n 1 | awk '{print $2}'`"

    if [[ "${GIT_BRANCH_BASENAME}" = *"master" ]];then
        export PROJECT_ENV="production"
    elif [[ "${GIT_BRANCH_BASENAME}" = *"/test"* ]];then
        export PROJECT_ENV="debug"
    elif [[ "${GIT_BRANCH_BASENAME}" = *"/release/"* ]];then
        export PROJECT_ENV="debug"
    elif [[ "${GIT_BRANCH_BASENAME}" == *"/develop" ]];then
        export PROJECT_ENV="dev"
    elif [[ "${GIT_BRANCH_BASENAME}" == "support/"* ]];then
        export PROJECT_ENV="dev"
    elif [[ "${GIT_BRANCH_BASENAME}" == "feature/"* ]];then
        export PROJECT_ENV="dev"
    elif [[ "${GIT_BRANCH_BASENAME}" == "hotfix/"* ]];then
        export PROJECT_ENV="dev"
    else
        echo "invalid branch name ${GIT_BRANCH_BASENAME}"
        exit 1
    fi

    # 获取项目名称
    export PROJECT_NAME=`basename $(git rev-parse --show-toplevel)`

    # 当前所在目录
    export SCRIPT_DIR=$(dirname $0)
    export PROJECT_ROOT="${SCRIPT_DIR}/../"
}
        """

    @classmethod
    def getGitignore(cls):
        return """
*.egg
__pycache__/*
.idea/*
.gitignore
.DS_Store/*
/build
/project.egg-info
setup.py
        """


class deployment(object):
    """
    添加构建和部署相关的脚本，我们约定添加到目录 .tools 中，可以直接从示例项目中拷贝并且不需要修改

    添加 Dockerfile（如果不知道是什么请自行 Google），从示例项目中拷贝并进行下图所示的修改

    添加 Makefile （如果不知道是什么请自行 Google），可以直接从示例项目中拷贝并且不需要修改
    添加 CI 配置文件，目录为 .circleci，从示例项目中拷贝并修改 working_directory 为你的项目名称
    找 Dengsheng Qian 开通github repo，添加相关人员
    提交代码
    找 Dengsheng Qian 开通服务器及数据库资源
    找 Dengsheng Qian 或者 PainCompiler Xu 配置 CircleCI
    """
    def __init__(self, object_name, dir_name):
        self.object_name = object_name
        self.dir_name = dir_name
        self.build_config = [
            {'stencil': config_stencil.getDockerfile(), 'path': '.',
             'file_name': 'Dockerfile', 'object_name': self.object_name},
            {'stencil': config_stencil.getRequirements(), 'path': '.',
             'file_name': 'requirements.txt', 'object_name': self.object_name},
            # {'stencil': config_stencil.getMakefile(), 'path': '.',
            #  'file_name': 'Makefile', 'object_name': self.object_name},
            {'stencil': config_stencil.getDockerignore(), 'path': '.',
             'file_name': '.dockerignore', 'object_name': self.object_name},

            {'stencil': config_stencil.getGitignore(), 'path': '.',
             'file_name': '.gitignore', 'object_name': self.object_name},

            # {'stencil': config_stencil.getCircleciConfig(), 'path': './.circleci',
            #  'file_name': 'config.yml', 'object_name': self.dir_name},
            {'stencil': config_stencil.getToolsBuild_egg(), 'path': './.tools',
             'file_name': 'build_egg.sh', 'object_name': self.object_name},
            {'stencil': config_stencil.getToolsBuild_image(), 'path': './.tools',
             'file_name': 'build_image.sh', 'object_name': self.object_name},
            {'stencil': config_stencil.gerToolsDeoloy(), 'path': './.tools',
             'file_name': 'deploy.sh', 'object_name': self.object_name},
            {'stencil': config_stencil.getToolsStart(), 'path': './.tools',
             'file_name': 'start.sh', 'object_name': self.object_name},
            {'stencil': config_stencil.getToolsUtils(), 'path': './.tools',
             'file_name': 'utils.sh', 'object_name': self.object_name},
        ]

        # 构建文件build_deployment
        for conf in self.build_config:
            self.build_deployment(**conf)


    def build_Dockerfile(self):
        stencil_str = config_stencil.getDockerfile()
        self.save_file('.', 'Dockerfile', stencil_str, object_name=self.object_name)

    def build_deployment(self, **kws):
        stencil_str = kws.get('stencil')
        path = kws.get('path')
        file_name = kws.get('file_name')
        object_name = kws.get('object_name')
        self.save_file(path, file_name, stencil_str, object_name=object_name)


    # 明天改成配置式的
    def save_file(self, path, file_name, stencil_str, **kws):
        """

        :param path:
        :param file_name:
        :param stencil_str:
        :param kws:
        :return:
        """
        try:

            # 判断路径
            if not os.path.exists(path):
                os.makedirs(path)

            stencil = Template(stencil_str)
            return_str = stencil.safe_substitute(kws).lstrip('\n')

            with open(path+'//'+file_name, mode='w') as f:
                f.write(return_str)

            logging.info('{} done'.format(path+'//'+file_name))
        except Exception :
            print('{}'.format(format_exc()))


if __name__ == "__main__":

    # 获取项目名称
    current_dir = os.getcwd()
    dir_name = current_dir.split('/')[-1]
    # 查找指定scrapy.cfg文件是否存在
    scrapy_status = os.path.isfile("scrapy.cfg")
    assert scrapy_status, 'scrapy.cfg 不存在，不符合自动配置要求'

    config = configparser.ConfigParser()
    config.read('scrapy.cfg')
    object_name = config['deploy'].get('project') if 'deploy' in config else None
    assert object_name, 'scrapy.cfg 缺失deploy组 或 project 配置'

    # 将项目名称写入到 模版中
    dep = deployment(object_name, dir_name)

    print(current_dir)