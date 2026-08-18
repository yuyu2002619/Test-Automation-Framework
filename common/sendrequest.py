import json
import allure
import requests
import urllib3
import time

from conf import setting
from common.exceptions import RequestExecutionError
from common.recordlog import logs
from common.security import redact_sensitive, redact_text, redact_url
from requests import utils
from common.readyaml import ReadYamlData
from urllib3.exceptions import InsecureRequestWarning


class SendRequest:
    """发送接口请求，暂时只写了get和post方法的请求"""

    def __init__(self, cookie=None):
        self.cookie = cookie
        self.read = ReadYamlData()

    @staticmethod
    def _raise_request_error(method, url, exc):
        """将 requests 异常转换为带请求上下文的框架异常。"""

        method = str(method or 'UNKNOWN').upper()
        safe_url = redact_url(url) if url else '<missing-url>'
        if isinstance(exc, requests.exceptions.Timeout):
            category = '请求超时'
        elif isinstance(exc, requests.exceptions.ConnectionError):
            category = '连接失败'
        else:
            category = '请求执行失败'

        message = f'HTTP{category}：method={method}, url={safe_url}; cause={exc}'
        logs.error(message)
        raise RequestExecutionError(message) from exc

    def get(self, url, data, header):
        """
        :param url: 接口地址
        :param data: 请求参数
        :param header: 请求头
        :return:
        """
        if not setting.TLS_VERIFY:
            requests.packages.urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        try:
            if data is None:
                response = requests.get(url, headers=header, cookies=self.cookie,
                                        timeout=setting.API_TIMEOUT, verify=setting.TLS_VERIFY)
            else:
                response = requests.get(url, data, headers=header, cookies=self.cookie,
                                        timeout=setting.API_TIMEOUT, verify=setting.TLS_VERIFY)
        except requests.RequestException as exc:
            self._raise_request_error('GET', url, exc)
        # 响应时间/毫秒
        res_ms = response.elapsed.microseconds / 1000
        # 响应时间/秒
        res_second = response.elapsed.total_seconds()
        response_dict = dict()

        # 接口响应状态码
        response_dict['code'] = response.status_code
        # 接口响应文本
        response_dict['text'] = response.text
        try:
            response_dict['body'] = response.json().get('body')
        except (ValueError, AttributeError):
            response_dict['body'] = ''
        response_dict['res_ms'] = res_ms
        response_dict['res_second'] = res_second
        return response_dict

    def post(self, url, data, header):
        """
        :param url:
        :param data: 请求数据
        :param header:
        :return:
        """
        # 控制台输出InsecureRequestWarning错误
        if not setting.TLS_VERIFY:
            requests.packages.urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        try:
            if data is None:
                response = requests.post(url, header, cookies=self.cookie,
                                         timeout=setting.API_TIMEOUT, verify=setting.TLS_VERIFY)
            else:
                response = requests.post(url, data, headers=header, cookies=self.cookie,
                                         timeout=setting.API_TIMEOUT, verify=setting.TLS_VERIFY)
        except requests.RequestException as exc:
            self._raise_request_error('POST', url, exc)
        # 响应时间/毫秒
        res_ms = response.elapsed.microseconds / 1000
        # 响应时间/秒
        res_second = response.elapsed.total_seconds()
        response_dict = dict()
        # 接口响应状态码
        response_dict['code'] = response.status_code
        # 接口响应文本
        response_dict['text'] = response.text
        try:
            response_dict['body'] = response.json().get('body')
        except (ValueError, AttributeError):
            response_dict['body'] = ''
        response_dict['res_ms'] = res_ms
        response_dict['res_second'] = res_second
        return response_dict

    def send_request(self, **kwargs):

        session = requests.session()
        cookie = {}
        try:
            result = session.request(**kwargs)
            set_cookie = requests.utils.dict_from_cookiejar(result.cookies)
            if set_cookie:
                cookie['Cookie'] = set_cookie
                self.read.write_yaml_data(cookie)
                logs.info("cookie：%s" % redact_sensitive(cookie))
            logs.info("接口返回信息：%s" % redact_text(result.text) if result.text else result)
        except requests.exceptions.RequestException as exc:
            self._raise_request_error(kwargs.get('method'), kwargs.get('url'), exc)
        return result

    def run_main(self, name, url, case_name, header, method, cookies=None, file=None, **kwargs):
        """
        接口请求
        :param name: 接口名
        :param url: 接口地址
        :param case_name: 测试用例
        :param header:请求头
        :param method:请求方法
        :param cookies：默认为空
        :param file: 上传文件接口
        :param kwargs: 请求参数，根据yaml文件的参数类型
        :return:
        """

        try:
            # 收集报告日志
            logs.info('接口名称：%s' % name)
            logs.info('请求地址：%s' % redact_url(url))
            logs.info('请求方式：%s' % method)
            logs.info('测试用例名称：%s' % case_name)
            safe_header = redact_sensitive(header)
            safe_cookies = redact_sensitive(cookies)
            safe_kwargs = redact_sensitive(kwargs)
            logs.info('请求头：%s' % safe_header)
            logs.info('Cookie：%s' % safe_cookies)
            req_params = json.dumps(safe_kwargs, ensure_ascii=False)
            if "data" in kwargs.keys():
                allure.attach(req_params, '请求参数', allure.attachment_type.TEXT)
                logs.info("请求参数：%s" % safe_kwargs)
            elif "json" in kwargs.keys():
                allure.attach(req_params, '请求参数', allure.attachment_type.TEXT)
                logs.info("请求参数：%s" % safe_kwargs)
            elif "params" in kwargs.keys():
                allure.attach(req_params, '请求参数', allure.attachment_type.TEXT)
                logs.info("请求参数：%s" % safe_kwargs)
        except Exception as e:
            logs.error(e)
        # time.sleep(0.5)
        if not setting.TLS_VERIFY:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        response = self.send_request(method=method,
                                     url=url,
                                     headers=header,
                                     cookies=cookies,
                                     files=file,
                                     timeout=setting.API_TIMEOUT,
                                     verify=setting.TLS_VERIFY,
                                     **kwargs)
        return response
