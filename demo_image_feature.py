#!/usr/bin/env python3
"""
demo_image_feature.py - PDF生成器图片功能演示

这个脚本演示如何使用PDF生成器的图片功能。
"""

import os
import sys
import subprocess
from PIL import Image, ImageDraw


def create_demo_images():
    """创建演示用的测试图片"""
    print("📸 创建演示图片...")
    
    # 创建输出目录
    demo_dir = "pdf_demo_images"
    os.makedirs(demo_dir, exist_ok=True)
    
    # 1. 创建柱状图样式的PNG
    img1 = Image.new('RGB', (400, 300), color='white')
    draw1 = ImageDraw.Draw(img1)
    # 绘制简单的柱状图
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    for i, color in enumerate(colors):
        x = 50 + i * 80
        height = [150, 200, 120, 180][i]
        draw1.rectangle([x, 250-height, x+60, 250], fill=color)
    draw1.text((50, 10), "Sales Chart", fill='black')
    img1.save(f"{demo_dir}/sales_chart.png")
    print(f"  ✅ {demo_dir}/sales_chart.png")
    
    # 2. 创建产品照片样式的JPEG
    img2 = Image.new('RGB', (300, 200), color='lightblue')
    draw2 = ImageDraw.Draw(img2)
    draw2.rectangle([50, 50, 250, 150], fill='white')
    draw2.text((80, 90), "Product A", fill='black')
    img2.save(f"{demo_dir}/product_a.jpg", quality=85)
    print(f"  ✅ {demo_dir}/product_a.jpg")
    
    # 3. 创建流程图样式的PNG
    img3 = Image.new('RGB', (500, 250), color='white')
    draw3 = ImageDraw.Draw(img3)
    # 绘制简单流程
    draw3.rectangle([50, 100, 150, 150], fill='#E3F2FD', outline='#1976D2')
    draw3.text((75, 115), "Start", fill='#1976D2')
    draw3.line([150, 125, 200, 125], fill='black', width=2)
    draw3.rectangle([200, 100, 300, 150], fill='#FFF3E0', outline='#F57C00')
    draw3.text((220, 115), "Process", fill='#F57C00')
    draw3.line([300, 125, 350, 125], fill='black', width=2)
    draw3.rectangle([350, 100, 450, 150], fill='#E8F5E9', outline='#388E3C')
    draw3.text((375, 115), "End", fill='#388E3C')
    draw3.text((150, 20), "System Flow", fill='black')
    img3.save(f"{demo_dir}/flow_diagram.png")
    print(f"  ✅ {demo_dir}/flow_diagram.png")
    
    return demo_dir


def run_demo_1_single_image(demo_dir):
    """演示1: 添加单张图片到报告"""
    print("\n" + "="*70)
    print("📄 演示 1: 在销售报告中添加图表")
    print("="*70)
    
    output_pdf = f"{demo_dir}/report_with_chart.pdf"
    
    cmd = [
        sys.executable,
        "skills/pdf-generator/scripts/generate_pdf.py",
        "--input-type", "markdown",
        "--input", "# Q1 销售报告\n\n## 摘要\n\n本季度销售额增长了20%,主要得益于新产品的推出。\n\n## 详细数据\n\n详见下方图表。",
        "--output", output_pdf,
        "--images", f"{demo_dir}/sales_chart.png",
        "--image-width", "80%",
        "--image-align", "center",
        "--image-caption", "图1: 各产品线销售对比",
        "--title", "Q1销售报告",
        "--author", "销售部",
        "--page-size", "A4"
    ]
    
    print(f"\n执行命令:")
    print("python skills/pdf-generator/scripts/generate_pdf.py \\")
    print("  --input-type markdown \\")
    print("  --input '# Q1 销售报告...' \\")
    print(f"  --output {output_pdf} \\")
    print(f"  --images {demo_dir}/sales_chart.png \\")
    print("  --image-width 80% \\")
    print("  --image-align center \\")
    print("  --image-caption '图1: 各产品线销售对比'")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("\n输出:")
    print(result.stdout)
    if result.stderr and "Warning" not in result.stderr:
        print("错误/警告:")
        print(result.stderr)
    
    images_pdf = output_pdf.replace('.pdf', '_images.pdf')
    if os.path.exists(images_pdf):
        size = os.path.getsize(images_pdf)
        print(f"\n✅ 成功! 查看文件: {images_pdf} ({size/1024:.1f}KB)")


def run_demo_2_multiple_images(demo_dir):
    """演示2: 添加多张图片到产品目录"""
    print("\n" + "="*70)
    print("📦 演示 2: 创建带多张图片的产品目录")
    print("="*70)
    
    output_pdf = f"{demo_dir}/product_catalog.pdf"
    
    cmd = [
        sys.executable,
        "skills/pdf-generator/scripts/generate_pdf.py",
        "--input-type", "html",
        "--input", "<h1>产品目录</h1><p>以下是我们的明星产品系列。</p>",
        "--output", output_pdf,
        "--images", 
        f"{demo_dir}/product_a.jpg",
        f"{demo_dir}/flow_diagram.png",
        "--image-width", "250px",
        "--image-height", "auto",
        "--image-align", "center",
        "--image-caption", "产品展示与流程图",
        "--page-size", "Letter",
        "--orientation", "landscape"
    ]
    
    print(f"\n执行命令:")
    print("python skills/pdf-generator/scripts/generate_pdf.py \\")
    print("  --input-type html \\")
    print("  --input '<h1>产品目录</h1>...' \\")
    print(f"  --output {output_pdf} \\")
    print(f"  --images {demo_dir}/product_a.jpg {demo_dir}/flow_diagram.png \\")
    print("  --image-width 250px \\")
    print("  --image-align center \\")
    print("  --orientation landscape")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("\n输出:")
    print(result.stdout)
    if result.stderr and "Warning" not in result.stderr:
        print("错误/警告:")
        print(result.stderr)
    
    images_pdf = output_pdf.replace('.pdf', '_images.pdf')
    if os.path.exists(images_pdf):
        size = os.path.getsize(images_pdf)
        print(f"\n✅ 成功! 查看文件: {images_pdf} ({size/1024:.1f}KB)")


def run_demo_3_custom_dimensions(demo_dir):
    """演示3: 自定义图片尺寸"""
    print("\n" + "="*70)
    print("📐 演示 3: 使用自定义尺寸的技术文档")
    print("="*70)
    
    output_pdf = f"{demo_dir}/tech_doc.pdf"
    
    cmd = [
        sys.executable,
        "skills/pdf-generator/scripts/generate_pdf.py",
        "--input-type", "text",
        "--input", "系统架构说明文档\n\n本文档描述了系统的整体架构和数据流向。",
        "--output", output_pdf,
        "--images", f"{demo_dir}/flow_diagram.png",
        "--image-width", "180mm",
        "--image-height", "90mm",
        "--image-align", "center",
        "--image-caption", "系统架构图 - 展示主要组件和数据流",
        "--font-family", "Arial",
        "--font-size", "11"
    ]
    
    print(f"\n执行命令:")
    print("python skills/pdf-generator/scripts/generate_pdf.py \\")
    print("  --input-type text \\")
    print("  --input '系统架构说明文档...' \\")
    print(f"  --output {output_pdf} \\")
    print(f"  --images {demo_dir}/flow_diagram.png \\")
    print("  --image-width 180mm \\")
    print("  --image-height 90mm \\")
    print("  --image-caption '系统架构图'")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("\n输出:")
    print(result.stdout)
    if result.stderr and "Warning" not in result.stderr:
        print("错误/警告:")
        print(result.stderr)
    
    images_pdf = output_pdf.replace('.pdf', '_images.pdf')
    if os.path.exists(images_pdf):
        size = os.path.getsize(images_pdf)
        print(f"\n✅ 成功! 查看文件: {images_pdf} ({size/1024:.1f}KB)")


def main():
    """主函数"""
    print("\n" + "="*70)
    print("🎨 PDF生成器图片功能演示")
    print("="*70)
    print("\n这个演示将展示如何使用PDF生成器的图片功能。")
    print("我们将创建示例图片并生成包含这些图片的PDF文档。\n")
    
    try:
        # 创建演示图片
        demo_dir = create_demo_images()
        
        # 运行演示
        run_demo_1_single_image(demo_dir)
        run_demo_2_multiple_images(demo_dir)
        run_demo_3_custom_dimensions(demo_dir)
        
        print("\n" + "="*70)
        print("✅ 所有演示完成!")
        print("="*70)
        print(f"\n生成的文件位于: {demo_dir}/ 目录")
        print("\n提示:")
        print("  - 查看 *_images.pdf 文件以看到包含图片的PDF")
        print("  - 可以使用任何PDF阅读器打开这些文件")
        print("  - 参见 IMAGE_USAGE.md 了解更多使用方法\n")
        
    except Exception as e:
        print(f"\n❌ 演示失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
