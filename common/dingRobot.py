import base64
import hashlib
import hmac
import os
import time
import urllib.parse

import requests

from conf import setting


def generate_sign(secret):
    """Generate a DingTalk timestamp and HMAC-SHA256 signature."""
    if not isinstance(secret, str) or not secret.strip():
        raise ValueError('钉钉Secret不能为空')

    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode('utf-8')
    string_to_sign = f'{timestamp}\n{secret}'
    hmac_code = hmac.new(
        secret_enc,
        string_to_sign.encode('utf-8'),
        digestmod=hashlib.sha256,
    ).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


def _required_environment_value(name):
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f'已启用钉钉通知，但未设置环境变量 {name}')
    return value.strip()


def send_dd_msg(content_str, at_all=True):
    """Send a text message using credentials supplied by the environment."""
    webhook = _required_environment_value('TAF_DINGTALK_WEBHOOK')
    secret = _required_environment_value('TAF_DINGTALK_SECRET')
    timestamp, sign = generate_sign(secret)

    headers = {'Content-Type': 'application/json;charset=utf-8'}
    data = {
        'msgtype': 'text',
        'text': {'content': content_str},
        'at': {'isAtAll': at_all},
    }
    response = requests.post(
        webhook,
        params={'timestamp': timestamp, 'sign': sign},
        json=data,
        headers=headers,
        timeout=setting.API_TIMEOUT,
        verify=setting.TLS_VERIFY,
    )
    return response.text
