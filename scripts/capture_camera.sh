#!/bin/bash
# 本地摄像头截图脚本 (macOS)
# 运行后会拍照并保存到桌面，然后你可以手动发送到飞书

OUTPUT="$HOME/Desktop/camera_$(date +%Y%m%d-%H%M%S).jpg"

# 检查是否安装 imagesnap（macOS 常用命令行截图工具）
if ! command -v imagesnap &> /dev/null; then
    echo "未找到 imagesnap，尝试安装..."
    brew install imagesnap
fi

# 拍照（0.5秒后自动保存，防止模糊）
echo "📸 准备拍照，请看向摄像头..."
sleep 0.5
imagesnap -w 1 "$OUTPUT" 2>/dev/null

if [ -f "$OUTPUT" ]; then
    echo "✅ 照片已保存到: $OUTPUT"
    echo "现在请在飞书里直接发送这个图片文件。"
    open "$OUTPUT"  # 预览图片
else
    echo "❌ 拍照失败，请检查摄像头权限（系统偏好设置 -> 安全性与隐私 -> 摄像头）"
fi
