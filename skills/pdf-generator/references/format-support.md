# 格式支持指南

本文档详细说明PDF生成器支持的输入格式和转换选项。

## 支持的输入格式

### 1. 纯文本（text）

最简单的格式，适合基本文档。

**特点：**
- 保留换行符
- 自动处理编码（UTF-8）
- 使用等宽字体显示

**示例：**
```
这是一个纯文本文档。

它保留了所有换行和空格。

适合简单的笔记和日志。
```

**使用方式：**
```bash
python scripts/generate_pdf.py \
  --input-type text \
  --input "这是内容" \
  --output "output.pdf"
```

### 2. Markdown（markdown）

功能丰富的标记语言，适合技术文档。

**支持的语法：**

#### 标题
```markdown
# H1 标题
## H2 标题
### H3 标题
#### H4 标题
##### H5 标题
###### H6 标题
```

#### 强调
```markdown
*斜体* 或 _斜体_
**粗体** 或 __粗体__
***粗斜体***
~~删除线~~
```

#### 列表
```markdown
无序列表：
- 项目一
- 项目二
  - 子项目

有序列表：
1. 第一步
2. 第二步
3. 第三步
```

#### 链接和图片
```markdown
[链接文本](https://example.com)

![图片描述](image.png)
```

#### 代码
```markdown
行内代码：`code()`

代码块：
```python
def hello():
    print("Hello, World!")
```
```

#### 表格
```markdown
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| A   | B   | C   |
| D   | E   | F   |
```

#### 引用
```markdown
> 这是一段引用文本。
> 
> 可以有多行。
```

#### 水平线
```markdown
---
```

**使用方式：**
```bash
python scripts/generate_pdf.py \
  --input-type markdown \
  --input-file "document.md" \
  --output "document.pdf"
```

### 3. HTML（html）

最灵活的格式，完全控制样式。

**支持的HTML元素：**

#### 文本元素
- `<h1>` - `<h6>`：标题
- `<p>`：段落
- `<strong>`, `<b>`：粗体
- `<em>`, `<i>`：斜体
- `<code>`：行内代码
- `<pre>`：预格式化文本
- `<blockquote>`：引用块
- `<hr>`：水平线

#### 列表
- `<ul>`, `<ol>`, `<li>`：列表
- `<dl>`, `<dt>`, `<dd>`：定义列表

#### 表格
- `<table>`, `<thead>`, `<tbody>`, `<tfoot>`
- `<tr>`, `<th>`, `<td>`

#### 链接和图片
- `<a href="...">`：链接
- `<img src="..." alt="...">`：图片

#### 容器
- `<div>`, `<span>`：通用容器
- `<header>`, `<footer>`, `<section>`, `<article>`：语义化标签

**使用方式：**
```bash
python scripts/generate_pdf.py \
  --input-type html \
  --input "<h1>Title</h1><p>Content</p>" \
  --output "output.pdf"
```

## 页面配置

### 页面尺寸

| 尺寸 | 宽度 × 高度 | 用途 |
|------|------------|------|
| A4 | 210mm × 297mm | 国际标准（默认） |
| Letter | 216mm × 279mm | 美国标准 |
| Legal | 216mm × 356mm | 法律文档 |
| A3 | 297mm × 420mm | 海报、图表 |
| A5 | 148mm × 210mm | 小册子 |

**使用示例：**
```bash
--page-size A4
--page-size Letter
--page-size Legal
```

### 页面方向

- `portrait`：纵向（默认）
- `landscape`：横向

**使用示例：**
```bash
--orientation portrait
--orientation landscape
```

### 边距设置

所有边距单位都是毫米（mm）。

**推荐值：**
- 标准文档：20mm
- 正式文档：25mm
- 最小边距：10mm
- 最大边距：50mm

**使用示例：**
```bash
--margin-top 25
--margin-bottom 25
--margin-left 20
--margin-right 20
```

## 字体配置

### 字体族

**常用字体：**
- `Arial`：无衬线字体（默认）
- `Times New Roman`：衬线字体
- `Courier New`：等宽字体
- `Helvetica`：无衬线字体
- `Georgia`：衬线字体

**中文字体：**
- `SimSun`：宋体
- `SimHei`：黑体
- `Microsoft YaHei`：微软雅黑
- `KaiTi`：楷体

**使用示例：**
```bash
--font-family "Arial"
--font-family "Microsoft YaHei"
```

### 字体大小

**推荐值：**
- 正文：10-12pt（默认12pt）
- 小字：8-10pt
- 大字：14-16pt
- 标题：自动缩放

**使用示例：**
```bash
--font-size 12
--font-size 14
```

## 文档元数据

### 标题

添加到PDF的元数据中，便于搜索和管理。

```bash
--title "月度报告"
```

### 作者

```bash
--author "张三"
```

### 查看元数据

生成的PDF包含以下元数据：
- 标题（Title）
- 作者（Author）
- 创建日期（Creation Date）
- 生成工具（Producer: WeasyPrint）

## 压缩选项

### 启用压缩

压缩可以显著减小文件大小，特别是包含图片的文档。

```bash
--compress true   # 启用压缩（默认）
--compress false  # 禁用压缩
```

**压缩效果：**
- 纯文本文档：减少10-20%
- 含图片文档：减少30-50%
- 复杂HTML：减少20-40%

## 高级功能

### 页眉和页脚

通过CSS添加：

```html
<style>
@page {
    @top-center {
        content: "文档标题";
        font-size: 9pt;
        color: #666;
    }
    
    @bottom-center {
        content: counter(page);
        font-size: 9pt;
        color: #666;
    }
}
</style>
```

### 分页控制

强制分页：

```html
<div style="page-break-after: always;">
    第一页内容
</div>

<div>
    第二页内容
</div>
```

避免分页：

```html
<div style="page-break-inside: avoid;">
    这段内容不会被分页打断
</div>
```

### 目录生成

Markdown自动为标题生成锚点，但PDF中需要手动创建目录：

```markdown
# 目录

1. [第一章](#第一章)
2. [第二章](#第二章)

# 第一章

内容...

# 第二章

内容...
```

## 性能优化

### 大文档处理

对于超过50页的文档：

1. **启用压缩**：`--compress true`
2. **优化图片**：使用适当分辨率
3. **简化样式**：减少复杂CSS
4. **分批生成**：考虑拆分为多个PDF

### 图片优化

**最佳实践：**
- 使用JPEG格式照片
- 使用PNG格式图表
- 分辨率：150-300 DPI足够
- 避免过大的base64图片

**示例：**
```html
<!-- ✅ 优化后的图片 -->
<img src="data:image/jpeg;base64,/9j/4AAQ..." alt="描述">

<!-- ❌ 过大的图片 -->
<img src="data:image/png;base64,iVBORw0KGgoAAA..." alt="描述">
```

## 常见问题

### Q1: 中文显示为方框？

**A:** 确保使用了支持中文的字体：

```bash
--font-family "Microsoft YaHei"
```

或在HTML中：
```html
<style>
body {
    font-family: "Microsoft YaHei", Arial, sans-serif;
}
</style>
```

### Q2: 表格边框不显示？

**A:** 明确设置边框样式：

```html
<table style="border-collapse: collapse;">
    <tr>
        <td style="border: 1px solid black;">单元格</td>
    </tr>
</table>
```

### Q3: 图片不显示？

**A:** 检查以下几点：
1. 使用base64编码
2. 验证base64字符串完整性
3. 确认图片格式支持（PNG、JPEG、SVG）

### Q4: PDF文件过大？

**A:** 优化方法：
1. 启用压缩：`--compress true`
2. 降低图片分辨率
3. 移除不必要的样式
4. 使用矢量图形代替位图

## 格式对比

| 特性 | Text | Markdown | HTML |
|------|------|----------|------|
| 易用性 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| 灵活性 | ⭐ | ⭐⭐ | ⭐⭐⭐ |
| 样式控制 | ⭐ | ⭐⭐ | ⭐⭐⭐ |
| 学习曲线 | 低 | 中 | 高 |
| 适用场景 | 简单文档 | 技术文档 | 复杂布局 |

## 选择建议

**使用Text：**
- 简单的笔记或日志
- 不需要格式化的内容
- 快速生成

**使用Markdown：**
- 技术文档
- README文件
- 博客文章
- 需要基本格式的内容

**使用HTML：**
- 复杂的报表
- 需要精确控制的布局
- 包含表格和图表
- 企业级文档

## 参考资料

- [Markdown语法指南](https://www.markdownguide.org/)
- [WeasyPrint文档](https://weasyprint.readthedocs.io/)
- [CSS Paged Media](https://www.w3.org/TR/css-page-3/)
