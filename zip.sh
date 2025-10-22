#!/bin/bash
# ===========================================
# 备份脚本：递归压缩 projects 和 roh_with_rm65
# 生成时间：$(date '+%Y-%m-%d %H:%M:%S')
# ===========================================

# 设置输出文件名（包含日期时间）
DATE=$(date '+%Y%m%d_%H%M%S')
OUTPUT_FILE="backup_${DATE}.tar"

# 要压缩的目录
DIRS=("projects" "roh_with_rm65")

# 检查目录是否存在
for DIR in "${DIRS[@]}"; do
    if [ ! -d "$DIR" ]; then
        echo "⚠️ 目录不存在：$DIR"
        exit 1
    fi
done

# 执行压缩
echo "开始压缩：${DIRS[*]}"
# tar -cvf "$OUTPUT_FILE" "${DIRS[@]}"
tar -cf "$OUTPUT_FILE" "${DIRS[@]}"

# 检查是否成功
if [ $? -eq 0 ]; then
    echo "✅ 压缩完成：$OUTPUT_FILE"
else
    echo "❌ 压缩失败！"
fi
