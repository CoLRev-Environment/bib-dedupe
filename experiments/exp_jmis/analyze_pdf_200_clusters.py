import pandas as pd
import ast

# 文件路径
INPUT_CSV_PATH = "/Users/jiangmingxin/Desktop/bib-dedupe-1/output/pdf_200_nodup_input.csv"
CLUSTERS_TXT_PATH = "/Users/jiangmingxin/Desktop/bib-dedupe-1/output/duplicate_clusters.txt"
CLUSTERS_CSV_PATH = "/Users/jiangmingxin/Desktop/bib-dedupe-1/output/duplicate_clusters_explained.csv"

# 读取输入数据
df = pd.read_csv(INPUT_CSV_PATH)

# 读取 duplicate_id_sets 列表（保存为文本文件的格式）
with open(CLUSTERS_TXT_PATH, "r") as f:
    text = f.read()
    duplicate_id_sets = ast.literal_eval(text)

# 提取每个组中所有记录
records = []
for cluster_index, id_set in enumerate(duplicate_id_sets, start=1):
    for item_id in id_set:
        # 注意转换为 int 类型以匹配原始 DataFrame 中的 ID 列
        item_id_int = int(item_id)
        row = df[df["ID"] == item_id_int]
        if not row.empty:
            record = row.iloc[0].to_dict()
            record["cluster_id"] = cluster_index
            records.append(record)

# 转换为 DataFrame，导出为 CSV
cluster_df = pd.DataFrame(records)

# 选取常用字段输出（你可以根据需要调整）
columns_to_show = ["cluster_id", "ID", "author", "title", "year", "journal"]
cluster_df[columns_to_show].sort_values(["cluster_id", "ID"]).to_csv(CLUSTERS_CSV_PATH, index=False)

print(f"{len(duplicate_id_sets)} clusters written to: {CLUSTERS_CSV_PATH}")
