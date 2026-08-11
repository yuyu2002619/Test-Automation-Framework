# 2026-08-10 Day 41 学习总结：YAML 参数化、运行时状态、Fixture 与 BFS

> 学习阶段：Day 41 / YAML 读取和运行时状态  
> 项目：`Test-Automation-Framework`  
> 当前分支：`study/baseline`  
> 学习方式：源码精读、最小实验、错误边界验证、口述复盘、算法手写  
> 本日原则：理解并验证原项目行为；不提前重构请求层、断言层、Mock 服务或动态变量实现。

---

## 一、今日目标与完成情况

Day 41 的目标不是泛泛学习 YAML 语法，而是弄清当前项目的两条真实链路：

```text
测试数据链：
YAML 文件文本
→ yaml.safe_load()
→ Python 嵌套对象
→ get_testcase_yaml()
→ pytest.parametrize()
→ Test Item

运行时数据链：
接口响应
→ extract / extract_list 规则
→ 根目录 extract.yaml
→ ${get_extract_data(...)}
→ 后续请求参数
```

本日已完成：

- [x] 阅读 `common/readyaml.py`，理解 `get_testcase_yaml()` 的两种返回结构。
- [x] 对比单接口 `queryUser.yaml` 与业务 `BusinessScenario.yml`。
- [x] 编写并运行 YAML 探针，验证 `safe_load` 和 `get_testcase_yaml` 的真实输出。
- [x] 验证文件不存在、空 YAML、YAML 语法错误三种异常情形。
- [x] 读取 `conf/setting.py`，确认运行时使用的是根目录 `extract.yaml`。
- [x] 阅读 `ReadYamlData` 的写入、清空、读取方法。
- [x] 阅读两个 `conftest.py`，理解 Fixture 范围和测试会话生命周期。
- [x] 阅读 `base/removefile.py`，区分清空文件内容与删除临时文件。
- [x] 解释业务场景五条 Test Item 的数据依赖，以及串行、并行的区别。
- [x] 完成 BFS 模板学习：LC 102 二叉树的层序遍历、LC 637 二叉树的层平均值。

---

## 二、首先区分三个层次：文本、Python 对象、pytest 参数

学习 YAML 时最容易犯的错误，是把下面三个层次混为一谈：

```text
第一层：磁盘上的 YAML 文本
第二层：yaml.safe_load() 后的 Python 对象
第三层：get_testcase_yaml() 整理后交给 pytest 的参数列表
```

### 2.1 YAML 文本

YAML 是普通文本文件。当前项目主要用它保存：

- 接口公共信息，例如 URL、Method、Header；
- 测试用例输入，例如 `data`、`json`、`params`；
- 断言规则，例如 `validation`；
- 动态数据提取规则，例如 `extract`、`extract_list`；
- 动态占位符，例如 `${get_extract_data(token)}`。

以 `testcase/Single interface/queryUser.yaml` 为例：

```yaml
- baseInfo:
    api_name: 用户查询
    url: /dar/user/queryUser
    method: POST
    header:
      Content-Type: application/x-www-form-urlencoded;charset=UTF-8
  testCase:
    - case_name: 有效查询用户
      data:
        user_id: 123839387391912
      validation:
        - contains: { 'msg': '查询成功' }
        - eq: { 'msg_code': 200 }
```

这里最外层的 `-` 表示列表元素。

### 2.2 `yaml.safe_load()`：文本转换为 Python 对象

项目调用：

```python
data = yaml.safe_load(f)
```

`safe_load()`的职责只是把 YAML 文本反序列化为 Python 对象，例如：

```text
YAML list   → Python list
YAML mapping → Python dict
YAML 数字    → Python int / float
YAML null    → Python None
```

它不知道 pytest，也不会自动生成测试用例。

上面的 `queryUser.yaml` 解析后的形状是：

```text
list，长度为 1
└── dict
    ├── "baseInfo"：dict
    └── "testCase"：list
        └── testcase dict
```

对应的 Python 概念模型：

```python
data = [
    {
        "baseInfo": {...},
        "testCase": [
            {...},
            {...},
        ],
    }
]
```

### 2.3 `get_testcase_yaml()`：把 Python 对象适配为 pytest 参数

`common/readyaml.py` 中的核心逻辑：

```python
def get_testcase_yaml(file):
    testcase_list = []
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if len(data) <= 1:
                yam_data = data[0]
                base_info = yam_data.get('baseInfo')
                for ts in yam_data.get('testCase'):
                    param = [base_info, ts]
                    testcase_list.append(param)
                return testcase_list
            else:
                return data
```

因此这个函数有两个职责：

```text
读取 YAML 文件并调用 safe_load
+
按当前项目规则重组 Python 对象，使其匹配 pytest 参数化方式
```

不是 `get_testcase_yaml()`本身把文本转换为 Python 对象；真正负责转换的是 `yaml.safe_load()`。

---

## 三、单接口 YAML 与业务 YAML 的准确比较

### 3.1 单接口 YAML：拆成两个 pytest 参数

`testcase/Single interface/test_debug_api.py` 中的新增、修改、删除、查询测试，使用的都是双参数化形式：

```python
@pytest.mark.parametrize(
    'base_info,testcase',
    get_testcase_yaml('./testcase/Single interface/queryUser.yaml')
)
def test_query_user(self, base_info, testcase):
    RequestBase().specification_yaml(base_info, testcase)
```

单接口 YAML 的最外层列表长度通常是 `1`。函数进入：

```python
if len(data) <= 1:
```

假设某个 YAML 有两条 `testCase`，适配过程是：

```python
# safe_load 的原始结果
[
    {
        "baseInfo": base_info,
        "testCase": [testcase_0, testcase_1],
    }
]

# get_testcase_yaml 的适配结果
[
    [base_info, testcase_0],
    [base_info, testcase_1],
]
```

每一个内部小列表代表一组 pytest 参数：

```text
[base_info, testcase_0]
→ test_query_user(base_info, testcase_0)

[base_info, testcase_1]
→ test_query_user(base_info, testcase_1)
```

所以：

> 单接口 YAML 中有几条 `testCase`，对应的测试方法通常就生成并执行几条 Test Item。

注意，`baseInfo`不是请求体；它主要保存接口级的公共信息：

```text
api_name、url、method、header，及可能的 cookies
```

每条用例自己的请求数据通常位于 `testCase`：

```text
params、data、json、files
```

### 3.2 业务 YAML：保留完整 `case_info`

业务文件：

```text
testcase/Business interface/BusinessScenario.yml
```

最外层有 5 个字典，分别代表：

```text
1. 商品列表
2. 商品详情
3. 提交订单
4. 订单支付
5. 校验订单状态
```

原始结构为：

```python
data = [
    {"baseInfo": {...}, "testCase": [...]},
    {"baseInfo": {...}, "testCase": [...]},
    {"baseInfo": {...}, "testCase": [...]},
    {"baseInfo": {...}, "testCase": [...]},
    {"baseInfo": {...}, "testCase": [...]},
]
```

因为：

```python
len(data) == 5
```

函数进入：

```python
else:
    return data
```

它不做 `[base_info, testcase]` 的拆分和重组。

对应的测试写法是单参数化：

```python
@pytest.mark.parametrize(
    'case_info',
    get_testcase_yaml('./testcase/Business interface/BusinessScenario.yml')
)
def test_business_scenario(self, case_info):
    allure.dynamic.title(case_info['baseInfo']['api_name'])
    RequestBase().specification_yaml(case_info)
```

因此每一条 Test Item 拿到的是完整字典：

```python
case_info = {
    "baseInfo": {...},
    "testCase": [...],
}
```

### 3.3 本日探针的真实验证结果

对 `queryUser.yaml`：

```text
safe_load 类型：list
safe_load 外层长度：1
原始第一个元素类型：dict
原始第一个元素的键：['baseInfo', 'testCase']

适配后类型：list
适配后长度：1
适配后第一个元素类型：list
```

适配后第一个元素实际为：

```python
[
    {
        'api_name': '用户查询',
        'url': '/dar/user/queryUser',
        'method': 'POST',
        'header': {...},
    },
    {
        'case_name': '有效查询用户',
        'data': {'user_id': 123839387391912},
        'validation': [...],
    },
]
```

对 `BusinessScenario.yml`：

```text
safe_load 类型：list
safe_load 外层长度：5
原始第一个元素类型：dict
原始第一个元素的键：['baseInfo', 'testCase']

适配后类型：list
适配后长度：5
适配后第一个元素类型：dict
```

这证明：

```text
单接口适配后：list[ list[base_info dict, testcase dict] ]
业务接口适配后：list[ case_info dict ]
```

---

## 四、pytest 收集阶段与执行阶段

参数化表达式写在装饰器里：

```python
@pytest.mark.parametrize(
    'base_info,testcase',
    get_testcase_yaml('...yaml')
)
```

因此 YAML 的读取、`safe_load()`和参数列表生成主要发生在：

```text
pytest 导入测试模块
→ 收集测试
→ 执行参数化表达式
→ 生成 Test Item
```

不是每执行一次测试函数，就重新读取一次 YAML。

例如 `addUser.yaml`中有 6 条 `testCase`：

```text
收集阶段：读取一次 addUser.yaml，生成 6 条 Test Item
执行阶段：test_add_user 以不同参数运行 6 次
```

`pytest --collect-only`会完成收集和参数化，但不会执行 Fixture 函数体、不会登录、不会发接口请求、不会清空 `extract.yaml`。

---

## 五、YAML 空值、字段缺失与字符串的区别

以下写法含义不同：

```yaml
token:           # YAML null
token2: null     # YAML null
token3: ~        # YAML null
token4: ""       # 空字符串
token5: "None"   # 四个字符组成的字符串
```

`safe_load()`后：

```python
{
    "token": None,
    "token2": None,
    "token3": None,
    "token4": "",
    "token5": "None",
}
```

字段完全不存在则不同：

```yaml
username: test01
```

```python
data = {"username": "test01"}
"token" in data  # False
```

要注意：

```python
data.get("token")
```

在“字段不存在”和“字段值是 `None`”时都可能返回 `None`。若要区分，先判断：

```python
if "token" not in data:
    print("字段不存在")
elif data["token"] is None:
    print("字段存在，但值是 None")
```

---

## 六、异常 YAML 的实验与结论

本日使用独立实验函数，让“原始 `safe_load`行为”和“项目函数行为”分开观察：

```python
def inspect_error_yaml(path_str: str) -> None:
    path = Path(path_str)

    try:
        raw_data = yaml.safe_load(
            path.read_text(encoding="utf-8")
        )
        print("safe_load 结果：", raw_data)
        print("safe_load 类型：", type(raw_data).__name__)
    except Exception as error:
        print(type(error).__name__, "-", error)

    result = get_testcase_yaml(str(path))
    print("get_testcase_yaml 返回：", result)
    print("返回类型：", type(result).__name__)
```

### 6.1 文件不存在

测试路径：

```text
testcase/Business interface/Business.yml
```

该文件不存在。

结果：

```text
原始读取：FileNotFoundError
get_testcase_yaml：记录“文件未找到，请检查路径是否正确”
返回值：None
```

对应项目分支：

```python
except FileNotFoundError:
    logs.error(f'[{file}]文件未找到，请检查路径是否正确')
```

### 6.2 空 YAML 文件

空文件不是 YAML 语法错误。

```python
yaml.safe_load(empty_file)
# None
```

当前函数后续执行：

```python
len(data)
```

等价于：

```python
len(None)
```

因此抛出：

```text
TypeError: object of type 'NoneType' has no len()
```

该错误落入宽泛的：

```python
except Exception as e:
```

日志表现为“获取文件数据时出现未知错误”，最终返回：

```python
None
```

### 6.3 YAML 语法错误

测试内容：

```yaml
baseInfo: [unclosed
```

`[`打开了 flow sequence，但没有用 `]`闭合。`safe_load()`抛出：

```text
yaml.parser.ParserError
```

项目函数通过宽泛 `except Exception`捕获该错误，记录解析详情，并最终返回：

```python
None
```

### 6.4 YAML 语法错误、结构错误、值问题

| 类型 | `safe_load()`是否成功 | 示例 | 风险 |
|---|---|---|---|
| YAML 语法错误 | 否 | `baseInfo: [unclosed` | 直接 ParserError |
| YAML 结构不符合项目约定 | 是 | 缺少 `baseInfo`、`testCase`写成 dict | 可能延迟到参数化或请求层失败 |
| YAML 值问题 | 是 | `token:`、`token: ""` | 由业务逻辑决定是否失败 |

例如下面是合法 YAML，但不符合项目预期，因为 `testCase`应该是列表：

```yaml
- baseInfo:
    api_name: 用户查询
  testCase:
    case_name: 查询用户
```

另一个实验中，YAML 文件内容只是：

```yaml
testcase/Business interface/none.yml
```

这是合法 YAML 标量，解析结果为 Python `str`。当前函数只判断：

```python
len(data)
```

字符串长度大于 1 时会直接走：

```python
return data
```

这说明该函数没有验证“解析结果必须是 list”，属于后续可改进的边界问题。

### 6.5 关键结论：日志不是返回值

三个 `except`分支都没有显式 `return`。

因此：

```text
函数写日志
≠ 调用方拿到错误对象
```

Python 函数走到末尾时会隐式返回：

```python
None
```

所以调用方只看返回值时，很难区分：

```text
文件不存在
空文件
YAML 语法错误
编码错误
```

真实错误可能延迟到 pytest 参数化或后续数据访问时才暴露。

---

## 七、运行时状态文件：根目录 `extract.yaml`

### 7.1 真正使用的是哪一个 `extract.yaml`

项目里有同名文件：

```text
根目录/extract.yaml
testcase/extract.yaml
```

不能根据文件名猜测，要根据配置确认。

`conf/setting.py`：

```python
DIR_BASE = os.path.dirname(os.path.dirname(__file__))

FILE_PATH = {
    ...
    'EXTRACT': os.path.join(DIR_BASE, 'extract.yaml'),
    ...
}
```

因此运行时真正读写的是：

```text
项目根目录/extract.yaml
```

`testcase/extract.yaml`不会因为同名而自动成为运行时状态文件。

### 7.2 `write_yaml_data()`：追加写入

核心实现：

```python
file_path = FILE_PATH['EXTRACT']
os.makedirs(os.path.dirname(file_path), exist_ok=True)
file = open(file_path, 'a', encoding='utf-8')

if isinstance(value, dict):
    write_data = yaml.dump(value, allow_unicode=True, sort_keys=False)
    file.write(write_data)
```

含义：

```text
os.makedirs：确保父目录存在
"a"：追加模式；文件不存在时也会创建
yaml.dump：把 Python dict 转回 YAML 文本
finally：无论成功失败，都尝试关闭文件
```

它只允许写入字典。非字典时只记录日志：

```text
写入 extract.yaml 的数据必须为 dict 格式
```

### 7.3 追加写带来的重复键问题

假设先写：

```yaml
orderNumber: ORDER-A
```

后写：

```yaml
orderNumber: ORDER-B
```

文件文本可能变成：

```yaml
orderNumber: ORDER-A
orderNumber: ORDER-B
```

当前 PyYAML 读取时，实际会以最后一次同名键的值为准。这意味着：

```text
文件保留了多次写入痕迹
读取者通常只得到最后一次写入的数据
```

旧值没有测试名、业务链路 ID 或生命周期信息，容易造成数据污染。

### 7.4 `clear_yaml_data()`：清空内容，不删除文件

实现：

```python
with open(FILE_PATH['EXTRACT'], 'w') as f:
    f.truncate()
```

`"w"`打开文件时本身就会截断原内容；`truncate()`是 Python 文件对象的内置方法，进一步确保文件内容被截断。最终效果是：

```text
extract.yaml 文件仍然存在
extract.yaml 旧内容被清空
```

### 7.5 `get_extract_yaml()`：读取动态变量

调用形式：

```python
get_extract_yaml(node_name)
get_extract_yaml(node_name, second_node_name)
```

内部先读取根目录状态文件：

```python
ext_data = yaml.safe_load(rf)
```

再返回：

```python
ext_data[node_name]
```

或：

```python
ext_data[node_name][second_node_name]
```

若状态文件不存在，函数会创建空文件；若 key 不存在、文件为空或 YAML 解析失败，异常被捕获并记录日志。

---

## 八、业务场景中的“读取、写入、生成”三类动态数据

`BusinessScenario.yml` 中的 `${...}`都属于动态占位符，但不代表它们都从 `extract.yaml`读取。

当前项目在请求执行前会识别：

```text
${函数名(参数)}
```

再调用 `DebugTalk`中对应的函数。数据来源由函数名决定。

### 8.1 从 `extract.yaml`读取

| 占位符 | 含义 |
|---|---|
| `${get_extract_data(token)}` | 读取登录后保存的 Token |
| `${get_extract_data(goodsIds,1)}` | 读取商品 ID 列表中的指定商品 |
| `${get_extract_data(orderNumber)}` | 读取下单后保存的订单号 |
| `${get_extract_data(userId)}` | 读取下单后保存的用户 ID |

例如业务 YAML 的商品列表请求头中：

```yaml
token: ${get_extract_data(token)}
```

在 YAML 解析阶段它还只是普通字符串；只有请求执行阶段才会被替换为实际 Token。

### 8.2 从响应中提取并写入 `extract.yaml`

`extract`和`extract_list`不是读取规则，而是写入规则。

商品列表：

```yaml
extract_list:
  goodsIds: $.goodsList[*].goodsId
```

含义：

```text
商品列表响应
→ JSONPath提取所有 goodsId
→ 写入 root/extract.yaml 的 goodsIds
```

提交订单：

```yaml
extract:
  orderNumber: $.orderNumber
  userId: $.userId
```

含义：

```text
下单响应
→ 提取订单号和用户 ID
→ 写入 root/extract.yaml
```

### 8.3 运行时生成，但不读取状态文件

```yaml
timeStamp: ${timestamp()}
```

这里调用时间戳函数，按当前时间生成值，不读取 `extract.yaml`。

### 8.4 五个业务步骤的完整数据链

```text
自动登录
  ↓ 写入 token（及可能的 Cookie 数据）
商品列表
  ↓ 读取 token
  ↓ 写入 goodsIds
商品详情
  ↓ 读取 goodsIds
提交订单
  ↓ 读取 goodsIds
  ↓ 写入 orderNumber、userId
订单支付
  ↓ 读取 orderNumber、userId
  ↓ 生成 timestamp
校验订单状态
  ↓ 读取 orderNumber
  ↓ 生成 timestamp
```

因此：

> 业务 YAML 从 pytest 角度生成 5 条 Test Item；从业务数据角度，它们是彼此依赖的一条“商品查询 → 下单 → 支付 → 状态校验”链路。

---

## 九、两个 `conftest.py` 与 Fixture 生命周期

### 9.1 pytest 如何使用 `conftest.py`

项目有两个：

```text
根目录/conftest.py
testcase/conftest.py
```

它们不需要被测试文件显式 import。pytest 会根据测试文件所在目录，加载目录层级上可用的 `conftest.py`。

```text
根目录 conftest.py
→ 对根目录及其子目录的测试可用

testcase/conftest.py
→ 对 testcase 目录及其子目录的测试可用
```

因此 `testcase/...`下的测试通常同时使用两份文件中的 Fixture。

### 9.2 根目录的 session Fixture

```python
@pytest.fixture(scope="session", autouse=True)
def clear_extract():
    yfd.clear_yaml_data()
    remove_file("./report/temp", ['json', 'txt', 'attach', 'properties'])
```

含义：

```text
scope="session"：一次 pytest 测试会话中通常只执行一次
autouse=True：测试函数不需要手工声明该 Fixture
```

真正执行测试时，它会：

```text
清空根 extract.yaml
→ 清理 report/temp 目录中指定后缀的报告临时文件
```

注意：

```text
pytest --collect-only 会收集测试并读取参数化 YAML
但不会执行 Fixture 函数体
```

所以收集测试时不会自动登录、不会清空状态文件、不会发请求。

### 9.3 pytest 测试结束 Hook

根目录中还有 pytest 固定 Hook：

```python
def pytest_terminal_summary(terminalreporter, exitstatus, config):
```

它在测试会话结束时调用：

```python
generate_test_summary(terminalreporter)
```

汇总：

```text
测试总数、通过数、失败数、错误数、跳过数、执行时长
```

若 `conf/setting.py`中的：

```python
dd_msg = True
```

才会进一步调用钉钉发送函数。当前配置是：

```python
dd_msg = False
```

因此只打印摘要，不发送钉钉消息。

### 9.4 `testcase/conftest.py`中的 Fixture

函数级自动 Fixture：

```python
@pytest.fixture(autouse=True)
def start_test_and_end():
    logs.info('-------------接口测试开始--------------')
    yield
    logs.info('-------------接口测试结束--------------')
```

默认 `scope`是 `function`，因此每条测试前后各执行一次：

```text
测试前打印“接口测试开始”
→ 执行测试
→ 测试后打印“接口测试结束”
```

登录 Fixture：

```python
@pytest.fixture(scope='session', autouse=True)
def system_login():
    api_info = get_testcase_yaml('./data/loginName.yaml')
    RequestBase().specification_yaml(api_info[0][0], api_info[0][1])
```

它读取登录 YAML，并从适配后的第一组参数中取：

```python
api_info[0][0]  # login base_info
api_info[0][1]  # login testcase
```

然后执行登录请求。登录响应中的提取规则会把 Token 等运行时数据写入根目录 `extract.yaml`。

数据库 Fixture：

```python
@pytest.fixture(scope='session', autouse=True)
def datadb_init():
    pass
```

当前被标记为自动执行，但函数体没有实际初始化或清理数据库。

### 9.5 一个需要记录的已有问题

登录失败时当前代码：

```python
except Exception as e:
    logs.error(...)
    exit()
```

`exit()`会直接终止 pytest 进程，不利于：

```text
生成标准失败报告
执行其他清理逻辑
区分错误、失败和跳过
```

该问题今天只记录，后续异常治理阶段再修复。

---

## 十、报告临时文件清理：`base/removefile.py`

### 10.1 `remove_file(filepath, endlst)`

根目录 Fixture 调用：

```python
remove_file(
    "./report/temp",
    ['json', 'txt', 'attach', 'properties']
)
```

该函数的实际行为：

```text
目录存在
→ os.listdir() 获取该目录第一层文件名称
→ 拼接完整路径
→ 判断名称是否以指定后缀结尾
→ os.remove() 删除匹配文件
```

要点：

- `filepath`在当前调用中是目录，而不是单个文件。
- 若目录不存在，`os.makedirs(filepath)`创建的是目录。
- `endlst`必须为 list；若不是 list，会抛 `TypeError`，但外层 `except`又会把它记录为日志而不是向调用方抛出。
- 它只遍历当前目录第一层，不递归删除子目录内容。

### 10.2 `remove_directory(path)`名称与实现不一致

函数实现：

```python
def remove_directory(path):
    if os.path.exists(path):
        os.remove(path)
```

`os.remove()`主要用于删除文件，不适合删除目录。因此：

```text
路径是文件：通常可删除
路径是目录：通常报错并记录日志
```

函数名看起来像“删除目录”，实际不具备可靠删除目录的能力。这是一个命名与行为不一致的问题。

---

## 十一、为什么当前框架能串行跑，但不适合并行跑

### 11.1 串行执行

串行意味着：

```text
上一个测试结束
→ 下一个测试才开始
```

若业务步骤按预期顺序执行：

```text
登录写 token
→ 商品列表读 token、写 goodsIds
→ 商品详情读 goodsIds
→ 下单读 goodsIds、写订单号和用户 ID
→ 支付读订单号和用户 ID
→ 状态校验读订单号
```

前一个步骤写入后，下一个步骤才读取，因此共享文件暂时可以传递数据。

### 11.2 并行执行

并行意味着多个 worker 同时执行不同 Test Item，例如：

```text
worker-1：商品列表
worker-2：提交订单
```

未来可能通过：

```powershell
pytest -n 2
```

启动多个 worker。

当前设计的风险如下。

#### 风险一：数据尚未写入就被读取

```text
worker-1：商品列表尚未完成，goodsIds尚未写入
worker-2：提交订单先读取goodsIds
→ 读取失败
```

#### 风险二：两条链路互相覆盖

```text
worker-1：写 goodsIds = ["A100"]
worker-2：写 goodsIds = ["B200"]
worker-1：读取 goodsIds
→ 可能读到 B200，而不是 A100
```

请求甚至可能成功，但操作的是另一个测试的数据，这比直接报错更难定位。

#### 风险三：多个 worker 同时清空状态文件

每个 worker 都可能执行自己的 session Fixture：

```text
worker-1：登录成功，写入 token
worker-2：启动时执行 clear_yaml_data，清空文件
worker-1：读取 token
→ Token 丢失
```

#### 风险四：追加写导致重复键和竞争

多个测试同时追加同名 `orderNumber`、`userId`，最终读取者通常只取得最后一次写入的数据。

### 11.3 正确结论

```text
pytest层面：业务 YAML 生成 5 条 Test Item
业务层面：这 5 条并不独立，而是一条有前后依赖的业务链路

当前框架：依赖全局共享 extract.yaml
结论：可以在受控串行顺序下作为基线运行；不适合直接并行执行
```

后续数据隔离阶段的改进方向包括：

```text
Fixture 直接传递业务数据
每条测试独立的上下文对象
每个 worker 独立状态文件
使用唯一测试数据
避免测试间依赖执行顺序
```

今天不实施这些改造，只保留问题、现象和证据。

---

## 十二、算法：BFS 队列模板

本日算法目标是从前面学习的递归 DFS，切换到按层处理的 BFS。

### 12.1 DFS 递归与 BFS 层序遍历的关系

它们都是树遍历，但决定“下一个访问谁”的方式不同：

| 方式 | 核心容器 | 特点 | 常见空间 |
|---|---|---|---|
| DFS 递归 | 调用栈 | 一路向下，无法继续时回退 | `O(h)` |
| BFS 层序 | 队列 | 先处理同层，再处理下一层 | `O(w)` |

其中：

```text
h：树高
w：树的最大宽度
```

例如：

```text
      1
     / \
    2   3
   /
  4
```

前序 DFS：

```text
1 → 2 → 4 → 3
```

层序 BFS：

```text
1 → 2 → 3 → 4
```

递归调用栈是后进先出（LIFO），会优先继续深入节点 `2`的孩子 `4`；队列是先进先出（FIFO），节点 `3`比节点 `4`更早入队，因此先处理 `3`，从而保证层序。

### 12.2 `deque`的作用

```python
from collections import deque
```

`deque`是 double-ended queue（双端队列）类，不是普通函数。调用：

```python
queue = deque([root])
```

是在创建一个队列对象，并让根节点先入队。

层序遍历只使用：

```python
queue.append(node)      # 从右侧进入队尾
queue.popleft()         # 从左侧取出最早进入的节点
```

这形成 FIFO：

```text
First In, First Out
先进先出
```

不使用：

```python
list.pop(0)
```

因为列表头部删除需要移动后续元素；`deque.popleft()`是适合队列的 `O(1)`操作。

### 12.3 LC 102：二叉树的层序遍历

题目要求按层返回节点值：

```text
输入：[3,9,20,null,null,15,7]
输出：[[3],[9,20],[15,7]]
```

标准实现：

```python
from collections import deque
from typing import List, Optional


class Solution:
    def levelOrder(
        self,
        root: Optional[TreeNode]
    ) -> List[List[int]]:
        if root is None:
            return []

        result = []
        queue = deque([root])

        while queue:
            level_size = len(queue)
            level = []

            for _ in range(level_size):
                node = queue.popleft()
                level.append(node.val)

                if node.left:
                    queue.append(node.left)

                if node.right:
                    queue.append(node.right)

            result.append(level)

        return result
```

三个容器的职责：

```text
queue：尚未处理的 TreeNode 对象
level：当前层已经取出的节点值
result：每一层的 level 组成的最终二维列表
```

最关键的一行：

```python
level_size = len(queue)
```

它必须在内层 `for`前执行。

原因：处理当前层时会把孩子节点加入队列。若不预先固定当前层数量，下一层孩子会被错误地当成当前层继续处理。

例如：

```text
当前 queue = [9, 20]
level_size = 2

处理9、20期间，15、7入队
queue 最后变为 [15, 7]

内层循环仍只执行2次
→ 15、7留给下一轮处理
```

### 12.4 LC 637：二叉树的层平均值

题目要求每层只返回一个平均值：

```text
输入：[3,9,20,null,null,15,7]
输出：[3.0,14.5,11.0]
```

它复用 LC 102 的队列、逐层循环和子节点入队逻辑；变化只在“每层如何聚合结果”。

当前学习版写法：

```python
from collections import deque
from typing import List, Optional


class Solution:
    def averageOfLevels(
        self,
        root: Optional[TreeNode]
    ) -> List[float]:
        if root is None:
            return []

        result = []
        queue = deque([root])

        while queue:
            level_size = len(queue)
            level = []

            for _ in range(level_size):
                node = queue.popleft()
                level.append(node.val)

                if node.left:
                    queue.append(node.left)

                if node.right:
                    queue.append(node.right)

            result.append(sum(level) / level_size)

        return result
```

`sum()`可以直接对数值列表求和：

```python
sum([9, 20])
# 29
```

但不能对字符串、`None`或 `TreeNode`对象直接求和。因此这里必须添加：

```python
node.val
```

而不是添加整个 `node`。

当只需要平均值时，不必保存完整 `level`列表，可以优化为：

```python
level_sum = 0

for _ in range(level_size):
    node = queue.popleft()
    level_sum += node.val
    ...

result.append(level_sum / level_size)
```

这不会改变 BFS 的核心结构。

### 12.5 两题复杂度

设：

```text
n：节点总数
h：树高
w：树最大宽度
```

| 题目 | 时间复杂度 | 队列辅助空间 | 输出空间 |
|---|---|---|---|
| LC 102 层序遍历 | `O(n)` | `O(w)` | `O(n)` |
| LC 637 层平均值 | `O(n)` | `O(w)` | `O(h)` |

时间都是 `O(n)`，因为每个节点只会入队、出队、处理一次。

LC 637 中的：

```python
sum(level)
```

不会让时间变成 `O(n²)`。各层节点数量相加仍是 `n`：

```text
第1层求和的节点数
+ 第2层求和的节点数
+ ...
= 全树节点数 n
```

与此前递归题对比：

```text
递归 DFS：辅助空间通常写 O(h)，来自调用栈
BFS 队列：辅助空间通常写 O(w)，来自最大宽度的队列
```

最坏情况下，`h`或 `w`都可能达到 `O(n)`，但它们描述的是不同的树形特征。

---

## 十三、今日已确认的问题与后续处理阶段

| 编号 | 已确认现象 | 风险 | 暂不修改原因 |
|---|---|---|---|
| Y-01 | 空 YAML 得到 `None`后执行 `len(None)` | 错误信息不清晰 | Day 41 先验证行为 |
| Y-02 | 合法字符串 YAML 可能被直接 `return data` | 不符合预期类型的数据延迟失败 | 后续增加输入校验 |
| Y-03 | 异常分支只写日志，最终多为 `None` | 调用方无法可靠区分错误类型 | 后续异常治理 |
| S-01 | `extract.yaml`追加同名键 | 状态污染、最后写入覆盖语义 | 后续数据隔离 |
| S-02 | 业务步骤依赖共享文件和顺序 | 单独运行、乱序、并行时不稳定 | 后续 Fixture/Client 重构 |
| F-01 | 登录失败调用 `exit()` | pytest 报告和清理可能被中断 | 后续异常治理 |
| C-01 | `remove_directory()`用 `os.remove()` | 名称与实际能力不一致 | 后续代码质量整理 |

---

## 十四、今日口述复盘模板

### 14.1 30 秒版本

> 当前项目先用 `yaml.safe_load()`把 YAML 文本转成 Python 对象。单接口 YAML 最外层只有一个接口块，`get_testcase_yaml()`会把公共 `baseInfo`和每条 `testCase`整理成 `[base_info, testcase]`，供 pytest 双参数化；业务 YAML 最外层有五个步骤字典，因此原样返回为五个 `case_info`。业务步骤通过根目录共享 `extract.yaml`传递 Token、商品 ID、订单号和用户 ID，串行时依赖前写后读，不能直接并行。算法部分用 `deque`实现 BFS，逐层处理队列，LC 102收集每层节点值，LC 637把每层数值求平均。

### 14.2 三分钟版本的回答顺序

```text
1. YAML文本和safe_load后的Python对象不同。
2. 单接口YAML与业务YAML的外层结构不同。
3. get_testcase_yaml根据外层长度返回不同的pytest参数形状。
4. 参数化在pytest收集阶段发生，不是每次测试执行时读取YAML。
5. 文件不存在、空YAML、语法错误的异常处理和None返回值。
6. FILE_PATH['EXTRACT']确认实际使用根目录extract.yaml。
7. extract、extract_list负责从响应写入；get_extract_data负责读取。
8. 两份conftest.py的作用范围、session与function Fixture。
9. 为什么共享文件可串行、不可安全并行。
10. BFS队列模板、level_size和两道算法题的差异。
```

---

## 十五、实验文件与提交建议

本日学习过程中创建或使用：

```text
day41_yaml_probe.py
testcase/Business interface/none.yml
testcase/Business interface/noneerror.yml
```

它们用于学习和异常验证，不是正式业务测试数据。

在准备提交代码前，应当：

```text
1. 把实验结论保留在本文档中；
2. 删除实验错误 YAML，或移至明确的临时学习目录；
3. 决定是否保留探针脚本；若保留，建议改成清晰的学习工具并补充用途说明；
4. 确认 git diff 中只有希望提交的学习成果。
```

不应把故意非法的 YAML 混入正式业务用例目录并提交。

---

## 十六、明日衔接：Day 42 请求执行主链

下一阶段进入：

```text
YAML
→ RequestBase.specification_yaml()
→ replace_load()
→ SendRequest.run_main()
→ requests.Session.request()
→ Response
```

明天重点回答：

```text
baseInfo中的URL、Header、Method如何变成真实请求？
params、data、json分别如何进入requests？
${...} 动态占位符在哪一步被替换？
请求失败、超时、TLS错误如何表现？
为什么pop()修改原始测试数据有副作用？
```

Day 41 已经建立了理解 Day 42 的前提：只有先区分“YAML 原始结构、pytest 参数对象、extract运行时状态”，才能继续追踪请求执行链。
