import pandas as pd
from bib_dedupe.bib_dedupe import block, cluster, match, merge, prep

# 定义数据路径
MERGED_CSV_PATH = "/Users/jiangmingxin/Desktop/bib-dedupe-1/output/merged_100_samples.csv"
OUTPUT_CSV_PATH = "/Users/jiangmingxin/Desktop/bib-dedupe-1/output/merged_100_deduped.csv"

if __name__ == "__main__":

    # 读取数据
    df = pd.read_csv(MERGED_CSV_PATH)

    # 确保数据不为空
    if df.empty:
        print("Error: The merged dataset is empty. Check your source files.")
        exit(1)

    print(f"Dataset loaded with {df.shape[0]} records.")

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
    print(f"Deduplicated dataset saved to {OUTPUT_CSV_PATH}")

