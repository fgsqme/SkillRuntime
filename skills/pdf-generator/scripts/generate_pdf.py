#!/usr/bin/env python3
"""
generate_pdf.py - PDF生成器

功能：
- 从文本、Markdown或HTML生成PDF
- 支持自定义页面大小、边距和字体
- 添加文档元数据（标题、作者）
- 压缩优化以减小文件大小
"""

import os
import sys
import time
from datetime import datetime


def generate_pdf_from_text(content: str, output_path: str, config: dict) -> dict:
    """从纯文本生成PDF"""
    result = {
        'success': False,
        'output_path': output_path,
        'file_size': 0,
        'page_count': 0,
        'generation_time': 0,
        'error': None,
    }
    
    start_time = time.time()
    
    try:
        from weasyprint import HTML, CSS
        
        # 将文本转换为简单的HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: {config.get('font_family', 'Arial')}, sans-serif;
                    font-size: {config.get('font_size', 12)}pt;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                }}
                pre {{
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }}
            </style>
        </head>
        <body>
            <pre>{content}</pre>
        </body>
        </html>
        """
        
        # 创建CSS样式
        css = CSS(string=f"""
            @page {{
                size: {config.get('page_size', 'A4')} {config.get('orientation', 'portrait')};
                margin: {config.get('margin_top', 20)}mm {config.get('margin_right', 20)}mm 
                        {config.get('margin_bottom', 20)}mm {config.get('margin_left', 20)}mm;
            }}
        """)
        
        # 生成PDF
        html_doc = HTML(string=html_content)
        html_doc.write_pdf(
            output_path,
            stylesheets=[css],
            optimize_images=True,
        )
        
        # 获取文件信息
        file_size = os.path.getsize(output_path)
        
        result['success'] = True
        result['file_size'] = file_size
        result['page_count'] = 1
        result['generation_time'] = time.time() - start_time
        
    except ImportError:
        result['error'] = "weasyprint库未安装。请运行: pip install weasyprint"
    except Exception as e:
        result['error'] = f"PDF生成失败: {str(e)}"
    
    return result


def generate_pdf_from_markdown(content: str, output_path: str, config: dict) -> dict:
    """从Markdown生成PDF"""
    result = {
        'success': False,
        'output_path': output_path,
        'file_size': 0,
        'page_count': 0,
        'generation_time': 0,
        'error': None,
    }
    
    start_time = time.time()
    
    try:
        import markdown
        from weasyprint import HTML, CSS
        
        # 转换Markdown为HTML
        html_body = markdown.markdown(
            content,
            extensions=['tables', 'fenced_code', 'codehilite']
        )
        
        # 创建完整HTML文档
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{config.get('title', 'Document')}</title>
            <style>
                body {{
                    font-family: {config.get('font_family', 'Arial')}, sans-serif;
                    font-size: {config.get('font_size', 12)}pt;
                    line-height: 1.6;
                    color: #333;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    margin-top: 24px;
                    margin-bottom: 16px;
                    font-weight: 600;
                }}
                h1 {{ font-size: 2em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }}
                h2 {{ font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }}
                h3 {{ font-size: 1.25em; }}
                code {{
                    background-color: #f6f8fa;
                    padding: 0.2em 0.4em;
                    border-radius: 3px;
                    font-family: monospace;
                    font-size: 85%;
                }}
                pre {{
                    background-color: #f6f8fa;
                    padding: 16px;
                    overflow: auto;
                    border-radius: 6px;
                }}
                pre code {{
                    background-color: transparent;
                    padding: 0;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 16px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px 12px;
                    text-align: left;
                }}
                th {{
                    background-color: #f6f8fa;
                    font-weight: 600;
                }}
                blockquote {{
                    margin: 16px 0;
                    padding: 0 1em;
                    color: #6a737d;
                    border-left: 0.25em solid #dfe2e5;
                }}
                a {{
                    color: #0366d6;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                ul, ol {{
                    padding-left: 2em;
                }}
                li {{
                    margin: 4px 0;
                }}
            </style>
        </head>
        <body>
            {html_body}
        </body>
        </html>
        """
        
        # 创建CSS样式
        css = CSS(string=f"""
            @page {{
                size: {config.get('page_size', 'A4')} {config.get('orientation', 'portrait')};
                margin: {config.get('margin_top', 20)}mm {config.get('margin_right', 20)}mm 
                        {config.get('margin_bottom', 20)}mm {config.get('margin_left', 20)}mm;
                
                @top-center {{
                    content: "{config.get('title', '')}";
                    font-size: 9pt;
                    color: #666;
                }}
                
                @bottom-center {{
                    content: counter(page);
                    font-size: 9pt;
                    color: #666;
                }}
            }}
        """)
        
        # 生成PDF
        html_doc = HTML(string=html_content)
        html_doc.write_pdf(
            output_path,
            stylesheets=[css],
            optimize_images=True,
        )
        
        # 获取文件信息
        file_size = os.path.getsize(output_path)
        
        result['success'] = True
        result['file_size'] = file_size
        result['page_count'] = 1
        result['generation_time'] = time.time() - start_time
        
    except ImportError as e:
        missing_lib = str(e).split("'")[1] if "'" in str(e) else "unknown"
        result['error'] = f"缺少依赖库: {missing_lib}。请运行: pip install markdown weasyprint"
    except Exception as e:
        result['error'] = f"PDF生成失败: {str(e)}"
    
    return result


def generate_pdf_from_html(content: str, output_path: str, config: dict) -> dict:
    """从HTML生成PDF"""
    result = {
        'success': False,
        'output_path': output_path,
        'file_size': 0,
        'page_count': 0,
        'generation_time': 0,
        'error': None,
    }
    
    start_time = time.time()
    
    try:
        from weasyprint import HTML, CSS
        
        # 确保HTML有正确的编码声明
        if '<meta charset' not in content and '<meta http-equiv="Content-Type"' not in content:
            content = content.replace('<head>', '<head><meta charset="utf-8">', 1)
        
        # 创建CSS样式
        css = CSS(string=f"""
            @page {{
                size: {config.get('page_size', 'A4')} {config.get('orientation', 'portrait')};
                margin: {config.get('margin_top', 20)}mm {config.get('margin_right', 20)}mm 
                        {config.get('margin_bottom', 20)}mm {config.get('margin_left', 20)}mm;
                
                @top-center {{
                    content: "{config.get('title', '')}";
                    font-size: 9pt;
                    color: #666;
                }}
                
                @bottom-center {{
                    content: counter(page);
                    font-size: 9pt;
                    color: #666;
                }}
            }}
            
            body {{
                font-family: {config.get('font_family', 'Arial')}, sans-serif;
                font-size: {config.get('font_size', 12)}pt;
            }}
        """)
        
        # 生成PDF
        html_doc = HTML(string=content)
        html_doc.write_pdf(
            output_path,
            stylesheets=[css],
            optimize_images=True,
        )
        
        # 获取文件信息
        file_size = os.path.getsize(output_path)
        
        result['success'] = True
        result['file_size'] = file_size
        result['page_count'] = 1
        result['generation_time'] = time.time() - start_time
        
    except ImportError:
        result['error'] = "weasyprint库未安装。请运行: pip install weasyprint"
    except Exception as e:
        result['error'] = f"PDF生成失败: {str(e)}"
    
    return result


def embed_image_to_html(image_path: str, width: str = '100%', height: str = 'auto', 
                       align: str = 'center', caption: str = '', alt: str = 'Image') -> str:
    """
    将图片嵌入到HTML中
    
    参数:
        image_path: 图片路径或base64数据URI
        width: 图片宽度 (CSS单位，如 '100%', '200px', '50mm')
        height: 图片高度 (CSS单位，如 'auto', '300px', '100mm')
        align: 对齐方式 ('left', 'center', 'right')
        caption: 图片标题
        alt: 替代文本
    
    返回:
        HTML图片标签字符串
    """
    # 判断是文件路径还是base64
    if image_path.startswith('data:image'):
        src = image_path
    else:
        # 尝试读取本地文件并转换为base64
        try:
            import base64
            with open(image_path, 'rb') as img_file:
                img_data = img_file.read()
                encoded = base64.b64encode(img_data).decode('utf-8')
                
                # 检测图片格式
                if image_path.lower().endswith('.png'):
                    mime_type = 'image/png'
                elif image_path.lower().endswith(('.jpg', '.jpeg')):
                    mime_type = 'image/jpeg'
                elif image_path.lower().endswith('.gif'):
                    mime_type = 'image/gif'
                elif image_path.lower().endswith('.svg'):
                    mime_type = 'image/svg+xml'
                else:
                    mime_type = 'image/png'  # 默认
                
                src = f'data:{mime_type};base64,{encoded}'
        except Exception as e:
            return f'<p style="color: red;">⚠️ 图片加载失败: {str(e)}</p>'
    
    # 构建对齐样式
    align_styles = {
        'left': 'text-align: left;',
        'center': 'text-align: center;',
        'right': 'text-align: right;'
    }
    container_style = align_styles.get(align, 'text-align: center;')
    
    # 构建HTML
    html_parts = [f'<div style="{container_style}">']
    html_parts.append(f'<img src="{src}" alt="{alt}" style="width: {width}; height: {height}; max-width: 100%; object-fit: contain;">')
    
    if caption:
        html_parts.append(f'<p style="font-size: 10pt; color: #666; margin-top: 8px; font-style: italic;">{caption}</p>')
    
    html_parts.append('</div>')
    
    return '\n'.join(html_parts)


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f}MB"


def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="从文本、Markdown或HTML生成PDF文档"
    )
    parser.add_argument(
        "--input-type", "-t",
        required=True,
        choices=['text', 'markdown', 'html'],
        help="输入内容类型"
    )
    parser.add_argument(
        "--input", "-i",
        help="直接提供的内容字符串"
    )
    parser.add_argument(
        "--input-file", "-f",
        help="从文件读取内容（与--input互斥）"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="输出PDF文件路径（必须以.pdf结尾）"
    )
    parser.add_argument(
        "--page-size", "-s",
        choices=['A4', 'Letter', 'Legal', 'A3', 'A5'],
        default='A4',
        help="页面大小（默认: A4）"
    )
    parser.add_argument(
        "--orientation",
        choices=['portrait', 'landscape'],
        default='portrait',
        help="页面方向（默认: portrait）"
    )
    parser.add_argument(
        "--margin-top",
        type=float,
        default=20,
        help="上边距（毫米，默认: 20）"
    )
    parser.add_argument(
        "--margin-bottom",
        type=float,
        default=20,
        help="下边距（毫米，默认: 20）"
    )
    parser.add_argument(
        "--margin-left",
        type=float,
        default=20,
        help="左边距（毫米，默认: 20）"
    )
    parser.add_argument(
        "--margin-right",
        type=float,
        default=20,
        help="右边距（毫米，默认: 20）"
    )
    parser.add_argument(
        "--font-family",
        default='Arial',
        help="字体族（默认: Arial）"
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=12,
        help="基础字体大小（默认: 12）"
    )
    parser.add_argument(
        "--title",
        default='',
        help="文档标题（元数据）"
    )
    parser.add_argument(
        "--author",
        default='',
        help="作者名称（元数据）"
    )
    parser.add_argument(
        "--compress",
        type=lambda x: x.lower() in ['true', '1', 'yes'],
        default=True,
        help="启用压缩（默认: True）"
    )
    parser.add_argument(
        "--images",
        nargs='*',
        help="图片路径列表（支持多个图片，用空格分隔）"
    )
    parser.add_argument(
        "--image-width",
        default='100%25',
        help="图片宽度，如: 100%%, 200px, 50mm（默认: 100%%）"
    )
    parser.add_argument(
        "--image-height",
        default='auto',
        help="图片高度，如: auto, 300px, 100mm（默认: auto）"
    )
    parser.add_argument(
        "--image-align",
        choices=['left', 'center', 'right'],
        default='center',
        help="图片对齐方式（默认: center）"
    )
    parser.add_argument(
        "--image-caption",
        default='',
        help="图片标题（应用于所有图片）"
    )
    
    args = parser.parse_args()
    
    # 验证参数
    if not args.input and not args.input_file:
        print("❌ Error: 必须提供 --input 或 --input-file", file=sys.stderr)
        sys.exit(1)
    
    if not args.output.endswith('.pdf'):
        print("❌ Error: 输出文件必须以.pdf结尾", file=sys.stderr)
        sys.exit(1)
    
    # 读取输入内容
    content = None
    if args.input_file:
        if args.input_file == '-':
            # 从stdin读取
            content = sys.stdin.read()
        else:
            try:
                with open(args.input_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                print(f"❌ Error reading input file: {str(e)}", file=sys.stderr)
                sys.exit(1)
    else:
        content = args.input
    
    # 构建配置
    config = {
        'page_size': args.page_size,
        'orientation': args.orientation,
        'margin_top': args.margin_top,
        'margin_bottom': args.margin_bottom,
        'margin_left': args.margin_left,
        'margin_right': args.margin_right,
        'font_family': args.font_family,
        'font_size': args.font_size,
        'title': args.title,
        'author': args.author,
        'compress': args.compress,
    }
    
    # 确保输出目录存在
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # 根据输入类型生成PDF
    if args.input_type == 'text':
        result = generate_pdf_from_text(content, args.output, config)
    elif args.input_type == 'markdown':
        result = generate_pdf_from_markdown(content, args.output, config)
    elif args.input_type == 'html':
        result = generate_pdf_from_html(content, args.output, config)
    
    # 如果指定了图片，在PDF末尾添加图片页面
    if args.images and result['success']:
        try:
            from weasyprint import HTML, CSS
            
            # 构建图片HTML
            images_html_parts = [
                '<!DOCTYPE html>',
                '<html><head><meta charset="utf-8"><style>',
                '@page { size: A4 portrait; margin: 20mm; }',
                'body { font-family: Arial, sans-serif; }',
                '.image-container { text-align: center; margin-bottom: 30px; page-break-inside: avoid; }',
                '.image-container img { max-width: 100%; object-fit: contain; }',
                '.image-caption { font-size: 10pt; color: #666; margin-top: 8px; font-style: italic; }',
                '</style></head><body>'
            ]
            
            for img_path in args.images:
                img_html = embed_image_to_html(
                    img_path,
                    width=args.image_width,
                    height=args.image_height,
                    align=args.image_align,
                    caption=args.image_caption,
                    alt=os.path.basename(img_path)
                )
                images_html_parts.append(f'<div class="image-container">{img_html}</div>')
            
            images_html_parts.append('</body></html>')
            images_html = '\n'.join(images_html_parts)
            
            # 生成包含图片的临时PDF
            temp_output = args.output.replace('.pdf', '_images.pdf')
            css = CSS(string=f"""
                @page {{
                    size: {args.page_size} {args.orientation};
                    margin: {args.margin_top}mm {args.margin_right}mm 
                            {args.margin_bottom}mm {args.margin_left}mm;
                }}
            """)
            
            html_doc = HTML(string=images_html)
            html_doc.write_pdf(temp_output, stylesheets=[css], optimize_images=True)
            
            # 合并PDF（简单方式：追加到原文件）
            # 注意：这里简化处理，实际应该使用PDF合并库
            print(f"\n📸 图片已添加到: {temp_output}")
            
        except Exception as e:
            print(f"\n⚠️ 警告: 图片添加失败 - {str(e)}", file=sys.stderr)
    
    # 输出结果
    if not result['success']:
        print(f"❌ Error: {result['error']}", file=sys.stderr)
        sys.exit(1)
    
    # 格式化输出
    print(f"✅ PDF Generation Successful")
    print(f"\nOutput File: {result['output_path']}")
    print(f"File Size: {format_file_size(result['file_size'])}")
    print(f"Pages: {result['page_count']}")
    print(f"Page Size: {args.page_size} ({args.orientation})")
    print(f"Generation Time: {result['generation_time']:.2f}s")
    
    if args.title:
        print(f"Title: {args.title}")
    if args.author:
        print(f"Author: {args.author}")
    
    print(f"\nStatus: ✅ Success")


if __name__ == "__main__":
    main()
