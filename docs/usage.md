# 使用文档

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行程序

```bash
python run.py
```

程序会自动抓取最近7天内中国政府采购网上与"眼科"、"皮肤科"相关的招标信息，并导出为Excel文件。

## 高级用法

### 自定义关键词

```bash
python run.py -k 眼科 皮肤科 口腔科 检验科
```

### 自定义时间范围

```bash
# 搜索最近30天
python run.py -d 30

# 搜索最近14天
python run.py -d 14
```

### 自定义输出文件

```bash
python run.py -o ./output/招标信息.xlsx
```

### 多工作表导出

```bash
python run.py --multi-sheet
```

这会将每个关键词的招标信息放在单独的工作表中，方便分类查看。

### 完整示例

```bash
python run.py \
    -k 眼科 皮肤科 \
    -d 30 \
    -o ./output/医疗器械招标.xlsx \
    -m 200 \
    -p 10 \
    --multi-sheet \
    -v
```

## 作为模块使用

```python
from src.config import TenderConfig
from src.fetchers.ccgp_fetcher import CCGPFetcher
from src.exporters.excel_exporter import ExcelExporter

# 创建配置
config = TenderConfig(
    keywords=["眼科", "皮肤科"],
    days_back=14,
    output_file="output.xlsx"
)

# 抓取数据
with CCGPFetcher(config) as fetcher:
    tenders = fetcher.get_all_tenders()

# 导出数据
exporter = ExcelExporter(config.output_file)
exporter.export(tenders)
```

## 输出文件格式

### 主工作表字段

| 字段 | 说明 |
|------|------|
| 标题 | 招标项目标题 |
| 链接 | 招标公告链接（可点击） |
| 发布日期 | 招标信息发布日期 |
| 信息来源 | 信息来源网站 |
| 关键词 | 匹配的关键词 |
| 项目描述 | 项目简要描述 |
| 地区 | 招标地区 |
| 代理机构 | 招标代理机构 |
| 项目编号 | 招标项目编号 |
| 抓取时间 | 数据抓取时间 |

### 汇总统计工作表

- 总记录数
- 抓取时间
- 各关键词数量统计
- 各来源数量统计
- 各地区数量统计（Top 5）

## 常见问题

### Q: 抓取不到数据？

A: 可能的原因：
1. 网络连接问题，请检查网络
2. 目标网站结构变化，需要更新解析器
3. 搜索条件过于严格，尝试放宽时间范围

### Q: 如何增加更多关键词？

A: 使用 `-k` 参数：
```bash
python run.py -k 关键词1 关键词2 关键词3
```

### Q: 如何定时自动运行？

A: 可以使用操作系统的定时任务：

**Linux/Mac (cron)**:
```bash
# 每天上午9点运行
crontab -e
0 9 * * * cd /path/to/project && python run.py
```

**Windows (任务计划程序)**:
1. 打开任务计划程序
2. 创建基本任务
3. 设置触发器和操作
4. 指定程序路径和参数

### Q: 如何修改默认配置？

A: 编辑 `src/config.py` 中的 `TenderConfig` 类：

```python
class TenderConfig(BaseModel):
    base_url: str = "http://www.ccgp.gov.cn"
    keywords: List[str] = ["眼科", "皮肤科"]  # 修改默认关键词
    days_back: int = 7  # 修改默认时间范围
    timeout: int = 30
    max_results: int = 100
    output_file: str = "medical_tenders.xlsx"
```

## 故障排除

### 编码错误

如果遇到编码问题，可以尝试修改 `http_client.py` 中的编码设置：

```python
response.encoding = "gb2312"  # 或 "gbk", "utf-8"
```

### 请求超时

增加超时时间：
```bash
python run.py -t 60
```

### SSL证书错误

如果遇到SSL证书错误，可以修改 `http_client.py` 中的客户端配置：

```python
self._client = httpx.Client(
    timeout=self.timeout,
    headers=self.headers,
    follow_redirects=True,
    verify=False  # 禁用SSL验证（不推荐用于生产环境）
)
```
