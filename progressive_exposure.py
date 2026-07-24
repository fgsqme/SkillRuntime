#!/usr/bin/env python3
"""
progressive_exposure.py - 渐进式暴露引擎

实现三级加载机制：
- L1: 元数据（始终在上下文）
- L2: SKILL.md body（触发后加载）
- L3: 资源文件（按需加载）
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re


class ProgressiveExposureEngine:
    """渐进式暴露引擎"""
    
    def __init__(self):
        # L1: 元数据缓存
        self.l1_metadata: Dict[str, dict] = {}
        
        # L2: SKILL.md body 缓存
        self.l2_body: Dict[str, str] = {}
        
        # L3: 资源缓存
        self.l3_resources: Dict[str, Dict[str, str]] = {}
        
    def load_l1_metadata(self, skill_name: str, description: str) -> dict:
        """
        L1: 加载元数据（轻量，始终在上下文）
        
        Args:
            skill_name: SKILL 名称
            description: SKILL 描述
            
        Returns:
            元数据字典
        """
        metadata = {
            'name': skill_name,
            'description': description,
            'level': 'L1',
            'token_cost': len(description.split())  # 估算 token 数
        }
        
        self.l1_metadata[skill_name] = metadata
        return metadata
    
    def load_l2_body(self, skill_path: Path, max_lines: int = 500,
                     variables: Dict[str, str] = None) -> Optional[str]:
        """
        L2: 加载 SKILL.md body（触发后加载）
        
        Args:
            skill_path: SKILL 目录路径
            max_lines: 最大行数限制
            variables: 占位符变量字典，支持 $ARGUMENTS、$<name>、${KIMI_SKILL_DIR} 等
            
        Returns:
            body 内容或 None
        """
        skill_md = skill_path / "SKILL.md"
        
        if not skill_md.exists():
            return None
        
        content = skill_md.read_text(encoding='utf-8')
        
        # 提取 body（跳过 frontmatter）
        parts = content.split('---', 2)
        if len(parts) < 3:
            return None
        
        body = parts[2].strip()
        
        # 限制行数
        lines = body.split('\n')
        if len(lines) > max_lines:
            body = '\n'.join(lines[:max_lines])
            body += f"\n\n... (内容截断，共 {len(lines)} 行)"
        
        # 渐进式调用：阶段 4 - 占位符展开
        body = self._expand_placeholders(body, skill_path, variables)
        
        self.l2_body[skill_path.name] = body
        
        return body
    
    def _expand_placeholders(self, text: str, skill_path: Path,
                            variables: Dict[str, str] = None) -> str:
        """
        展开 Skill 正文中的占位符。
        
        支持的占位符：
        - ${KIMI_SKILL_DIR}: Skill 目录的绝对路径
        - $ARGUMENTS: 用户传入的参数（从 variables['ARGUMENTS'] 获取）
        - $<name> 或 ${name}: 从 variables 字典中查找
        
        Args:
            text: 待展开的文本
            skill_path: Skill 目录路径
            variables: 变量字典
            
        Returns:
            展开后的文本
        """
        if variables is None:
            variables = {}
        
        # 1. 展开 ${KIMI_SKILL_DIR}
        text = text.replace('${KIMI_SKILL_DIR}', str(skill_path.resolve()))
        
        # 2. 展开 $ARGUMENTS
        if 'ARGUMENTS' in variables:
            text = text.replace('$ARGUMENTS', variables['ARGUMENTS'])
        
        # 3. 展开 $<name> 和 ${name} 格式的变量
        def replace_var(match):
            var_name = match.group(1) or match.group(2)
            return variables.get(var_name, match.group(0))
        
        # 匹配 $<name> 或 ${name}，但排除已处理的 ${KIMI_SKILL_DIR}
        text = re.sub(r'\$<([a-zA-Z_][a-zA-Z0-9_]*)>|\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}', replace_var, text)
        
        return text
    
    def load_l3_resource(self, skill_path: Path, resource_type: str, 
                         filename: str) -> Optional[str]:
        """
        L3: 按需加载资源文件
        
        Args:
            skill_path: SKILL 目录路径
            resource_type: 资源类型 (scripts/references/assets)
            filename: 文件名
            
        Returns:
            文件内容或 None
        """
        resource_path = skill_path / resource_type / filename
        
        if not resource_path.exists():
            return None
        
        # 对于 scripts，返回路径而非内容（执行而不读入）
        if resource_type == "scripts":
            content = f"# Script path: {resource_path}\n# Execute with: python {resource_path}"
        else:
            content = resource_path.read_text(encoding='utf-8')
        
        # 缓存
        if skill_path.name not in self.l3_resources:
            self.l3_resources[skill_path.name] = {}
        
        self.l3_resources[skill_path.name][f"{resource_type}/{filename}"] = content
        
        return content
    
    def list_l3_resources(self, skill_path: Path) -> Dict[str, List[str]]:
        """
        列出 SKILL 的所有 L3 资源
        
        Args:
            skill_path: SKILL 目录路径
            
        Returns:
            资源类型到文件列表的映射
        """
        resources = {
            'scripts': [],
            'references': [],
            'assets': []
        }
        
        for resource_type in resources.keys():
            resource_dir = skill_path / resource_type
            if resource_dir.exists():
                for item in resource_dir.iterdir():
                    if item.is_file():
                        resources[resource_type].append(item.name)
        
        return resources
    
    def get_skill_context(self, skill_name: str, skill_path: Path,
                         trigger_keywords: List[str] = None) -> dict:
        """
        获取 SKILL 的完整上下文（智能分级加载）
        
        Args:
            skill_name: SKILL 名称
            skill_path: SKILL 目录路径
            trigger_keywords: 触发关键词（用于判断是否需要加载 L2/L3）
            
        Returns:
            上下文字典
        """
        context = {
            'skill_name': skill_name,
            'levels_loaded': ['L1'],
            'token_estimate': 0
        }
        
        # L1: 始终加载
        skill_md = skill_path / "SKILL.md"
        metadata = self._parse_frontmatter(skill_md)
        l1_data = self.load_l1_metadata(skill_name, metadata.get('description', ''))
        context['l1_metadata'] = l1_data
        context['token_estimate'] += l1_data['token_cost']
        
        # L2: 如果有触发关键词或用户明确请求，加载 body
        if trigger_keywords:
            body = self.load_l2_body(skill_path)
            if body:
                context['levels_loaded'].append('L2')
                context['l2_body'] = body
                context['token_estimate'] += len(body.split())
        
        # L3: 列出可用资源（不加载内容，除非明确请求）
        l3_list = self.list_l3_resources(skill_path)
        context['l3_available'] = l3_list
        
        return context
    
    def load_full_skill(self, skill_path: Path) -> dict:
        """
        加载 SKILL 的全部内容（用于调试或完整索引）
        
        Args:
            skill_path: SKILL 目录路径
            
        Returns:
            完整内容字典
        """
        skill_name = skill_path.name
        
        result = {
            'name': skill_name,
            'path': str(skill_path),
        }
        
        # L1
        skill_md = skill_path / "SKILL.md"
        metadata = self._parse_frontmatter(skill_md)
        result['metadata'] = metadata
        
        # L2
        body = self.load_l2_body(skill_path)
        if body:
            result['body'] = body
        
        # L3
        resources = self.list_l3_resources(skill_path)
        result['resources'] = {}
        
        for resource_type, files in resources.items():
            result['resources'][resource_type] = {}
            for filename in files:
                content = self.load_l3_resource(skill_path, resource_type, filename)
                if content:
                    result['resources'][resource_type][filename] = content
        
        return result
    
    def _parse_frontmatter(self, skill_md_path: Path) -> dict:
        """解析 frontmatter"""
        import yaml
        
        content = skill_md_path.read_text(encoding='utf-8')
        
        if not content.startswith('---'):
            return {}
        
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}
        
        yaml_content = parts[1].strip()
        
        try:
            metadata = yaml.safe_load(yaml_content)
            return metadata if isinstance(metadata, dict) else {}
        except:
            return {}
    
    def estimate_token_cost(self, text: str) -> int:
        """
        估算文本的 token 成本
        
        Args:
            text: 文本内容
            
        Returns:
            估算的 token 数
        """
        # 简单估算：英文约 4 字符/token，中文约 1.5 字符/token
        # 这里使用保守估计：平均 3 字符/token
        return len(text) // 3
    
    def clear_cache(self, skill_name: str = None):
        """
        清除缓存
        
        Args:
            skill_name: 指定 SKILL 名称，None 则清除所有
        """
        if skill_name:
            self.l1_metadata.pop(skill_name, None)
            self.l2_body.pop(skill_name, None)
            self.l3_resources.pop(skill_name, None)
        else:
            self.l1_metadata.clear()
            self.l2_body.clear()
            self.l3_resources.clear()
    
    def clear_l2_body(self, skill_name: str = None):
        """
        清除 L2 body 缓存，实现「用完即弃」策略。
        SKILL.md 正文在命中并注入系统提示词后应立即清除，
        不持久化到对话历史，以节省 token。
        
        Args:
            skill_name: 指定 SKILL 名称，None 则清除所有 L2 缓存
        """
        if skill_name:
            removed = self.l2_body.pop(skill_name, None)
            if removed:
                print(f"🗑️  [L2] 已清除 Skill '{skill_name}' 正文缓存")
        else:
            count = len(self.l2_body)
            self.l2_body.clear()
            if count > 0:
                print(f"🗑️  [L2] 已清除全部 {count} 个 Skill 正文缓存")


def main():
    """命令行测试"""
    import argparse
    from pathlib import Path
    
    parser = argparse.ArgumentParser(
        description="渐进式暴露引擎测试"
    )
    parser.add_argument(
        "skill_path",
        help="SKILL 目录路径"
    )
    parser.add_argument(
        "--full", "-f",
        action="store_true",
        help="加载全部内容"
    )
    parser.add_argument(
        "--trigger", "-t",
        nargs="+",
        help="触发关键词"
    )
    
    args = parser.parse_args()
    
    engine = ProgressiveExposureEngine()
    skill_path = Path(args.skill_path)
    skill_name = skill_path.name
    
    if args.full:
        print("加载完整 SKILL 内容...\n")
        full_content = engine.load_full_skill(skill_path)
        
        print(f"SKILL: {full_content['name']}")
        print(f"路径: {full_content['path']}")
        print(f"\n元数据:")
        for key, value in full_content.get('metadata', {}).items():
            print(f"  {key}: {value}")
        
        print(f"\nBody 长度: {len(full_content.get('body', ''))} 字符")
        
        print(f"\n资源:")
        for resource_type, files in full_content.get('resources', {}).items():
            print(f"  {resource_type}/:")
            for filename in files:
                print(f"    - {filename}")
    
    else:
        print("智能分级加载...\n")
        context = engine.get_skill_context(
            skill_name, 
            skill_path,
            trigger_keywords=args.trigger
        )
        
        print(f"SKILL: {context['skill_name']}")
        print(f"加载层级: {', '.join(context['levels_loaded'])}")
        print(f"估算 Token: {context['token_estimate']}")
        
        print(f"\nL1 元数据:")
        print(f"  名称: {context['l1_metadata']['name']}")
        print(f"  描述: {context['l1_metadata']['description'][:100]}...")
        
        if 'l2_body' in context:
            print(f"\nL2 Body: 已加载 ({len(context['l2_body'])} 字符)")
        
        print(f"\nL3 可用资源:")
        for resource_type, files in context.get('l3_available', {}).items():
            if files:
                print(f"  {resource_type}/: {', '.join(files)}")


if __name__ == "__main__":
    main()
