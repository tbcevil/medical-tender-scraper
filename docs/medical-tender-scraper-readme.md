# 医疗器械招投标信息搜集工具

> 开发完成日期：2026-04-07  
> 版本：v1.0  
> 状态：✅ 已封装为OpenClaw Skill

---

## 项目概述

从中国政府采购网抓取医疗器械相关招标信息，支持关键词搜索、多字段提取、Excel导出。

### 核心功能

- ✅ **关键词搜索**：支持自定义关键词（如"眼科"、"激光"等）
- ✅ **时间范围**：可指定搜索最近N天的招标信息
- ✅ **多字段提取**：提取13个字段（标题、日期、省份、采购单位、预算、标的物、联系人等）
- ✅ **Excel导出**：支持单工作表和多工作表格式
- ✅ **自动命名**：输出文件自动带上日期（medical_tenders_YYYYMMDD.xlsx）

---

## 快速开始

### 安装

```bash
# 进入Skill目录
cd skills/medical-tender-scraper

# 安装依赖
pip install -r requirements.txt
```

### 基本使用

```bash
# 默认运行（搜索"眼科"，最近7天）
python scripts/run.py

# 指定关键词
python scripts/run.py -k 眼科

# 指定时间范围（最近14天）
python scripts/run.py -d 14

# 指定最大结果数
python scripts/run.py --max-results 50

# 多工作表导出
python scripts/run.py --multi-sheet

# 完整示例
python scripts/run.py -k 眼科 -d 7 --max-results 50 -v
```

---

## 技术架构

### 项目结构

```
medical-tender-scraper/
├── SKILL.md                    # Skill说明文档
├── src/
│   ├── config.py              # 配置管理（Pydantic）
│   ├── main.py                # 主入口
│   ├── http_client.py         # HTTP客户端（httpx）
│   ├── fetchers/
│   │   └── ccgp_fetcher.py   # 中国政府采购网抓取器
│   └── exporters/
│       └── excel_exporter.py # Excel导出器（pandas+openpyxl）
├── scripts/
│   └── run.py                 # 运行脚本
└── requirements.txt           # Python依赖
```

### 数据流

```
用户输入 → 配置解析 → 关键词搜索 → 列表页解析 → 详情页抓取 → Excel导出
```

### 提取策略

**标的物提取（5种策略）：**
1. 表格"包内容"列提取
2. "品目名称"列提取
3. 标题提取医疗设备关键词
4. 页面文本提取
5. "采购需求"段落提取

**联系人提取（多模式匹配）：**
- 项目联系人/联系人字段
- 电话/联系方式字段
- 地址字段
- 遍历页面段落备用提取

---

## 输出字段

| 序号 | 字段 | 说明 | 提取成功率 |
|-----|------|------|-----------|
| 1 | 关键词 | 搜索使用的关键词 | 100% |
| 2 | 标题 | 招标公告标题 | 100% |
| 3 | 发布日期 | 公告发布日期 | 100% |
| 4 | 公告类型 | 公开招标/中标公告等 | 100% |
| 5 | 省份 | 招标所在省份 | 70% |
| 6 | 采购单位 | 采购人名称 | 100% |
| 7 | 代理机构 | 招标代理机构 | 100% |
| 8 | 预算金额 | 项目预算 | 15% |
| 9 | **标的物** | 采购的医疗设备 | **100%** |
| 10 | 联系人 | 项目联系人 | 75% |
| 11 | **联系电话** | 联系人电话 | **100%** |
| 12 | 联系地址 | 联系地址 | 70% |
| 13 | URL | 公告详情页链接 | 100% |

> 注：预算金额提取率低是因为原始页面中大部分未标注预算

---

## 测试结果

### 完整测试（2026-04-07）

**测试配置：**
- 关键词：眼科
- 时间范围：最近7天
- 最大结果：50条

**测试结果：**
- 总记录数：20条
- 数据来源：中国政府采购网

**省份分布：**
- 山东、浙江、河北：各2条
- 内蒙古、新疆、吉林、天津、山西、四川、广东：各1条

**公告类型：**
- 公开招标公告：6条
- 中标公告、竞争性磋商：各4条
- 竞争性谈判公告：3条

---

## 数据源

### 已验证可用（37个网站）

| 级别 | 数量 | 网站 |
|------|------|------|
| 中央级 | 2 | 中国政府采购网、中国招标投标公共服务平台 |
| 直辖市 | 4 | 北京、天津、上海、重庆 |
| 省份 | 28 | 河北、山西、内蒙古、辽宁、吉林、**黑龙江**、江苏、浙江、安徽、福建、**江西**、山东、河南、湖北、湖南、广东、广西、海南、四川、贵州、云南、西藏、陕西、甘肃、青海、宁夏、新疆 |
| 计划单列市 | 4 | 大连、宁波、厦门、**深圳** |

> **替代网址说明**：
> - **黑龙江**：https://hljcg.hlj.gov.cn/（原域名DNS失败）
> - **江西**：https://zfcg.jxf.gov.cn/（原域名证书错误）
> - **深圳**：http://zfcg.szggzy.com:8081/gsgg/002001/002001002/list.html（原域名云防护拦截）
>
> 以上替代网址由阿土伯提供并验证可用

### 数据源扩展计划

**V1版本（当前）：**
- ✅ 中国政府采购网（HTTP抓取）

**V2版本（计划中）：**
- 各省市政府采购网（需浏览器渲染的9个网站）

**V3版本（未来）：**
- 中国招标投标公共服务平台
- 第三方招标信息平台

---

## 配置说明

### 命令行参数

| 参数 | 短格式 | 说明 | 默认值 |
|------|--------|------|--------|
| `--keywords` | `-k` | 搜索关键词列表 | ["眼科"] |
| `--days` | `-d` | 搜索最近N天 | 7 |
| `--output` | `-o` | 输出文件名 | 自动生成 |
| `--max-results` | - | 每个关键词最大结果数 | 100 |
| `--multi-sheet` | - | 使用多工作表格式 | False |
| `--verbose` | `-v` | 显示详细输出 | False |

### 配置文件

```python
# src/config.py
class TenderConfig:
    keywords: List[str] = ["眼科"]
    days_back: int = 7
    max_results: int = 100
    output_file: str = "medical_tenders.xlsx"
    timeout: int = 30
    retries: int = 3
```

---

## 定时任务配置

### 使用OpenClaw Cron

```bash
# 每周四上午10:00自动运行
openclaw cron add \
  --name "每周眼科招标采集" \
  --schedule "0 10 * * 4" \
  --command "python skills/medical-tender-scraper/scripts/run.py -k 眼科 -d 7"
```

### 使用系统Cron（Linux/Mac）

```bash
# 编辑crontab
crontab -e

# 添加定时任务
0 10 * * 4 cd /path/to/skills/medical-tender-scraper && python scripts/run.py -k 眼科 -d 7
```

### 使用Windows任务计划程序

1. 创建基本任务
2. 触发器：每周四 10:00
3. 操作：启动程序
4. 程序：python
5. 参数：scripts/run.py -k 眼科 -d 7
6. 起始于：skills/medical-tender-scraper目录

---

## 扩展开发

### 添加新的数据源

1. 在 `src/fetchers/` 下创建新的抓取器
2. 实现 `search()` 和 `parse_list_page()` 方法
3. 在 `main.py` 中添加调用

示例：
```python
# src/fetchers/xxx_fetcher.py
class XXXFetcher:
    def search(self, keyword: str) -> List[TenderInfo]:
        # 实现搜索逻辑
        pass
```

### 添加新的提取字段

1. 在 `TenderInfo` 数据类中添加新字段
2. 在 `_fetch_detail_info()` 中添加提取逻辑
3. 在 `excel_exporter.py` 中添加导出列

---

## 注意事项

1. **请求频率**：程序自动控制（每页1.5秒间隔），避免对服务器造成压力
2. **编码问题**：Windows控制台可能显示乱码，不影响Excel文件
3. **预算金额**：仅部分招标信息标注预算，未标注的显示为空
4. **反爬机制**：部分网站有WAF防护，已标记为"需浏览器渲染"
5. **数据时效**：基于中国政府采购网公开数据，实时性取决于网站更新

---

## 依赖清单

```
httpx>=0.24.0          # HTTP客户端
beautifulsoup4>=4.12.0 # HTML解析
pydantic>=2.0.0        # 数据验证
pandas>=2.0.0          # 数据处理
openpyxl>=3.1.0        # Excel导出
```

---

## 更新日志

### v1.0 (2026-04-07)
- ✅ 完成MVP版本开发
- ✅ 实现中国政府采购网抓取
- ✅ 13个字段完整提取
- ✅ 标的物提取成功率100%
- ✅ 联系人提取成功率75%
- ✅ 文件名自动带日期
- ✅ 封装为OpenClaw Skill

### 后续计划
- [ ] 添加更多数据源（省级网站）
- [ ] 优化预算金额提取
- [ ] 添加数据去重功能
- [ ] 支持增量更新
- [ ] 添加邮件通知功能

---

## 许可证

MIT License

---

## 联系方式

如有问题或建议，请联系开发者。
