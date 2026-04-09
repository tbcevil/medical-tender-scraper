# 医疗器械招投标信息搜集工具

从中国政府采购网抓取医疗器械相关招标信息的MVP版本。

## 功能特性

- 🔍 支持多关键词搜索（默认：眼科、皮肤科）
- 📅 可配置时间范围（默认：最近7天）
- 📊 导出为格式化的Excel文件
- 🏷️ 自动去重和关键词标记
- 📈 包含汇总统计信息
- 🖥️ 命令行界面，易于使用
- 🔄 **智能重试机制** - 每页最多重试3次，自动处理网络超时
- 📄 **获取所有结果** - 支持 `--all` 参数获取全部招标信息

## 项目结构

```
skills/medical-tender-scraper/
├── src/
│   ├── __init__.py
│   ├── config.py              # 配置模块 (Pydantic)
│   ├── http_client.py         # HTTP客户端 (httpx)
│   ├── parser.py              # HTML解析器 (BeautifulSoup)
│   ├── main.py                # 主程序
│   ├── fetchers/
│   │   ├── __init__.py
│   │   └── ccgp_fetcher.py    # 中国政府采购网抓取器
│   └── exporters/
│       ├── __init__.py
│       └── excel_exporter.py  # Excel导出器
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_http_client.py
│   ├── test_parser.py
│   ├── test_ccgp_fetcher.py
│   ├── test_excel_exporter.py
│   └── test_main.py
├── docs/
├── run.py                     # 运行入口
├── requirements.txt           # 依赖列表
└── README.md                  # 项目说明
```

## 安装

### 1. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本使用

```bash
python run.py
```

### 命令行参数

```bash
python run.py -h
```

常用参数：

```bash
# 指定关键词
python run.py -k 眼科 皮肤科 口腔科

# 指定时间范围（最近14天）
python run.py -d 14

# 指定输出文件
python run.py -o my_tenders.xlsx

# 按关键词分多个工作表导出
python run.py --multi-sheet

# 显示详细输出
python run.py -v

# 获取所有结果（不限制数量）
python run.py --all

# 组合使用
python run.py -k 眼科 -d 30 -o 眼科招标.xlsx -v
```

### 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| --keywords | -k | 搜索关键词列表 | 眼科 |
| --days | -d | 搜索最近多少天 | 7 |
| --output | -o | 输出文件路径 | medical_tenders_时间戳.xlsx |
| --max-results | | 每个关键词最大结果数，0表示全部 | 100 |
| --all | | 获取所有结果（等同于 --max-results 0） | False |
| --multi-sheet | | 按关键词分多个工作表 | False |
| --verbose | -v | 显示详细输出 | False |

## 配置说明

可以通过修改 `src/config.py` 中的 `TenderConfig` 类来自定义默认配置：

```python
config = TenderConfig(
    base_url="http://www.ccgp.gov.cn",
    keywords=["眼科", "皮肤科"],
    days_back=7,
    timeout=30,
    max_results=100,
    output_file="medical_tenders.xlsx"
)
```

## 测试

### 运行所有测试

```bash
pytest
```

### 运行特定测试

```bash
pytest tests/test_config.py
pytest tests/test_parser.py
```

### 生成测试报告

```bash
pytest --cov=src --cov-report=html
```

## 注意事项

1. **请求频率**：工具内置了1.5秒的请求间隔，避免对目标网站造成压力
2. **网络环境**：确保网络可以访问中国政府采购网 (ccgp.gov.cn)
3. **编码问题**：工具会自动检测和转换页面编码
4. **数据去重**：相同URL的招标信息会自动去重
5. **重试机制**：每页请求失败时会自动重试，最多3次，等待时间递增（2秒→4秒→6秒）
6. **分页获取**：网站每页显示20条结果，工具会自动获取多页直到达到限制或获取全部

## 开发计划

- [x] 配置模块 (Pydantic)
- [x] HTTP客户端 (httpx)
- [x] HTML解析器 (BeautifulSoup)
- [x] 中国政府采购网抓取器
- [x] Excel导出器 (pandas + openpyxl)
- [x] 主程序和命令行界面
- [x] 单元测试
- [x] 实际抓取测试
- [x] 智能重试机制
- [x] 获取所有结果功能
- [ ] 定时任务支持
- [ ] 数据库存储
- [ ] Web界面

## 许可证

MIT License
