import logging
import os
import sys

DIR_BASE = os.path.dirname(os.path.dirname(__file__))
sys.path.append(DIR_BASE)

TRUE_VALUES = frozenset({'1', 'true', 'yes', 'on'})
FALSE_VALUES = frozenset({'0', 'false', 'no', 'off'})

CONFIG_ENV_OVERRIDES = {
    ('api_envi', 'host'): 'TAF_API_BASE_URL',
    ('report_type', 'type'): 'TAF_REPORT_TYPE',
    ('mysql', 'host'): 'TAF_MYSQL_HOST',
    ('mysql', 'port'): 'TAF_MYSQL_PORT',
    ('mysql', 'username'): 'TAF_MYSQL_USERNAME',
    ('mysql', 'password'): 'TAF_MYSQL_PASSWORD',
    ('mysql', 'database'): 'TAF_MYSQL_DATABASE',
    ('redis', 'host'): 'TAF_REDIS_HOST',
    ('redis', 'port'): 'TAF_REDIS_PORT',
    ('redis', 'username'): 'TAF_REDIS_USERNAME',
    ('redis', 'password'): 'TAF_REDIS_PASSWORD',
    ('redis', 'db'): 'TAF_REDIS_DB',
    ('clickhouse', 'host'): 'TAF_CLICKHOUSE_HOST',
    ('clickhouse', 'port'): 'TAF_CLICKHOUSE_PORT',
    ('clickhouse', 'username'): 'TAF_CLICKHOUSE_USERNAME',
    ('clickhouse', 'password'): 'TAF_CLICKHOUSE_PASSWORD',
    ('clickhouse', 'timeout'): 'TAF_CLICKHOUSE_TIMEOUT',
    ('clickhouse', 'db'): 'TAF_CLICKHOUSE_DB',
    ('mongodb', 'host'): 'TAF_MONGODB_HOST',
    ('mongodb', 'port'): 'TAF_MONGODB_PORT',
    ('mongodb', 'username'): 'TAF_MONGODB_USERNAME',
    ('mongodb', 'password'): 'TAF_MONGODB_PASSWORD',
    ('mongodb', 'database'): 'TAF_MONGODB_DATABASE',
    ('email', 'host'): 'TAF_EMAIL_HOST',
    ('email', 'port'): 'TAF_EMAIL_PORT',
    ('email', 'user'): 'TAF_EMAIL_USER',
    ('email', 'passwd'): 'TAF_EMAIL_PASSWORD',
    ('email', 'addressee'): 'TAF_EMAIL_ADDRESSEE',
    ('email', 'subject'): 'TAF_EMAIL_SUBJECT',
    ('ssh', 'host'): 'TAF_SSH_HOST',
    ('ssh', 'port'): 'TAF_SSH_PORT',
    ('ssh', 'username'): 'TAF_SSH_USERNAME',
    ('ssh', 'password'): 'TAF_SSH_PASSWORD',
    ('ssh', 'timeout'): 'TAF_SSH_TIMEOUT',
    ('ssh', 'command'): 'TAF_SSH_COMMAND',
}


def get_env_bool(name, default):
    """Read a boolean environment variable with explicit validation."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    value = raw_value.strip().lower()
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    raise ValueError(f'环境变量 {name} 必须是布尔值，当前值为：{raw_value!r}')


def get_env_int(name, default, min_value=1):
    """Read an integer environment variable and validate its lower bound."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        value = int(raw_value.strip())
    except ValueError as exc:
        raise ValueError(f'环境变量 {name} 必须是整数，当前值为：{raw_value!r}') from exc

    if value < min_value:
        raise ValueError(f'环境变量 {name} 不能小于 {min_value}，当前值为：{value}')
    return value


def get_config_env_name(section, option):
    """Return the environment-variable name that overrides an INI option."""
    return CONFIG_ENV_OVERRIDES.get((section.casefold(), option.casefold()))


def get_api_base_url(config, default='http://127.0.0.1:8787'):
    """Resolve API base URL using environment, INI, then a safe default."""
    env_value = os.getenv('TAF_API_BASE_URL')
    if env_value is not None:
        base_url = env_value.strip()
        if not base_url:
            raise ValueError('环境变量 TAF_API_BASE_URL 不能为空')
        return base_url

    ini_value = config.get_section_for_data('api_envi', 'host')
    if ini_value and ini_value.strip():
        return ini_value.strip()
    return default

# log日志输出级别
LOG_LEVEL = logging.DEBUG  # 文件
STREAM_LOG_LEVEL = logging.DEBUG  # 控制台

# 接口超时时间，单位/s；TLS验证默认开启
API_TIMEOUT = get_env_int('TAF_API_TIMEOUT', 60)
TLS_VERIFY = get_env_bool('TAF_TLS_VERIFY', True)

# excel文件的sheet页，默认读取第一个sheet页的数据，int类型，第一个sheet为0，以此类推0.....9
SHEET_ID = 0

# 生成的测试报告类型，可以生成两个风格的报告，allure或tm
REPORT_TYPE = os.getenv('TAF_REPORT_TYPE', 'allure').strip().lower()
if REPORT_TYPE not in {'allure', 'tm'}:
    raise ValueError('环境变量 TAF_REPORT_TYPE 只能是 allure 或 tm')

# 是否发送钉钉消息。保留dd_msg别名兼容旧入口。
DINGTALK_ENABLED = get_env_bool('TAF_DINGTALK_ENABLED', False)
dd_msg = DINGTALK_ENABLED

# 文件路径
FILE_PATH = {
    'CONFIG': os.path.join(DIR_BASE, 'conf/config.ini'),
    'LOG': os.path.join(DIR_BASE, 'logs'),
    'YAML': os.path.join(DIR_BASE),
    'TEMP': os.path.join(DIR_BASE, 'report/temp'),
    'TMR': os.path.join(DIR_BASE, 'report/tmreport'),
    'EXTRACT': os.path.join(DIR_BASE, 'extract.yaml'),
    'XML': os.path.join(DIR_BASE, 'data/sql'),
    'RESULTXML': os.path.join(DIR_BASE, 'report'),
    'EXCEL': os.path.join(DIR_BASE, 'data', '测试数据.xls')
}

# 默认请求头信息
LOGIN_HEADER = {
    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive'
}
