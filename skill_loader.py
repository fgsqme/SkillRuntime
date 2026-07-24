#!/usr/bin/env python3
"""
skill_loader.py - SKILL 加载器

功能：
- 扫描目录发现 SKILL
- 解析 SKILL.md 元数据
- 验证 SKILL 结构完整性
- 提供技能索引和检索
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml


class SkillInfo:
    """SKILL 信息"""
    
    def __init__(self, path: Path):
        self.path = path
        self.name = ""
        self.description = ""
        self.when_to_use = ""  # 使用时机（从 frontmatter whenToUse 解析）
        self.metadata = {}
        self.has_scripts = False
        self.has_references = False
        self.has_assets = False
        self.skill_md_path = None
        
    def __repr__(self):
        return f"SkillInfo(name='{self.name}', path={self.path})"


class SkillLoader:
    """SKILL 加载器"""
    
    def __init__(self, skill_dirs: List[str] = None):
        """
        初始化加载器
        
        Args:
            skill_dirs: SKILL 目录列表，默认为 ./skills
        """
        if skill_dirs is None:
            skill_dirs = ["./skills"]
        
        self.skill_dirs = [Path(d) for d in skill_dirs]
        self.skills: Dict[str, SkillInfo] = {}
        
    def scan_skills(self) -> Dict[str, SkillInfo]:
        """
        扫描所有 SKILL 目录
        
        Returns:
            技能名称到 SkillInfo 的映射
        """
        self.skills.clear()
        
        for skill_dir in self.skill_dirs:
            if not skill_dir.exists():
                print(f"⚠️  SKILL 目录不存在: {skill_dir}")
                continue
            
            # 遍历子目录
            for item in sorted(skill_dir.iterdir()):
                if item.is_dir():
                    skill_info = self._load_skill(item)
                    if skill_info:
                        self.skills[skill_info.name] = skill_info
        
        print(f"✅ 扫描完成，发现 {len(self.skills)} 个 SKILL")
        return self.skills
    
    def _load_skill(self, skill_path: Path) -> Optional[SkillInfo]:
        """
        加载单个 SKILL
        
        Args:
            skill_path: SKILL 目录路径
            
        Returns:
            SkillInfo 或 None（如果无效）
        """
        # 检查 SKILL.md 是否存在
        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            print(f"⚠️  跳过 {skill_path.name}: 缺少 SKILL.md")
            return None
        
        # 解析元数据
        try:
            metadata = self._parse_frontmatter(skill_md)
        except Exception as e:
            print(f"⚠️  跳过 {skill_path.name}: 解析失败 - {e}")
            return None
        
        # 创建 SkillInfo
        info = SkillInfo(skill_path)
        info.name = metadata.get('name', skill_path.name)
        info.description = metadata.get('description', '')
        info.when_to_use = metadata.get('whenToUse', '')
        info.metadata = metadata
        info.skill_md_path = skill_md
        
        # 检查资源目录
        info.has_scripts = (skill_path / "scripts").exists()
        info.has_references = (skill_path / "references").exists()
        info.has_assets = (skill_path / "assets").exists()
        
        print(f"✓ 加载 SKILL: {info.name}")
        
        return info
    
    def _parse_frontmatter(self, skill_md_path: Path) -> Dict:
        """
        解析 SKILL.md 的 YAML frontmatter
        
        Args:
            skill_md_path: SKILL.md 路径
            
        Returns:
            元数据字典
        """
        content = skill_md_path.read_text(encoding='utf-8')
        
        if not content.startswith('---'):
            raise ValueError("SKILL.md 必须以 --- 开头")
        
        parts = content.split('---', 2)
        if len(parts) < 3:
            raise ValueError("frontmatter 格式错误")
        
        yaml_content = parts[1].strip()
        metadata = yaml.safe_load(yaml_content)
        
        if not isinstance(metadata, dict):
            raise ValueError("frontmatter 必须是 YAML 字典")
        
        return metadata
    
    def get_skill(self, name: str) -> Optional[SkillInfo]:
        """获取指定名称的 SKILL"""
        return self.skills.get(name)
    
    def list_skills(self) -> List[Dict]:
        """
        列出所有 SKILL 的摘要信息
        
        Returns:
            SKILL 信息列表
        """
        result = []
        for name, info in self.skills.items():
            result.append({
                'name': info.name,
                'description': info.description[:100] + '...' if len(info.description) > 100 else info.description,
                'path': str(info.path),
                'has_scripts': info.has_scripts,
                'has_references': info.has_references,
                'has_assets': info.has_assets,
            })
        return result
    
    def search_skills(self, query: str) -> List[SkillInfo]:
        """
        根据关键词搜索 SKILL
        
        Args:
            query: 搜索关键词
            
        Returns:
            匹配的 SKILL 列表
        """
        query_lower = query.lower()
        matches = []
        
        for info in self.skills.values():
            # 在名称和描述中搜索
            if (query_lower in info.name.lower() or 
                query_lower in info.description.lower()):
                matches.append(info)
        
        return matches
    
    def reload_skill(self, name: str) -> bool:
        """
        重新加载指定 SKILL
        
        Args:
            name: SKILL 名称
            
        Returns:
            是否成功
        """
        if name not in self.skills:
            return False
        
        info = self.skills[name]
        new_info = self._load_skill(info.path)
        
        if new_info:
            self.skills[name] = new_info
            return True
        
        return False


def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="SKILL 加载器 - 扫描和管理技能"
    )
    parser.add_argument(
        "--dirs", "-d",
        nargs="+",
        default=["./skills"],
        help="SKILL 目录列表"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出所有 SKILL"
    )
    parser.add_argument(
        "--search", "-s",
        metavar="QUERY",
        help="搜索 SKILL"
    )
    parser.add_argument(
        "--detail",
        metavar="NAME",
        help="显示 SKILL 详细信息"
    )
    
    args = parser.parse_args()
    
    loader = SkillLoader(args.dirs)
    loader.scan_skills()
    
    if args.list:
        print("\n" + "=" * 60)
        print("已加载的 SKILL")
        print("=" * 60)
        
        skills = loader.list_skills()
        for i, skill in enumerate(skills, 1):
            print(f"\n{i}. {skill['name']}")
            print(f"   描述: {skill['description']}")
            print(f"   路径: {skill['path']}")
            print(f"   资源: scripts={skill['has_scripts']}, "
                  f"references={skill['has_references']}, "
                  f"assets={skill['has_assets']}")
    
    elif args.search:
        print(f"\n搜索: '{args.search}'")
        matches = loader.search_skills(args.search)
        
        if matches:
            print(f"找到 {len(matches)} 个匹配:\n")
            for info in matches:
                print(f"• {info.name}")
                print(f"  {info.description[:150]}")
        else:
            print("未找到匹配的 SKILL")
    
    elif args.detail:
        info = loader.get_skill(args.detail)
        if info:
            print(f"\nSKILL: {info.name}")
            print(f"路径: {info.path}")
            print(f"\n描述:")
            print(info.description)
            print(f"\n资源:")
            print(f"  scripts: {info.has_scripts}")
            print(f"  references: {info.has_references}")
            print(f"  assets: {info.has_assets}")
        else:
            print(f"未找到 SKILL: {args.detail}")
    
    else:
        print(f"\n已加载 {len(loader.skills)} 个 SKILL")
        print("使用 --list 查看所有技能")
        print("使用 --search '关键词' 搜索技能")


if __name__ == "__main__":
    main()
