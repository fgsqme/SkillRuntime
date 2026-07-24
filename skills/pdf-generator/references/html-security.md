# HTML安全指南

本文档说明PDF生成器中HTML内容的安全限制和最佳实践。

## 安全限制

### 禁止的HTML元素

以下HTML元素在PDF生成中被严格禁止：

1. **`<script>` 标签**
   - 原因：可能执行恶意JavaScript代码
   - 替代方案：使用纯静态HTML

2. **`<iframe>` 标签**
   - 原因：可能加载外部恶意内容
   - 替代方案：直接嵌入所需内容

3. **`<object>` 和 `<embed>` 标签**
   - 原因：可能加载外部插件或资源
   - 替代方案：使用内联内容

4. **`<form>` 标签**
   - 原因：PDF是静态文档，不支持交互表单
   - 替代方案：展示表单数据为表格

5. **`<applet>` 标签**
   - 原因：已废弃且存在安全风险

### 内联事件处理器

以下JavaScript事件属性将被忽略（不执行）：

- `onclick`, `onload`, `onerror`
- `onmouseover`, `onmouseout`
- `onsubmit`, `onchange`
- 所有其他 `on*` 事件

**示例：**
```html
<!-- ❌ 不安全 - 将被忽略 -->
<button onclick="alert('XSS')">Click me</button>

<!-- ✅ 安全 - 纯静态 -->
<button style="padding: 10px;">Click me</button>
```

### 外部资源

外部资源引用会受到限制：

1. **外部CSS/JS文件**
   - 警告：可能在离线环境中无法加载
   - 建议：使用内联样式

2. **外部图片**
   - 警告：需要网络连接
   - 建议：使用base64编码的图片或本地路径

3. **Web字体**
   - 警告：可能需要下载
   - 建议：使用系统字体

## 安全的HTML示例

### 基本结构

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Document Title</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            font-size: 12pt;
            line-height: 1.6;
        }
        h1 {
            color: #333;
            border-bottom: 2px solid #007bff;
        }
    </style>
</head>
<body>
    <h1>标题</h1>
    <p>这是一个段落。</p>
</body>
</html>
```

### 表格

```html
<table>
    <thead>
        <tr>
            <th>姓名</th>
            <th>年龄</th>
            <th>城市</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>张三</td>
            <td>25</td>
            <td>北京</td>
        </tr>
        <tr>
            <td>李四</td>
            <td>30</td>
            <td>上海</td>
        </tr>
    </tbody>
</table>
```

### 列表

```html
<ul>
    <li>项目一</li>
    <li>项目二</li>
    <li>项目三</li>
</ul>

<ol>
    <li>第一步</li>
    <li>第二步</li>
    <li>第三步</li>
</ol>
```

### 代码块

```html
<pre><code>
def hello():
    print("Hello, World!")
</code></pre>
```

### 引用块

```html
<blockquote>
    <p>这是一段引用文本。</p>
    <footer>— 作者</footer>
</blockquote>
```

## CSS支持

### 支持的CSS属性

WeasyPrint支持大多数CSS属性：

- **布局**：margin, padding, width, height
- **字体**：font-family, font-size, font-weight
- **颜色**：color, background-color
- **边框**：border, border-radius
- **文本**：text-align, text-decoration, line-height

### 不支持的CSS特性

- CSS Grid（部分支持）
- Flexbox（有限支持）
- CSS动画和过渡
- @media查询（PDF是固定格式）

### 页面样式

```css
@page {
    size: A4 portrait;
    margin: 20mm;
    
    @top-center {
        content: "页眉文本";
    }
    
    @bottom-center {
        content: counter(page);
    }
}
```

## 最佳实践

### 1. 使用内联样式

```html
<!-- ✅ 推荐 -->
<div style="color: red; font-weight: bold;">重要文本</div>

<!-- ⚠️ 避免外部CSS -->
<link rel="stylesheet" href="styles.css">
```

### 2. 嵌入图片

```html
<!-- ✅ Base64编码 -->
<img src="data:image/png;base64,iVBORw0KGgo..." alt="描述">

<!-- ⚠️ 外部URL（可能失败） -->
<img src="https://example.com/image.png" alt="描述">
```

### 3. 简化布局

```html
<!-- ✅ 简单表格布局 -->
<table>
    <tr>
        <td>左侧内容</td>
        <td>右侧内容</td>
    </tr>
</table>

<!-- ⚠️ 复杂CSS Grid -->
<div style="display: grid; grid-template-columns: 1fr 1fr;">
    ...
</div>
```

### 4. 测试渲染

在生成PDF之前：
1. 在浏览器中预览HTML
2. 检查是否有JavaScript依赖
3. 验证所有资源都可访问
4. 测试不同页面尺寸

## 安全检查清单

在提交HTML内容之前，确保：

- [ ] 没有 `<script>` 标签
- [ ] 没有 `<iframe>` 标签
- [ ] 没有内联JavaScript事件
- [ ] 所有外部资源都可用
- [ ] CSS样式是内联的
- [ ] 图片使用base64或本地路径
- [ ] 内容大小不超过1MB
- [ ] 使用了有效的HTML语法

## 常见错误

### 错误1：脚本标签

```html
<!-- ❌ 错误 -->
<script>alert('test');</script>

<!-- ✅ 修正 -->
<!-- 移除所有脚本 -->
```

### 错误2：外部资源

```html
<!-- ❌ 可能失败 -->
<img src="https://example.com/logo.png">

<!-- ✅ 可靠 -->
<img src="data:image/png;base64,...">
```

### 错误3：复杂布局

```html
<!-- ❌ 可能渲染不正确 -->
<div style="display: flex; justify-content: space-between;">

<!-- ✅ 更可靠 -->
<table style="width: 100%;">
    <tr>
        <td>左侧</td>
        <td style="text-align: right;">右侧</td>
    </tr>
</table>
```

## 故障排除

### PDF生成失败

**症状**：生成过程中出现错误

**解决方案**：
1. 检查HTML语法是否正确
2. 移除所有JavaScript代码
3. 简化CSS样式
4. 验证字符编码（UTF-8）

### 样式未应用

**症状**：CSS样式在PDF中不显示

**解决方案**：
1. 确保样式是内联的或在`<style>`标签中
2. 检查CSS属性是否被WeasyPrint支持
3. 避免使用CSS变量

### 图片缺失

**症状**：PDF中图片不显示

**解决方案**：
1. 使用base64编码图片
2. 检查图片路径是否正确
3. 验证图片格式（PNG、JPEG、SVG）

## 参考资料

- [WeasyPrint文档](https://weasyprint.readthedocs.io/)
- [CSS Paged Media规范](https://www.w3.org/TR/css-page-3/)
- [HTML5规范](https://html.spec.whatwg.org/)
