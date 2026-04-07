import pandas as pd
import os

# 找到最新的Excel文件
files = [f for f in os.listdir('.') if f.startswith('medical_tenders_') and f.endswith('.xlsx')]
if not files:
    print('未找到Excel文件')
    exit()

latest_file = sorted(files)[-1]
print('文件:', latest_file)
print('文件大小:', os.path.getsize(latest_file), '字节')
print()

# 读取Excel
df = pd.read_excel(latest_file)

print('=== 抓取结果统计 ===')
print('总记录数:', len(df))
print()

print('列名:')
for i, col in enumerate(df.columns, 1):
    print('  ' + str(i) + '. ' + col)
print()

# 统计各字段非空数量
print('字段完整度:')
for col in df.columns:
    non_null = df[col].notna().sum()
    pct = non_null / len(df) * 100
    print('  ' + col + ': ' + str(non_null) + '/' + str(len(df)) + ' (' + str(round(pct, 0)) + '%)')
print()

# 统计省份分布
print('省份分布:')
province_counts = df['省份'].value_counts()
for province, count in province_counts.items():
    if pd.notna(province):
        print('  ' + str(province) + ': ' + str(count) + '条')
print()

# 统计公告类型
print('公告类型分布:')
type_counts = df['公告类型'].value_counts()
for t, count in type_counts.items():
    if pd.notna(t):
        print('  ' + str(t) + ': ' + str(count) + '条')
print()

# 显示所有记录
print('=== 所有记录详情 ===')
for i in range(len(df)):
    row = df.iloc[i]
    print()
    print(str(i+1) + '. ' + str(row['标题']))
    print('   日期:', row['发布日期'])
    print('   类型:', row['公告类型'])
    print('   省份:', row['省份'] if pd.notna(row['省份']) else '未标注')
    print('   采购单位:', row['采购单位'])
    budget = row['预算金额'] if pd.notna(row['预算金额']) else '未标注'
    print('   预算:', budget)
    subject = row['标的物'] if pd.notna(row['标的物']) and str(row['标的物']) != '' else '未提取'
    print('   标的物:', subject)
    contact = row['联系人'] if pd.notna(row['联系人']) and str(row['联系人']) != '' else '未提取'
    print('   联系人:', contact)
    phone = row['联系电话'] if pd.notna(row['联系电话']) and str(row['联系电话']) != '' else '未提取'
    print('   电话:', phone)
