"""框架核心异常。

这些异常用于在保留原始异常链的同时，向测试报告提供可定位的业务上下文。
"""


class TestDataError(ValueError):
    """测试数据内容或结构不符合框架约定。"""


class YamlLoadError(TestDataError):
    """YAML 文件无法读取、解码或解析。"""


class RequestExecutionError(RuntimeError):
    """HTTP 请求在获得有效响应前执行失败。"""
