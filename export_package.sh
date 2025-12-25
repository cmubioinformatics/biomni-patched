#!/bin/bash
# 将修改后的 biomni 包导出为 tar.gz 压缩包

PATCH_DIR="/data/ag_reichart_lindberg/home/xin/project/biomni-patched"
OUTPUT_FILE="/data/ag_reichart_lindberg/home/xin/project/biomni-patched-$(date +%Y%m%d).tar.gz"

echo "正在导出 biomni 补丁包..."

cd "$PATCH_DIR"
tar -czf "$OUTPUT_FILE" biomni/ PATCH_README.md

echo ""
echo "导出完成!"
echo "压缩包位置: $OUTPUT_FILE"
echo ""
echo "在另一台机器上使用:"
echo "  1. 解压: tar -xzf biomni-patched-*.tar.gz"
echo "  2. 覆盖安装到 conda 环境的 site-packages/biomni/"
