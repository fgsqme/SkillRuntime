# PDF生成器图片功能使用指南

## 概述

PDF生成器现在支持将图片添加到PDF文档中。您可以从本地文件添加单张或多张图片,并自定义它们的尺寸、对齐方式和标题。

## 快速开始

### 1. 基本用法 - 添加单张图片

```bash
python skills/pdf-generator/scripts/generate_pdf.py \
  --input-type text \
  --input "这是一个带图片的报告" \
  --output "report.pdf" \
  --images "chart.png" \
  --image-width 80% \
  --image-align center \
  --image-caption "销售趋势图"
```

### 2. 添加多张图片

```bash
python skills/pdf-generator/scripts/generate_pdf.py \
  --input-type markdown \
  --input-file "article.md" \
  --output "article.pdf" \
  --images "fig1.jpg" "fig2.png" "fig3.svg" \
  --image-width 100% \
  --image-align center \
  --image-caption "图表展示"
```

### 3. 自定义图片尺寸

```bash
python skills/pdf-generator/scripts/generate_pdf.py \
  --input-type html \
  --input "<h1>产品目录</h1>" \
  --output "products.pdf" \
  --images "product.jpg" \
  --image-width 300px \
  --image-height 200px \
  --image-align left
```

## 支持的图片格式

- **PNG** (.png): 适合图表、截图,支持透明背景
- **JPEG/JPG** (.jpg, .jpeg): 适合照片,文件较小
- **GIF** (.gif): 支持简单动画(静态显示)
- **SVG** (.svg): 矢量图形,无损缩放

## 参数说明

### --images
图片路径列表,支持多个图片,用空格分隔。

```bash
--images "image1.png" "image2.jpg" "image3.svg"
```

### --image-width
图片宽度,支持以下单位:
- **百分比**: `100%`, `80%`, `50%` (相对于页面宽度)
- **像素**: `200px`, `300px`, `500px`
- **毫米**: `50mm`, `100mm`, `150mm`

默认值: `100%`

### --image-height
图片高度,支持相同单位。

默认值: `auto` (保持原始比例)

### --image-align
图片对齐方式:
- `left`: 左对齐
- `center`: 居中对齐 (默认)
- `right`: 右对齐

### --image-caption
图片标题,会显示在图片下方,使用斜体灰色文字。

## 工作原理

1. **图片读取**: 脚本读取指定的本地图片文件
2. **Base64编码**: 将图片转换为base64格式嵌入HTML
3. **HTML生成**: 创建包含所有图片的HTML页面
4. **PDF渲染**: 使用WeasyPrint将HTML转换为PDF
5. **输出文件**: 生成名为 `原文件名_images.pdf` 的文件

## 示例场景

### 场景1: 创建带图表的销售报告

```bash
python skills/pdf-generator/scripts/generate_pdf.py \
  --input-type markdown \
  --input "# Q1 销售报告\n\n## 总结\n\n本季度销售额增长20%。" \
  --output "q1_report.pdf" \
  --images "sales_chart.png" "growth_graph.jpg" \
  --image-width 90% \
  --image-align center \
  --image-caption "2024年第一季度数据" \
  --title "Q1销售报告" \
  --author "销售部"
```

### 场景2: 创建产品目录

```bash
python skills/pdf-generator/scripts/generate_pdf.py \
  --input-type html \
  --input "<h1>产品目录</h1><p>以下是我们的主要产品线。</p>" \
  --output "catalog.pdf" \
  --images "product_a.jpg" "product_b.jpg" "product_c.png" \
  --image-width 250px \
  --image-height 200px \
  --image-align center \
  --page-size Letter \
  --orientation landscape
```

### 场景3: 技术文档配图

```bash
python skills/pdf-generator/scripts/generate_pdf.py \
  --input-type markdown \
  --input-file "architecture.md" \
  --output "architecture_doc.pdf" \
  --images "system_diagram.svg" "data_flow.png" \
  --image-width 180mm \
  --image-height auto \
  --image-align center \
  --image-caption "系统架构图"
```

## 最佳实践

### 1. 优化图片大小
- 照片使用JPEG格式,质量70-80%
- 图表使用PNG格式
- 避免过大的图片(建议单张<5MB)
- 使用适当分辨率(150-300 DPI足够)

### 2. 选择合适的尺寸单位
- **百分比**: 当需要适应不同页面大小时
- **像素**: 当需要精确控制时
- **毫米**: 当需要打印友好时

### 3. 添加有意义的标题
```bash
--image-caption "图1: 2024年用户增长趋势"
```

### 4. 考虑页面布局
- 横向页面适合宽图片: `--orientation landscape`
- 调整边距为图片留出空间: `--margin-left 15 --margin-right 15`

## 注意事项

1. **文件位置**: 图片会被添加到单独的PDF文件中(`_images.pdf`后缀)
2. **顺序**: 图片按照命令行中指定的顺序排列
3. **分页**: 每张图片会自动避免跨页分割
4. **错误处理**: 如果图片加载失败,会显示错误提示但不会中断整个流程

## 故障排除

### 问题: 图片未显示
**解决**: 
- 检查图片路径是否正确
- 确认图片格式是否支持(PNG/JPG/GIF/SVG)
- 查看错误信息中的具体原因

### 问题: PDF文件过大
**解决**:
- 压缩图片后再添加
- 使用JPEG代替PNG(对于照片)
- 降低图片分辨率
- 启用压缩: `--compress true`

### 问题: 图片变形
**解决**:
- 使用 `--image-height auto` 保持比例
- 或者设置合适的宽高比

## 依赖要求

确保已安装以下Python库:
```bash
pip install weasyprint pillow
```

对于Markdown支持:
```bash
pip install markdown
```

## 更多信息

- 参见 [SKILL.md](SKILL.md) 了解完整的PDF生成器功能
- 参见 [format-support.md](references/format-support.md) 了解格式支持详情
