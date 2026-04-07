# 医疗器械招投标信息搜集工具 - 使用指南

> 版本：v1.0  
> 更新日期：2026-04-07

---

## 目录

1. [快速开始](#快速开始)
2. [安装方法](#安装方法)
3. [命令行使用](#命令行使用)
4. [Python代码调用](#python代码调用)
5. [定时任务配置](#定时任务配置)
6. [输出文件说明](#输出文件说明)
7. [常见问题](#常见问题)
8. [高级用法](#高级用法)

---

## 快速开始

### 最简单的使用方式

```bash
# 进入Skill目录
cd ~/.stepclaw/skills/medical-tender-scraper

# 运行（默认搜索"眼科"，最近7天）
python scripts/run.py
```

运行后会在当前目录生成Excel文件，如：`medical_tenders_20260407.xlsx`

---

## 安装方法

### 1. 依赖安装

```bash
cd ~/.stepclaw/skills/medical-tender-scraper
pip install -r requirements.txt
```

依赖包：
- httpx >= 0.24.0
- beautifulsoup4 >= 4.12.0
- pydantic >= 2.0.0
- pandas >= 2.0.0
- openpyxl >= 3.1.0

### 2. 验证安装

```bash
python scripts/run.py --help
```

---

## 命令行使用

### 基本命令格式

```bash
python scripts/run.py [选项]
```

### 命令行参数

| 参数 | 短格式 | 说明 | 默认值 | 示例 |
|------|--------|------|--------|------|
| `--keywords` | `-k` | 搜索关键词列表 | ["眼科"] | `-k 眼科 激光` |
| `--days` | `-d` | 搜索最近N天 | 7 | `-d 14` |
| `--output` | `-o` | 输出文件名 | 自动生成 | `-o output.xlsx` |
| `--max-results` | - | 每个关键词最大结果数 | 100 | `--max-results 50` |
| `--multi-sheet` | - | 多工作表格式 | False | `--multi-sheet` |
| `--verbose` | `-v` | 详细输出 | False | `-v` |

### 常用命令示例

#### 示例1：搜索单个关键词

```bash
python scripts/run.py -k 眼科
```

#### 示例2：搜索多个关键词

```bash
python scripts/run.py -k 眼科 激光 显微镜
```

#### 示例3：指定时间范围

```bash
# 搜索最近14天
python scripts/run.py -d 14

# 搜索最近30天
python scripts/run.py -d 30
```

#### 示例4：限制结果数量

```bash
# 每个关键词最多50条
python scripts/run.py --max-results 50
```

#### 示例5：多工作表导出

```bash
# 每个关键词一个工作表
python scripts/run.py --multi-sheet
```

#### 示例6：完整示例

```bash
python scripts/run.py -k 眼科 -d 7 --max-results 50 --multi-sheet -v
```

#### 示例7：指定输出文件名

```bash
python scripts/run.py -o my_tenders.xlsx
```

---

## Python代码调用

### 基础调用

```python
import sys
sys.path.insert(0, '~/.stepclaw/skills/medical-tender-scraper/src')

from config import TenderConfig
from fetchers.ccgp_fetcher import CCGPFetcher
from exporters.excel_exporter import ExcelExporter

# 创建配置
config = TenderConfig(
    keywords=["眼科"],
    days_back=7,
    max_results=50
)

# 创建抓取器
fetcher = CCGPFetcher(config)

# 执行搜索
results = fetcher.search_all_keywords()

# 导出到Excel
exporter = ExcelExporter()
output_path = exporter.export(results)

print(f"结果已保存到: {output_path}")
```

### 高级调用（自定义处理）

```python
import sys
sys.path.insert(0, '~/.stepclaw/skills/medical-tender-scraper/src')

from config import TenderConfig
from fetchers.ccgp_fetcher import CCGPFetcher

# 创建配置
config = TenderConfig(
    keywords=["眼科", "激光"],
    days_back=14,
    max_results=100
)

# 创建抓取器
fetcher = CCGPFetcher(config)

# 搜索所有关键词
results = fetcher.search_all_keywords()

# 遍历结果
for keyword, tenders in results.items():
    print(f"\n关键词 '{keyword}' 找到 {len(tenders)} 条:")
    for tender in tenders:
        print(f"  - {tender.title}")
        print(f"    日期: {tender.publish_date}")
        print(f"    省份: {tender.province}")
        print(f"    预算: {tender.budget}")
        print(f"    标的物: {tender.subject}")
        print(f"    联系人: {tender.contact_name} {tender.contact_phone}")
```

### 仅搜索不导出

```python
import sys
sys.path.insert(0, '~/.stepclaw/skills/medical-tender-scraper/src')

from config import TenderConfig
from fetchers.ccgp_fetcher import CCGPFetcher

config = TenderConfig(keywords=["眼科"], days_back=7)
fetcher = CCGPFetcher(config)

# 只搜索第一个关键词
results = fetcher.search("眼科")

# 处理结果
for tender in results:
    print(f"{tender.publish_date} - {tender.title}")
```

---

## 定时任务配置

### 方法1：OpenClaw Cron（推荐）

```bash
# 每周四上午10:00自动运行
openclaw cron add \
  --name "每周眼科招标采集" \
  --schedule "0 10 * * 4" \
  --command "python ~/.stepclaw/skills/medical-tender-scraper/scripts/run.py -k 眼科 -d 7"
```

查看定时任务：
```bash
openclaw cron list
```

### 方法2：Linux/Mac Cron

编辑crontab：
```bash
crontab -e
```

添加任务：
```bash
# 每周四上午10:00运行
0 10 * * 4 cd ~/.stepclaw/skills/medical-tender-scraper && python scripts/run.py -k 眼科 -d 7

# 每天上午9:00运行
0 9 * * * cd ~/.stepclaw/skills/medical-tender-scraper && python scripts/run.py -k 眼科 激光 -d 1
```

### 方法3：Windows任务计划程序

1. **打开任务计划程序**
   - 按 `Win + R`，输入 `taskschd.msc`

2. **创建基本任务**
   - 名称：每周眼科招标采集
   - 描述：自动采集眼科招标信息

3. **设置触发器**
   - 选择：每周
   - 开始时间：10:00:00
   - 选择：星期四

4. **设置操作**
   - 操作：启动程序
   - 程序/脚本：`python`
   - 参数：`scripts/run.py -k 眼科 -d 7`
   - 起始于：`C:\Users\[用户名]\.stepclaw\skills\medical-tender-scraper`

5. **完成**
   - 勾选"打开属性对话框"
   - 在"常规"选项卡中，选择"不管用户是否登录都要运行"

### 方法4：Python Schedule库

创建定时脚本 `scheduler.py`：

```python
import schedule
import time
import subprocess
import os

skill_path = os.path.expanduser("~/.stepclaw/skills/medical-tender-scraper")

def job():
    print("开始采集招标信息...")
    subprocess.run([
        "python", f"{skill_path}/scripts/run.py",
        "-k", "眼科",
        "-d", "7"
    ], cwd=skill_path)
    print("采集完成")

# 每周四10:00运行
schedule.every().thursday.at("10:00").do(job)

print("定时任务已启动，按Ctrl+C停止")
while True:
    schedule.run_pending()
    time.sleep(60)
```

运行：
```bash
python scheduler.py
```

---

## 输出文件说明

### 文件名格式

默认自动生成带日期的文件名：
```
medical_tenders_YYYYMMDD.xlsx
```

示例：
- `medical_tenders_20260407.xlsx`
- `medical_tenders_20260414.xlsx`

### 输出字段

| 序号 | 字段 | 说明 | 示例 |
|-----|------|------|------|
| 1 | 关键词 | 搜索使用的关键词 | 眼科 |
| 2 | 标题 | 招标公告标题 | 某医院眼科设备采购项目 |
| 3 | 发布日期 | 公告发布日期 | 2026-04-07 |
| 4 | 公告类型 | 招标/中标/询价等 | 公开招标公告 |
| 5 | 省份 | 招标所在省份 | 山东 |
| 6 | 采购单位 | 采购人名称 | 某市人民医院 |
| 7 | 代理机构 | 招标代理机构 | 某招标代理公司 |
| 8 | 预算金额 | 项目预算（如有） | 1,000,000.00元 |
| 9 | 标的物 | 采购的医疗设备 | 眼科激光治疗仪 |
| 10 | 联系人 | 项目联系人 | 张三 |
| 11 | 联系电话 | 联系人电话 | 0531-12345678 |
| 12 | 联系地址 | 联系地址 | 济南市某区某路 |
| 13 | URL | 公告详情页链接 | http://www.ccgp.gov.cn/... |

### 工作表格式

**单工作表（默认）：**
- 所有数据在一个工作表中
- 按关键词分组

**多工作表（--multi-sheet）：**
- 汇总表：统计各关键词数量
- 每个关键词一个独立工作表

---

## 常见问题

### Q1: 运行时报错"ModuleNotFoundError"

**原因**：依赖未安装

**解决**：
```bash
cd ~/.stepclaw/skills/medical-tender-scraper
pip install -r requirements.txt
```

### Q2: Windows控制台显示乱码

**原因**：Windows默认使用GBK编码

**解决**：
- 不影响Excel文件内容
- 或修改控制台编码为UTF-8：
```bash
chcp 65001
```

### Q3: 没有找到任何招标信息

**原因**：
1. 关键词太具体
2. 时间范围太短
3. 网络问题

**解决**：
```bash
# 尝试更宽泛的关键词
python scripts/run.py -k 医疗 设备

# 扩大时间范围
python scripts/run.py -d 30
```

### Q4: 预算金额大部分为空

**原因**：原始页面中大部分招标信息未标注预算

**解决**：这是正常情况，只有部分公告会标注预算金额

### Q5: 如何只导出特定省份的数据？

**解决**：导出后用Excel筛选，或使用Python代码过滤：

```python
import pandas as pd

df = pd.read_excel('medical_tenders_20260407.xlsx')
shandong = df[df['省份'] == '山东']
shandong.to_excel('shandong_tenders.xlsx', index=False)
```

### Q6: 如何合并多个Excel文件？

```python
import pandas as pd
import glob

files = glob.glob('medical_tenders_*.xlsx')
dfs = [pd.read_excel(f) for f in files]
merged = pd.concat(dfs, ignore_index=True)
merged.to_excel('merged_tenders.xlsx', index=False)
```

---

## 高级用法

### 自定义配置

编辑 `src/config.py`：

```python
from pydantic import BaseModel, Field
from typing import List

class TenderConfig(BaseModel):
    """自定义配置"""
    keywords: List[str] = ["眼科", "皮肤科"]
    days_back: int = 7
    max_results: int = 100
    output_file: str = "output.xlsx"
    timeout: int = 30
    retries: int = 3
```

### 添加新的关键词

编辑 `src/fetchers/ccgp_fetcher.py`：

```python
class CCGPFetcher:
    # 在MEDICAL_DEVICE_KEYWORDS中添加
    MEDICAL_DEVICE_KEYWORDS = [
        '显微镜', '激光', '超声', 'CT', 'MRI',
        '内窥镜', '监护仪', '呼吸机',  # 添加更多
    ]
```

### 修改Excel格式

编辑 `src/exporters/excel_exporter.py`：

```python
# 修改列宽
ws.column_dimensions['A'].width = 60  # 标题列更宽

# 修改表头颜色
header_fill = PatternFill(
    start_color="FF0000",  # 改为红色
    end_color="FF0000",
    fill_type="solid"
)
```

---

## 技术支持

如有问题，请检查：
1. Python版本 >= 3.7
2. 所有依赖已正确安装
3. 网络连接正常
4. 中国政府采购网可访问

---

## 更新日志

### v1.0 (2026-04-07)
- 初始版本发布
- 支持中国政府采购网抓取
- 13个字段完整提取
- Excel导出功能
- 定时任务支持

---

*文档维护：小招*  
*最后更新：2026-04-07*
