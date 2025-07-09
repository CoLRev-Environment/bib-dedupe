import pandas as pd
import os

# 定义数据文件路径
DBLP_CSV_PATH = "/Users/jiangmingxin/.colrev/curated_metadata/journal-of-management-information-systems/data/search/DBLP.csv"
PDF_CSV_PATH = "/Users/jiangmingxin/.colrev/curated_metadata/journal-of-management-information-systems/data/search/pdfs.csv"
MERGED_CSV_PATH = "/Users/jiangmingxin/Desktop/bib-dedupe-1/output/merged_100_samples.csv"

# 读取 CSV 数据
try:
    dblp_df = pd.read_csv(DBLP_CSV_PATH)
    pdf_df = pd.read_csv(PDF_CSV_PATH)
except FileNotFoundError as e:
    print(f"Error: {e}")
    exit(1)

# **打印 CSV 记录数**
print(f"DBLP data loaded: {dblp_df.shape[0]} rows")
print(f"PDF data loaded: {pdf_df.shape[0]} rows")

# 确保数据文件不是空的
if dblp_df.empty or pdf_df.empty:
    print("Error: One or both CSV files are empty. Check your data sources.")
    exit(1)

# 取前 50 条数据（如果少于 50，则取全部）
dblp_sample = dblp_df.head(50)
pdf_sample = pdf_df.head(50)

# **修改 ID，保证唯一，改成 1-100 的连续数字**
merged_df = pd.concat([dblp_sample, pdf_sample], ignore_index=True)
merged_df["ID"] = range(1, len(merged_df) + 1)

# **修正 title 为空的问题**
merged_df["title"].fillna("UNKNOWN", inplace=True)

# 确保输出目录存在
os.makedirs(os.path.dirname(MERGED_CSV_PATH), exist_ok=True)

# **检查是否正确合并**
print(f"Merged dataset has {merged_df.shape[0]} rows.")

# 保存合并后的 CSV 文件
merged_df.to_csv(MERGED_CSV_PATH, index=False)
print(f"Merged CSV file created: {MERGED_CSV_PATH}")

# **检查最终文件是否存在**
if os.path.exists(MERGED_CSV_PATH):
    print(f"✅ Success: {MERGED_CSV_PATH} created.")
else:
    print(f"❌ Error: {MERGED_CSV_PATH} not found!")
