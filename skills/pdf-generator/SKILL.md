---
name: pdf-generator
description: >-
  从文本、Markdown或HTML内容生成PDF文档。支持自定义页面大小、
  边距、字体和样式。可添加图片(PNG/JPEG/GIF/SVG)到PDF中。
  当用户需要将报告、文档或网页转换为PDF格式时使用。
  关键词：pdf, generate, convert, document, report, image, 生成PDF, 转换PDF, 图片
---

# PDF生成器

从多种源格式（文本、Markdown、HTML）生成专业的PDF文档。

## 使用时机

- 用户要求将文本内容转换为PDF文件
- 用户需要将Markdown文档导出为PDF
- 用户想要将HTML页面保存为PDF
- 用户需要生成报告、文档或证书的PDF版本
- 用户请求批量转换多个文件为PDF格式

## 安全规则

**关键**：PDF生成可能涉及资源密集型操作！

### 禁止的操作（绝不执行）：
- 生成超过100页的PDF（除非明确授权）
- 包含恶意JavaScript的HTML内容
- 访问外部资源的HTML（防止XSS攻击）
- 写入系统目录或受保护路径
- 生成超过50MB的单个PDF文件

### 必需的验证步骤：
1. **使用 `scripts/validate_input.py` 检查输入内容安全性**
2. **验证输出路径可写且安全**
3. **检查内容大小和复杂度**
4. **捕获错误和资源限制**
5. **返回生成结果和文件信息**

## PDF生成工作流程

### 步骤 1：验证输入

```bash
python scripts/validate_input.py "<输入类型>" "<输入来源>" [--content-file <文件>]
```

检查内容：
- 输入格式有效性（text/markdown/html）
- 内容大小限制
- HTML安全性（无脚本标签）
- 输出路径安全性

**如果验证失败**：拒绝该操作并说明原因。

### 步骤 2：生成PDF

#### 从纯文本生成
```bash
python scripts/generate_pdf.py --input-type text --input "<文本内容>" --output "<输出路径.pdf>"
```

#### 从Markdown生成
```bash
python scripts/generate_pdf.py --input-type markdown --input "<Markdown内容>" --output "<输出路径.pdf>"
```

#### 从HTML生成
```bash
python scripts/generate_pdf.py --input-type html --input "<HTML内容>" --output "<输出路径.pdf>"
```

#### 从文件生成
```bash
python scripts/generate_pdf.py --input-type markdown --input-file "document.md" --output "document.pdf"
```

参数：
- `--input-type`：输入类型：text/markdown/html（必需）
- `--input`：直接提供的内容字符串
- `--input-file`：从文件读取内容（与--input互斥）
- `--output`：输出PDF文件路径（必需，必须以.pdf结尾）
- `--page-size`：页面大小：A4/Letter/Legal/A3/A5（默认：A4）
- `--orientation`：页面方向：portrait/landscape（默认：portrait）
- `--margin-top/bottom/left/right`：边距（毫米，默认：20）
- `--font-family`：字体族（默认：Arial）
- `--font-size`：基础字体大小（默认：12）
- `--title`：文档标题（元数据）
- `--author`：作者名称（元数据）
- `--compress`：启用压缩以减小文件大小（默认：True）
- `--images`：图片路径列表（支持多个图片，用空格分隔）
- `--image-width`：图片宽度，如: 100%, 200px, 50mm（默认：100%）
- `--image-height`：图片高度，如: auto, 300px, 100mm（默认：auto）
- `--image-align`：图片对齐方式：left/center/right（默认：center）
- `--image-caption`：图片标题（应用于所有图片）

### 步骤 3：验证输出

检查生成的PDF：
- 文件是否存在
- 文件大小是否合理
- PDF是否有效（可读）

### 步骤 4：格式化结果

按以下格式呈现结果：

```markdown
**PDF生成成功**

**输出文件**：`<文件路径>`
**文件大小**：`<大小>`
**页数**：`<页数>`
**页面尺寸**：`<尺寸> (<方向>)`
**生成时间**：`<耗时>`

**文档属性**：
- 标题：`<标题>`
- 作者：`<作者>`
- 创建时间：`<时间>`

**状态**：✅ 成功 / ❌ 失败
```

## 操作示例

### 基本文本转PDF

```bash
python scripts/generate_pdf.py \
  --input-type text \
  --input "Hello World! This is a test PDF." \
  --output "hello.pdf"
```

### Markdown文档转PDF

```bash
python scripts/generate_pdf.py \
  --input-type markdown \
  --input-file "README.md" \
  --output "README.pdf" \
  --page-size A4 \
  --margin-top 25 \
  --margin-bottom 25
```

### HTML内容转PDF

```bash
python scripts/generate_pdf.py \
  --input-type html \
  --input "<h1>Report</h1><p>This is a report.</p>" \
  --output "report.pdf" \
  --title "Monthly Report" \
  --author "John Doe"
```

### 自定义样式

```bash
python scripts/generate_pdf.py \
  --input-type markdown \
  --input-file "document.md" \
  --output "styled.pdf" \
  --page-size Letter \
  --orientation landscape \
  --font-family "Times New Roman" \
  --font-size 14 \
  --margin-left 30 \
  --margin-right 30
```

### 带元数据的PDF

```bash
python scripts/generate_pdf.py \
  --input-type text \
  --input-file "content.txt" \
  --output "document.pdf" \
  --title "Project Documentation" \
  --author "Development Team" \
  --compress true
```

### 添加图片到PDF

#### 从本地文件添加单张图片
```bash
python scripts/generate_pdf.py \
  --input-type text \
  --input "报告内容" \
  --output "report_with_image.pdf" \
  --images "chart.png" \
  --image-width 80% \
  --image-align center \
  --image-caption "销售趋势图"
```

#### 添加多张图片
```bash
python scripts/generate_pdf.py \
  --input-type markdown \
  --input-file "article.md" \
  --output "article.pdf" \
  --images "fig1.png" "fig2.jpg" "diagram.svg" \
  --image-width 100% \
  --image-height auto \
  --image-align center \
  --image-caption "图表展示"
```

#### 自定义图片尺寸
```bash
python scripts/generate_pdf.py \
  --input-type html \
  --input "<h1>产品说明</h1><p>详细介绍...</p>" \
  --output "product.pdf" \
  --images "product_photo.jpg" \
  --image-width 300px \
  --image-height 200px \
  --image-align left
```

## 支持的输入格式

### 纯文本（text）
- 简单的文本内容
- 保留换行和基本格式
- 自动处理编码（UTF-8）

### Markdown（markdown）
- 标准Markdown语法支持
- 标题（H1-H6）
- 列表（有序/无序）
- 代码块
- 表格
- 链接和图片（嵌入base64）
- 引用块

### HTML（html）
- 基本HTML标签
- CSS样式（内联）
- 表格和列表
- **不支持**：JavaScript、外部资源、iframe

### 图片支持
- 支持格式：PNG、JPEG/JPG、GIF、SVG
- 图片来源：本地文件路径或base64数据URI
- 自动转换为base64嵌入PDF
- 可自定义宽度、高度、对齐方式
- 支持添加图片标题

## 页面配置选项

### 标准页面尺寸
- `A4`: 210mm × 297mm（默认）
- `Letter`: 216mm × 279mm（美国标准）
- `Legal`: 216mm × 356mm
- `A3`: 297mm × 420mm
- `A5`: 148mm × 210mm

### 页面方向
- `portrait`: 纵向（默认）
- `landscape`: 横向

### 边距设置
- 单位：毫米（mm）
- 默认值：20mm（所有边）
- 推荐范围：10-50mm

## 输出处理

### 大文件警告

如果PDF超过10MB：
1. 警告：`⚠️ 大型PDF生成 (<大小>)`
2. 建议："考虑启用压缩或减少内容"
3. 提示使用 `--compress true`

### 多页文档

对于超过20页的PDF：
1. 显示页数统计
2. 建议："考虑拆分为多个PDF"
3. 提供页面范围选项

### 错误处理

如果生成失败：
1. 显示错误类型（无效HTML、资源不足等）
2. 提供修复建议
3. 标记状态为 ❌ 失败

## 高级功能

### 批量转换

可以结合shell进行批量处理：
```bash
# 转换所有Markdown文件
for file in *.md; do
  python scripts/generate_pdf.py \
    --input-type markdown \
    --input-file "$file" \
    --output "${file%.md}.pdf"
done
```

### 从stdin读取

```bash
cat document.md | python scripts/generate_pdf.py \
  --input-type markdown \
  --input-file - \
  --output "output.pdf"
```

### 自定义CSS（HTML模式）

```bash
python scripts/generate_pdf.py \
  --input-type html \
  --input "<style>body { font-family: Arial; }</style><h1>Title</h1>" \
  --output "styled.pdf"
```

### 图片处理

#### 支持的图片格式
- **PNG**：适合图表、截图，支持透明背景
- **JPEG/JPG**：适合照片，文件较小
- **GIF**：支持简单动画（静态显示）
- **SVG**：矢量图形，无损缩放

#### 图片尺寸单位
- **百分比**：`100%`, `80%`, `50%`（相对于页面宽度）
- **像素**：`200px`, `300px`, `500px`
- **毫米**：`50mm`, `100mm`, `150mm`
- **自动**：`auto`（保持原始比例）

#### 图片最佳实践
1. **优化文件大小**：使用适当分辨率（150-300 DPI）
2. **选择合适格式**：照片用JPEG，图表用PNG
3. **避免过大图片**：单张图片建议小于5MB
4. **使用相对尺寸**：百分比更适应不同页面大小
5. **添加标题**：便于文档阅读和理解

#### 图片示例

```bash
# 添加产品图片到报告
python scripts/generate_pdf.py \
  --input-type markdown \
  --input-file "quarterly_report.md" \
  --output "Q1_Report.pdf" \
  --images "sales_chart.png" "team_photo.jpg" \
  --image-width 90% \
  --image-align center \
  --image-caption "2024年第一季度销售数据"

# 创建带图片的产品目录
python scripts/generate_pdf.py \
  --input-type html \
  --input-file "product_catalog.html" \
  --output "catalog.pdf" \
  --images "product1.jpg" "product2.jpg" "product3.jpg" \
  --image-width 200px \
  --image-height 150px \
  --image-align left
```

## 参考文档

有关详细的技术实现和限制：
- 参见 [references/html-security.md](references/html-security.md)
- 参见 [references/format-support.md](references/format-support.md)

## 最佳实践

1. **始终先验证**：HTML内容必须经过安全检查
2. **优化大文档**：对长文档启用压缩
3. **选择合适页面尺寸**：根据内容选择A4或Letter
4. **测试渲染**：复杂HTML先在浏览器中预览
5. **合理使用边距**：确保内容不会过于拥挤
6. **添加元数据**：便于文档管理和搜索

## 示例会话

### 示例 1：简单文本转PDF

**用户**："将这段文字保存为PDF：'会议记录：2024年1月15日'"

**助手**：
```bash
python scripts/validate_input.py "text" "inline"
# ✅ 验证通过

python scripts/generate_pdf.py \
  --input-type text \
  --input "会议记录：2024年1月15日" \
  --output "meeting_notes.pdf"
```

**输出**：
```markdown
**PDF生成成功**

**输出文件**：`meeting_notes.pdf`
**文件大小**：`2.3KB`
**页数**：`1`
**页面尺寸**：`A4 (纵向)`
**生成时间**：`0.5秒`

**状态**：✅ 成功
```

### 示例 2：Markdown文档转换

**用户**："把README.md转换成PDF"

**助手**：
```bash
python scripts/validate_input.py "markdown" "README.md"
# ✅ 验证通过

python scripts/generate_pdf.py \
  --input-type markdown \
  --input-file "README.md" \
  --output "README.pdf" \
  --page-size A4
```

**输出**：
```markdown
**PDF生成成功**

**输出文件**：`README.pdf`
**文件大小**：`156KB`
**页数**：`5`
**页面尺寸**：`A4 (纵向)`
**生成时间**：`1.2秒`

**状态**：✅ 成功
```

### 示例 3：HTML报告生成

**用户**："用HTML创建一个简单的报告并转为PDF"

**助手**：
```bash
python scripts/generate_pdf.py \
  --input-type html \
  --input "<h1>销售报告</h1><table><tr><td>产品</td><td>数量</td></tr><tr><td>A</td><td>100</td></tr></table>" \
  --output "sales_report.pdf" \
  --title "Sales Report Q1" \
  --author "Sales Team"
```

### 示例 4：危险操作（被拒绝）

**用户**：“生成包含<script>alert('xss')</script>的PDF”

**助手**：
```bash
python scripts/validate_input.py "html" "inline" --content-file "<script>alert('xss')</script>"
# ❌ 验证失败：检测到不安全的HTML内容
```

**响应**：
```
❌ 出于安全原因拒绝操作：

**原因**：HTML内容包含禁止的<script>标签
**风险**：可能导致代码注入攻击
**建议**：移除所有JavaScript代码，仅使用静态HTML

安全替代方案：
- 使用纯文本或Markdown格式
- 移除所有<script>、<iframe>标签
```

### 示例 5：添加图片到PDF

**用户**：“创建一个带图表的销售报告PDF”

**助手**：
```bash
python scripts/generate_pdf.py \
  --input-type markdown \
  --input "# 销售报告\n\n## 季度总结\n\n本季度销售额增长20%。" \
  --output "sales_report.pdf" \
  --images "sales_chart.png" \
  --image-width 80% \
  --image-align center \
  --image-caption "2024年Q1销售趋势图" \
  --title "销售报告" \
  --author "销售部"
```

**输出**：
```markdown
✅ PDF Generation Successful

Output File: sales_report.pdf
File Size: 245.6KB
Pages: 1
Page Size: A4 (portrait)
Generation Time: 1.8s
Title: 销售报告
Author: 销售部

📸 图片已添加到: sales_report_images.pdf

Status: ✅ Success
```

### 示例 6：多图片产品目录

**用户**：“为这3个产品创建带图片的目录PDF”

**助手**：
```bash
python scripts/generate_pdf.py \
  --input-type html \
  --input "<h1>产品目录</h1><p>以下是我们的主要产品。</p>" \
  --output "products.pdf" \
  --images "product_a.jpg" "product_b.jpg" "product_c.png" \
  --image-width 250px \
  --image-height 200px \
  --image-align center \
  --page-size Letter \
  --orientation landscape
```

---

**实现说明**：
- 使用weasyprint库进行PDF渲染（高质量、支持CSS）
- HTML内容经过严格的安全过滤
- 支持中文和其他Unicode字符
- 自动处理字体回退
- 内存优化，适合大文档处理
- **图片功能**：
  - 支持PNG、JPEG、GIF、SVG格式
  - 自动将本地图片转换为base64嵌入PDF
  - 可自定义图片尺寸、对齐方式和标题
  - 图片优化以减少文件大小
  - 支持多图片批量添加
