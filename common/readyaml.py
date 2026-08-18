import yaml
import traceback
import os

from common.exceptions import TestDataError, YamlLoadError
from common.recordlog import logs
from conf.operationConfig import OperationConfig
from conf.setting import FILE_PATH


def _load_yaml_file(file):
    """使用 UTF-8 安全解析 YAML，并保留底层异常链。"""

    try:
        with open(file, 'r', encoding='utf-8') as yaml_file:
            data = yaml.safe_load(yaml_file)
    except FileNotFoundError as exc:
        error = YamlLoadError(f'YAML文件不存在：{file}')
        logs.error(str(error))
        raise error from exc
    except UnicodeDecodeError as exc:
        error = YamlLoadError(f'YAML文件不是有效的UTF-8编码：{file}')
        logs.error(str(error))
        raise error from exc
    except yaml.YAMLError as exc:
        error = YamlLoadError(f'YAML语法解析失败：{file}；{exc}')
        logs.error(str(error))
        raise error from exc
    except OSError as exc:
        error = YamlLoadError(f'YAML文件读取失败：{file}；{exc}')
        logs.error(str(error))
        raise error from exc

    if data is None:
        error = TestDataError(f'YAML文件内容为空：{file}')
        logs.error(str(error))
        raise error

    return data


def get_testcase_yaml(file):
    """读取并校验接口测试 YAML 的顶层结构。"""

    data = _load_yaml_file(file)
    if not isinstance(data, list):
        raise TestDataError(
            f'YAML根节点必须是list类型：{file}；'
            f'当前类型为：{type(data).__name__}'
        )
    if not data:
        raise TestDataError(f'YAML测试用例列表不能为空：{file}')

    for index, yaml_case in enumerate(data):
        location = f'{file}的第{index + 1}个顶层用例'
        if not isinstance(yaml_case, dict):
            raise TestDataError(f'{location}必须是dict类型')

        base_info = yaml_case.get('baseInfo')
        test_cases = yaml_case.get('testCase')
        if not isinstance(base_info, dict):
            raise TestDataError(f'{location}缺少baseInfo，或baseInfo不是dict类型')
        if not isinstance(test_cases, list):
            raise TestDataError(f'{location}缺少testCase，或testCase不是list类型')
        if not test_cases:
            raise TestDataError(f'{location}的testCase不能为空')
        if not all(isinstance(test_case, dict) and test_case for test_case in test_cases):
            raise TestDataError(f'{location}的testCase每一项都必须是非空dict类型')

    if len(data) == 1:
        yaml_case = data[0]
        return [[yaml_case['baseInfo'], test_case] for test_case in yaml_case['testCase']]

    return data


class ReadYamlData:
    """读写接口的YAML格式测试数据"""

    def __init__(self, yaml_file=None):
        if yaml_file is not None:
            self.yaml_file = yaml_file
        else:
            pass
        self.conf = OperationConfig()
        self.yaml_data = None

    @property
    def get_yaml_data(self):
        """
        获取测试用例yaml数据
        :param file: YAML文件
        :return: 返回list
        """
        self.yaml_data = _load_yaml_file(self.yaml_file)
        return self.yaml_data

    def write_yaml_data(self, value):
        """
        写入数据需为dict，allow_unicode=True表示写入中文，sort_keys按顺序写入
        写入YAML文件数据,主要用于接口关联
        :param value: 写入数据，必须用dict
        :return:
        """

        file = None
        file_path = FILE_PATH['EXTRACT']
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        try:
            file = open(file_path, 'a', encoding='utf-8')
            if isinstance(value, dict):
                write_data = yaml.dump(value, allow_unicode=True, sort_keys=False)
                file.write(write_data)
            else:
                logs.info('写入[extract.yaml]的数据必须为dict格式')
        except Exception:
            logs.error(str(traceback.format_exc()))
        finally:
            if file:
                file.close()

    def clear_yaml_data(self):
        """
        清空extract.yaml文件数据
        :param filename: yaml文件名
        :return:
        """
        with open(FILE_PATH['EXTRACT'], 'w') as f:
            f.truncate()

    def get_extract_yaml(self, node_name, second_node_name=None):
        """
        用于读取接口提取的变量值
        :param node_name:
        :return:
        """
        if os.path.exists(FILE_PATH['EXTRACT']):
            pass
        else:
            logs.error('extract.yaml不存在')
            file = open(FILE_PATH['EXTRACT'], 'w')
            file.close()
            logs.info('extract.yaml创建成功！')
        try:
            with open(FILE_PATH['EXTRACT'], 'r', encoding='utf-8') as rf:
                ext_data = yaml.safe_load(rf)
                if second_node_name is None:
                    return ext_data[node_name]
                else:
                    return ext_data[node_name][second_node_name]
        except Exception as e:
            logs.error(f"【extract.yaml】没有找到：{node_name},--%s" % e)

    def get_testCase_baseInfo(self, case_info):
        """
        获取testcase yaml文件的baseInfo数据
        :param case_info: yaml数据，dict类型
        :return:
        """
        pass

    def get_method(self):
        """
        :param self:
        :return:
        """
        yal_data = self.get_yaml_data()
        metd = yal_data[0].get('method')
        return metd

    def get_request_parame(self):
        """
        获取yaml测试数据中的请求参数
        :return:
        """
        data_list = []
        yaml_data = self.get_yaml_data()
        del yaml_data[0]
        for da in yaml_data:
            data_list.append(da)
        return data_list
