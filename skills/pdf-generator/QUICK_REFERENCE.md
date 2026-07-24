# PDF生成器图片功能 - 快速参考

## 🚀 快速开始

### 添加单张图片
```bash
python skills/pdf-generator/scripts/generate_pdf.py \
  --input-type text \
  --input "报告内容" \
  --output "report.pdf" \
  --images "chart.png" \
  --image-width 80% \
  --image-align center \
  --image-caption "图表标题"
```

### 添加多张图片
```bash
python skills/pdf-generator/scripts/generate_pdf.py \
  --input-type html \
  --input "<h1>目录</h1>" \
  --output "catalog.pdf" \
  --images "img1.jpg" "img2.png" "img3.svg" \
  --image-width 100% \
  --image-align center
```

## 📋 参数速查

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--images` | 图片路径列表 | - | `"a.png" "b.jpg"` |
| `--image-width` | 图片宽度 | `100%` | `80%`, `200px`, `50mm` |
| `--image-height` | 图片高度 | `auto` | `auto`, `150px`, `100mm` |
| `--image-align` | 对齐方式 | `center` | `left`, `center`, `right` |
| `--image-caption` | 图片标题 | `` | `"销售图表"` |

## 🖼️ 支持格式

- ✅ **PNG** - 图表、截图
- ✅ **JPEG/JPG** - 照片
- ✅ **GIF** - 简单图形
- ✅ **SVG** - 矢量图

## 💡 常用场景

### 1. 销售报告带图表
```bash
--images "sales_chart.png" \
--image-width 90% \
--image-caption "Q1销售数据"
```

### 2. 产品目录
```bash
--images "p1.jpg" "p2.jpg" "p3.jpg" \
--image-width 250px \
--image-height 200px \
--orientation landscape
```

### 3. 技术文档配图
```bash
--images "architecture.svg" \
--image-width 180mm \
--image-height auto \
--image-align center
```

## ⚠️ 注意事项

1. **输出文件**: 图片保存在 `原文件名_images.pdf`
2. **文件大小**: 建议单张图片 < 5MB
3. **分辨率**: 150-300 DPI 足够
4. **格式选择**: 照片用JPEG,图表用PNG

## 🔧 故障排除

**图片未显示?**
- 检查文件路径是否正确
- 确认格式是否支持(PNG/JPG/GIF/SVG)
- 查看错误信息

**PDF太大?**
- 压缩图片后再使用
- 使用JPEG代替PNG(照片)
- 降低分辨率

**尺寸不合适?**
- 尝试百分比单位: `--image-width 80%`
- 或使用固定单位: `--image-width 200px`
- 高度设为auto保持比例: `--image-height auto`

## 📚 更多资源

- 完整文档: [SKILL.md](SKILL.md)
- 使用指南: [IMAGE_USAGE.md](IMAGE_USAGE.md)
- 演示脚本: `python demo_image_feature.py`
- 测试脚本: `python test_image_feature.py`

---

**提示**: 运行 `python skills/pdf-generator/scripts/generate_pdf.py --help` 查看所有可用参数
