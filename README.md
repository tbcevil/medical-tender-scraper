# 医疗器械招投标信息搜集工具

从中国政府采购网(CCGP)和全国公共资源交易平台(GGZY)抓取医疗器械相关招标信息。

## 功能特性

- 🔍 支持多关键词搜索（默认：眼科）
- 📅 可配置时间范围（默认：最近7天）
- 📊 导出为格式化的Excel文件
- 🏷️ 自动去重和关键词标记
- 📈 包含汇总统计信息
- 🖥️ 命令行界面，易于使用
- 🔄 **智能重试机制** - 每页最多重试3次，自动处理网络超时
- 📄 **获取所有结果** - 支持 `--all` 参数获取全部招标信息
- 🌐 **双平台支持** - 同时支持CCGP和GGZY两个平台
- 📑 **多Sheet导出** - CCGP和GGZY数据分别导出到不同Sheet

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
│   │   ├── ccgp_fetcher.py    # 中国政府采购网抓取器
│   │   ├── ggzy_fetcher.py    # 全国公共资源交易平台抓取器
│   │   └── ggzy_fetcher_playwright.py  # GGZY Playwright版本
│   └── exporters/
│       ├── __init__.py
│       └── excel_exporter.py  # Excel导出器
├── scripts/
│   ├── run.py                 # CCGP运行入口
│   ├── run_ggzy.py            # GGZY运行入口
│   └── run_combined.py        # 合并运行入口
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_http_client.py
│   ├── test_parser.py
│   ├── test_ccgp_fetcher.py
│   ├── test_excel_exporter.py
│   └── test_main.py
├── docs/
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

### 1. 合并抓取（推荐）

同时抓取CCGP和GGZY两个平台：

```bash
python scripts/run_combined.py -k 眼科
```

### 2. 单独抓取CCGP

```bash
python scripts/run.py -k 眼科
```

### 3. 单独抓取GGZY

```bash
# 需要先安装Playwright
pip install playwright
playwright install chromium

python scripts/run_ggzy.py -k 眼科
```

### 常用参数

```bash
# 指定关键词
python scripts/run_combined.py -k 眼科 激光 显微镜

# 指定时间范围（最近7天，仅CCGP）
python scripts/run_combined.py -d 7

# 指定输出文件
python scripts/run_combined.py -o my_tenders.xlsx

# 指定最大结果数
python scripts/run_combined.py --max-results 50

# 获取所有结果
python scripts/run_combined.py --all

# 只抓取CCGP
python scripts/run_combined.py --ccgp-only

# 只抓取GGZY
python scripts/run_combined.py --ggzy-only

# 显示详细输出
python scripts/run_combined.py -v

# 组合使用
python scripts/run_combined.py -k 眼科 -d 7 --max-results 50 -v
```

### 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| --keywords | -k | 搜索关键词列表 | 眼科 |
| --days | -d | 搜索最近多少天（仅CCGP） | 7 |
| --output | -o | 输出文件路径 | combined_tenders_时间戳.xlsx |
| --max-results | | 每个关键词最大结果数，0表示全部 | 20 |
| --all | | 获取所有结果（等同于 --max-results 0） | False |
| --ccgp-only | | 只抓取CCGP数据 | False |
| --ggzy-only | | 只抓取GGZY数据 | False |
| --verbose | -v | 显示详细输出 | False |

### 数据源说明

| 平台 | 网址 | 特点 | 技术方案 |
|------|------|------|----------|
| CCGP | ccgp.gov.cn | 政府采购信息 | 标准HTTP请求 |
| GGZY | ggzy.gov.cn | 公共资源交易（含工程、采购等） | Playwright浏览器自动化 |

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
2. **网络环境**：确保网络可以访问中国政府采购网 (ccgp.gov.cn) 和全国公共资源交易平台 (ggzy.gov.cn)
3. **编码问题**：工具会自动检测和转换页面编码
4. **数据去重**：相同URL的招标信息会自动去重
5. **重试机制**：每页请求失败时会自动重试，最多3次，等待时间递增（2秒→4秒→6秒）
6. **分页获取**：网站每页显示20条结果，工具会自动获取多页直到达到限制或获取全部
7. **GGZY依赖**：GGZY抓取需要安装Playwright和Chromium浏览器
8. **字段差异**：CCGP和GGZY的字段覆盖程度可能不同，部分字段在某些平台可能为空

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
- [x] 定时任务支持
- [ ] 数据库存储
- [ ] Web界面

## 定时任务配置

工具支持通过OpenClaw Cron设置定时自动采集任务。

### 当前配置
- **任务名称**: 每周眼科/皮肤科招标采集
- **运行时间**: 每周四上午10:00
- **超时时间**: 900秒（15分钟）
- **采集关键词**: 眼科、皮肤科
- **时间范围**: 近7天
- **数据数量**: 全部（--all）
- **执行方式**: 依次执行两个任务并汇总结果

### 手动配置定时任务
```bash
# 添加每周定时任务（周四上午10点）
openclaw cron add \
  --name "每周招标采集" \
  --schedule "0 10 * * 4" \
  --message "python scripts/run_combined.py -k 眼科 -d 7 --all -v" \
  --timeout 900
```

## 更新日志

### v1.5 (2026-04-15)
- 添加定时任务支持，支持自动每周采集
- 支持多关键词定时采集（眼科、皮肤科）
- 优化GGZY翻页功能，修复分页按钮选择逻辑
- 更新文档，添加定时任务配置说明

### v1.4 (2026-04-10)
- 修复GGZY搜索URL参数，使用正确的FINDTXT接口
- 添加DEAL_TIME时间范围参数支持（01-05对应不同时间范围）
- 修复GGZY详情页信息提取，正确获取采购单位、联系人、电话、地址
- 修复GGZY翻页功能，支持JavaScript翻页
- 优化GGZY搜索结果相关性，确保与关键词匹配

### v1.3 (2026-04-09)
- 添加全国公共资源交易平台(GGZY)抓取器
- 支持CCGP和GGZY双平台同时抓取
- 导出Excel包含两个Sheet（CCGP和GGZY）
- 添加合并运行脚本 `run_combined.py`

### v1.2 (2026-04-09)
- 增强标的物无效内容过滤
- 修复"首页政采法规..."等导航文字被误提取的问题
- 添加导航关键词组合检测

### v1.1 (2026-04-09)
- 修复分页解析问题，支持获取多页结果
- 添加智能重试机制（每页最多3次重试）
- 添加 `--all` 参数支持获取所有结果
- 优化 verbose 输出信息

### v1.0 (2026-04-07)
- 完成MVP版本开发
- 实现中国政府采购网抓取
- 13个字段完整提取
- Excel导出功能

## 许可证

MIT License
