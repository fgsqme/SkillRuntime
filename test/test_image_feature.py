#!/usr/bin/env python3
"""
test_image_feature.py - 测试PDF生成器的图片功能
"""

import os
import sys
import subprocess
import tempfile
from PIL import Image, ImageDraw


def create_test_image(filepath, width=200, height=150, color='blue', text='Test Image'):
    """创建测试图片"""
    img = Image.new('RGB', (width, height), color=color)
    draw = ImageDraw.Draw(img)
    
    # 添加文字
    draw.text((10, 10), text, fill=(255, 255, 255))
    
    # 保存图片
    img.save(filepath)
    print(f"✅ 创建测试图片: {filepath}")


def test_single_image():
    """测试单张图片功能"""
    print("\n" + "="*60)
    print("测试 1: 单张图片添加到PDF")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试图片
        img_path = os.path.join(tmpdir, "test_chart.png")
        create_test_image(img_path, text="Sales Chart")
        
        # 生成带图片的PDF
        output_pdf = os.path.join(tmpdir, "report.pdf")
        
        cmd = [
            sys.executable, 
            "skills/pdf-generator/scripts/generate_pdf.py",
            "--input-type", "text",
            "--input", "销售报告\n\n本季度表现良好。",
            "--output", output_pdf,
            "--images", img_path,
            "--image-width", "80%",
            "--image-align", "center",
            "--image-caption", "销售趋势图"
        ]
        
        print(f"\n执行命令: {' '.join(cmd)}\n")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("输出:")
        print(result.stdout)
        if result.stderr:
            print("错误/警告:")
            print(result.stderr)
        
        # 检查文件是否存在
        if os.path.exists(output_pdf):
            size = os.path.getsize(output_pdf)
            print(f"\n✅ PDF生成成功: {output_pdf} ({size} bytes)")
        else:
            print(f"\n❌ PDF未生成")
        
        # 检查图片PDF是否存在
        images_pdf = output_pdf.replace('.pdf', '_images.pdf')
        if os.path.exists(images_pdf):
            size = os.path.getsize(images_pdf)
            print(f"✅ 图片PDF生成成功: {images_pdf} ({size} bytes)")
        else:
            print(f"⚠️ 图片PDF未生成")


def test_multiple_images():
    """测试多张图片功能"""
    print("\n" + "="*60)
    print("测试 2: 多张图片添加到PDF")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建多个测试图片
        img_paths = []
        colors = ['red', 'green', 'blue']
        for i, color in enumerate(colors, 1):
            img_path = os.path.join(tmpdir, f"product_{i}.jpg")
            create_test_image(img_path, color=color, text=f"Product {i}")
            img_paths.append(img_path)
        
        # 生成带多张图片的PDF
        output_pdf = os.path.join(tmpdir, "catalog.pdf")
        
        cmd = [
            sys.executable,
            "skills/pdf-generator/scripts/generate_pdf.py",
            "--input-type", "html",
            "--input", "<h1>产品目录</h1><p>展示我们的产品。</p>",
            "--output", output_pdf,
            "--images"
        ] + img_paths + [
            "--image-width", "200px",
            "--image-height", "150px",
            "--image-align", "center",
            "--image-caption", "产品展示"
        ]
        
        print(f"\n执行命令: {' '.join(cmd)}\n")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("输出:")
        print(result.stdout)
        if result.stderr:
            print("错误/警告:")
            print(result.stderr)
        
        # 检查文件
        images_pdf = output_pdf.replace('.pdf', '_images.pdf')
        if os.path.exists(images_pdf):
            size = os.path.getsize(images_pdf)
            print(f"\n✅ 多图片PDF生成成功: {images_pdf} ({size} bytes)")
        else:
            print(f"\n❌ 多图片PDF未生成")


def test_custom_dimensions():
    """测试自定义图片尺寸"""
    print("\n" + "="*60)
    print("测试 3: 自定义图片尺寸")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试图片
        img_path = os.path.join(tmpdir, "diagram.svg")
        # 创建简单的SVG
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200">
            <rect width="300" height="200" fill="lightblue"/>
            <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-size="20">Diagram</text>
        </svg>'''
        with open(img_path, 'w') as f:
            f.write(svg_content)
        
        # 生成PDF
        output_pdf = os.path.join(tmpdir, "diagram_report.pdf")
        
        cmd = [
            sys.executable,
            "skills/pdf-generator/scripts/generate_pdf.py",
            "--input-type", "markdown",
            "--input", "# 技术图表\n\n以下是系统架构图。",
            "--output", output_pdf,
            "--images", img_path,
            "--image-width", "150mm",
            "--image-height", "100mm",
            "--image-align", "left",
            "--image-caption", "系统架构图"
        ]
        
        print(f"\n执行命令: {' '.join(cmd)}\n")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print("输出:")
        print(result.stdout)
        if result.stderr:
            print("错误/警告:")
            print(result.stderr)
        
        # 检查文件
        images_pdf = output_pdf.replace('.pdf', '_images.pdf')
        if os.path.exists(images_pdf):
            size = os.path.getsize(images_pdf)
            print(f"\n✅ 自定义尺寸PDF生成成功: {images_pdf} ({size} bytes)")
        else:
            print(f"\n❌ 自定义尺寸PDF未生成")


def main():
    """运行所有测试"""
    print("🧪 PDF生成器图片功能测试")
    print("="*60)
    
    try:
        test_single_image()
        test_multiple_images()
        test_custom_dimensions()
        
        print("\n" + "="*60)
        print("✅ 所有测试完成!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
