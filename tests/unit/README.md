# Day 48：框架行为基线测试

这个目录只测试框架自身的局部行为，不启动 Mock 服务，不发送 HTTP 请求，
也不连接真实数据库。

## 阅读顺序

1. `conf/operationConfig.py`
2. `common/readyaml.py`
3. `base/apiutil.py` 中的 `replace_load`、`extract_data`、`extract_data_list`
4. `common/debugtalk.py` 中的 `get_extract_data`、`get_extract_order_data`
5. `common/assertions.py`

阅读每个方法时回答五个问题：

1. 输入是什么类型？
2. 正常分支返回什么？
3. 失败或边界分支返回什么、抛什么异常？
4. 是否修改参数、文件或其他共享状态？
5. 依赖了哪些外部对象，单元测试中如何替换？

## 测试文件

- `test_operation_config.py`：INI 配置读取、缺失项和写入行为。
- `test_readyaml.py`：单接口 YAML、业务 YAML 和错误输入。
- `test_request_transform.py`：`${...}` 变量替换、JSONPath/正则提取。
- `test_assertions.py`：状态码、包含、相等和任意值断言。
- `conftest.py`：覆盖根目录的清理 Fixture，并禁止意外网络/数据库访问。

测试名带有 `current_behavior` 的用例，记录的是当前真实行为，不表示该行为合理。
后续有意修复代码时，应同时更新这些测试，并在学习记录中说明行为为什么改变。

## 执行

先把 uv 缓存固定到当前 D 盘项目目录，避免使用 C 盘系统临时目录：

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location) ".uv-cache"
```

先确认收集数量不是 0：

```powershell
uv run --frozen python -m pytest --basetemp=".pytest-tmp-$PID" --confcutdir=tests/unit tests/unit --collect-only -q
```

再运行：

```powershell
uv run --frozen python -m pytest --basetemp=".pytest-tmp-$PID" --confcutdir=tests/unit tests/unit -q
```

`--basetemp` 把 pytest 临时目录放到当前项目的可写目录；`$PID` 为当前
PowerShell 进程号，可以避免不同执行身份复用同一个临时目录而发生权限冲突；
`--confcutdir` 防止加载项目根目录会清空真实 `extract.yaml` 的自动 Fixture。`pytest.ini`
已经使用标准的 `python_functions = test_*` 发现规则，不再需要命令行临时覆盖。
