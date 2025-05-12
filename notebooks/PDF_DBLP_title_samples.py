import os
import pandas as pd
from pybtex.database import parse_file
from bib_dedupe.bib_dedupe import prep, block, match, cluster, merge

# 🔹 文件路径
BIB_FILE_PATH = "/Users/jiangmingxin/Desktop/bib-dedupe-1/notebooks/PDF_DBLP_title_samples.bib"
CSV_FILE_PATH = "/Users/jiangmingxin/Desktop/bib-dedupe-1/output/PDF_DBLP_title_samples.csv"
OUTPUT_CSV_PATH = "/Users/jiangmingxin/Desktop/bib-dedupe-1/output/PDF_DBLP_title_samples_deduped.csv"

# 🔹 确保输出目录存在
os.makedirs(os.path.dirname(CSV_FILE_PATH), exist_ok=True)

# 🔹 设定要提取的字段
FIELDS_TO_KEEP = ["ID", "author", "title", "year", "journal", "doi"]

def convert_bib_to_csv():
    """转换 BibTeX 文件到 CSV"""
    print(f"🔄 正在转换 {BIB_FILE_PATH} 到 CSV...")
    bib_data = parse_file(BIB_FILE_PATH)
    records = []
    
    for key, entry in bib_data.entries.items():
        record = {field: entry.fields.get(field, "") for field in FIELDS_TO_KEEP}
        
        # 处理作者字段
        if "author" in entry.persons:
            record["author"] = " and ".join(
                [" ".join(person.first_names + person.last_names) for person in entry.persons["author"]]
            )

        # 设定唯一 ID
        record["ID"] = key
        records.append(record)

    # 转换为 DataFrame
    df = pd.DataFrame(records)

    # 处理空值（避免 BibDedupe 忽略）
    df.fillna("", inplace=True)

    # 保存为 CSV
    df.to_csv(CSV_FILE_PATH, index=False)
    print(f"✅ CSV 文件已创建: {CSV_FILE_PATH}")

def run_dedupe():
    """运行 BibDedupe 去重"""
    print(f"\n🚀 运行去重算法...")
    df = pd.read_csv(CSV_FILE_PATH)
    print(f"📌 原始数据集大小: {df.shape[0]} 条")

    # 预处理数据
    df = prep(df)

    # 进行 blocking 以减少计算量
    blocked_df = block(df)

    # 进行匹配，找到可能的重复项
    matched_df = match(blocked_df)

    # 进行聚类，将重复项归类到一起
    duplicate_id_sets = cluster(matched_df)

    # 执行合并，移除重复项
    deduped_df = merge(df, duplicate_id_sets=duplicate_id_sets)

    # 保存去重后的结果
    deduped_df.to_csv(OUTPUT_CSV_PATH, index=False)
    print(f"✅ 去重后数据集已保存: {OUTPUT_CSV_PATH}")

    # 查看去重结果
    print(f"📌 去重后数据集大小: {deduped_df.shape[0]} 条")
    print(deduped_df.head())

if __name__ == "__main__":
    convert_bib_to_csv()  # 步骤 1: 转换 CSV
    run_dedupe()          # 步骤 2: 运行去重
