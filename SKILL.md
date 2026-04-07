---
name: medical-tender-scraper
description: 医疗器械招投标信息搜集工具。从中国政府采购网等平台抓取医疗器械相关招标信息，输出为Excel表格。Use when: (1) 需要搜集医疗器械招标信息，(2) 需要监控特定医疗设备的采购公告，(3) 需要导出招标信息到Excel，(4) 需要定期获取招标信息更新。
---

# 医疗器械招投标信息搜集工具

从中国政府采购网抓取医疗器械相关招标信息，支持关键词搜索、多字段提取、Excel导出。

## 功能特性

- **关键词搜索**：支持自定义关键词（如"眼科"、"激光"等）
- **时间范围**：可指定搜索最近N天的招标信息
- **多字段提取**：提取13个字段（标题、日期、省份、采购单位、预算、标的物、联系人等）
- **Excel导出**：支持单工作表和多工作表格式
- **自动命名**：输出文件自动带上日期（medical_tenders_YYYYMMDD.xlsx）

## 使用方法

### 命令行运行

```bash
# 基本使用（默认搜索"眼科"，最近7天）
python run.py

# 指定关键词
python run.py -k 眼科

# 指定多个关键词
python run.py -k 眼科 激光 显微镜

# 指定时间范围（最近14天）
python run.py -d 14

# 指定最大结果数
python run.py --max-results 50

# 多工作表导出
python run.py --multi-sheet

# 完整示例
python run.py -k 眼科 -d 7 --max-results 50 --multi-sheet -v
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-k, --keywords` | 搜索关键词列表 | ["眼科"] |
| `-d, --days` | 搜索最近N天 | 7 |
| `-o, --output` | 输出文件名 | 自动生成 |
| `--max-results` | 每个关键词最大结果数 | 100 |
| `--multi-sheet` | 使用多工作表格式 | False |
| `-v, --verbose` | 显示详细输出 | False |

## 输出字段

1. **关键词** - 搜索使用的关键词
2. **标题** - 招标公告标题
3. **发布日期** - 公告发布日期（YYYY-MM-DD格式）
4. **公告类型** - 公开招标、中标公告、询价公告等
5. **省份** - 招标所在省份
6. **采购单位** - 采购人/采购单位名称
7. **代理机构** - 招标代理机构
8. **预算金额** - 项目预算（如有标注）
9. **标的物** - 采购的医疗设备名称
10. **联系人** - 项目联系人姓名
11. **联系电话** - 联系人电话
12. **联系地址** - 联系地址
13. **URL** - 公告详情页链接

## 项目结构

```
medical-tender-scraper/
├── SKILL.md                    # 本文件
├── src/
│   ├── config.py              # 配置管理
│   ├── main.py                # 主入口
│   ├── http_client.py         # HTTP客户端
│   ├── fetchers/
│   │   └── ccgp_fetcher.py   # 中国政府采购网抓取器
│   └── exporters/
│       └── excel_exporter.py # Excel导出器
├── scripts/                    # 可执行脚本
│   └── run.py                 # 运行脚本（入口）
└── requirements.txt           # Python依赖
```

## 依赖安装

```bash
pip install -r requirements.txt
```

依赖包：
- httpx >= 0.24.0
- beautifulsoup4 >= 4.12.0
- pydantic >= 2.0.0
- pandas >= 2.0.0
- openpyxl >= 3.1.0

## 注意事项

1. **请求频率**：程序会自动控制请求频率（每页间隔1.5秒），避免对服务器造成压力
2. **编码问题**：Windows控制台可能显示乱码，但不影响Excel文件内容
3. **预算金额**：只有部分招标信息标注了预算，未标注的显示为空
4. **数据来源**：目前仅支持中国政府采购网（ccgp.gov.cn）

## 扩展开发

### 添加新的数据源

1. 在 `src/fetchers/` 下创建新的抓取器（如 `xxx_fetcher.py`）
2. 实现 `search()` 和 `parse_list_page()` 方法
3. 在 `main.py` 中添加对新抓取器的调用

### 添加新的提取字段

1. 在 `src/fetchers/ccgp_fetcher.py` 的 `TenderInfo` 数据类中添加新字段
2. 在 `_fetch_detail_info()` 方法中添加提取逻辑
3. 在 `src/exporters/excel_exporter.py` 中添加导出列

## 定时任务配置

使用cron配置每周四上午10:00自动运行：

```bash
openclaw cron add \
  --name "每周眼科招标采集" \
  --schedule "0 10 * * 4" \
  --command "python skills/medical-tender-scraper/scripts/run.py -k 眼科 -d 7"
```
