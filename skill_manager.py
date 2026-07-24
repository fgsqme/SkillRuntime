#!/usr/bin/env python3
"""
skill_manager.py - SKILL 管理器

功能：
- 管理多个 SKILL
- 智能匹配用户需求与 SKILL
- 协调渐进式加载
- 提供统一的 SKILL 访问接口
"""

from pathlib import Path
from typing import Dict, List, Optional
from skill_loader import SkillLoader, SkillInfo
from progressive_exposure import ProgressiveExposureEngine


class SkillManager:
    """SKILL 管理器"""
    
    def __init__(self, skill_dirs: List[str] = None, verbose: bool = True):
        """
        初始化管理器
        
        Args:
            skill_dirs: SKILL 目录列表
            verbose: 是否显示详细日志
        """
        self.loader = SkillLoader(skill_dirs)
        self.exposure_engine = ProgressiveExposureEngine()
        self.active_skills: Dict[str, SkillInfo] = {}
        self.verbose = verbose
        
    def initialize(self) -> int:
        """
        初始化：扫描并加载所有 SKILL（只解析 frontmatter 元数据）
        
        Returns:
            加载的 SKILL 数量
        """
        if self.verbose:
            print("🔍 扫描 SKILL 目录（只解析元数据）...")
        skills = self.loader.scan_skills()
        
        # 激活所有发现的 SKILL
        for name, info in skills.items():
            self.active_skills[name] = info
            
            # 预加载 L1 元数据
            self.exposure_engine.load_l1_metadata(
                info.name, 
                info.description
            )
        
        if self.verbose:
            print(f"✅ 已激活 {len(self.active_skills)} 个 SKILL（仅元数据）\n")
        return len(self.active_skills)
    
    def list_active_skills(self) -> List[Dict]:
        """列出所有激活的 SKILL"""
        return self.loader.list_skills()
    
    def match_skills(self, user_query: str, top_k: int = 3) -> List[SkillInfo]:
        """
        根据用户查询匹配最相关的 SKILL
        
        Args:
            user_query: 用户输入
            top_k: 返回前 K 个匹配
            
        Returns:
            匹配的 SKILL 列表（按相关性排序）
        """
        query_lower = user_query.lower()
        
        # 计算每个 SKILL 的相关性分数
        scored_skills = []
        
        for name, info in self.active_skills.items():
            score = self._calculate_relevance(query_lower, info)
            # 降低阈值，让更多 SKILL 被匹配
            if score >= 0.0:  # 总是包含所有 SKILL，让 AI 决定
                scored_skills.append((score, info))
        
        # 按分数排序
        scored_skills.sort(key=lambda x: x[0], reverse=True)
        
        # 返回前 K 个
        return [info for score, info in scored_skills[:top_k]]
    
    def _calculate_relevance(self, query: str, skill_info: SkillInfo) -> float:
        """
        计算查询与 SKILL 的相关性分数
        
        Args:
            query: 用户查询（小写）
            skill_info: SKILL 信息
            
        Returns:
            相关性分数 (0-1)
        """
        score = 0.0
        
        # 在名称中匹配
        if query in skill_info.name.lower():
            score += 0.5
        
        # 在描述中匹配
        description_lower = skill_info.description.lower()
        
        # 关键词匹配
        query_words = set(query.split())
        desc_words = set(description_lower.split())
        
        matching_words = query_words & desc_words
        if matching_words:
            score += len(matching_words) * 0.1
        
        # 完全匹配描述中的短语
        if query in description_lower:
            score += 0.3
        
        return min(score, 1.0)
    
    def activate_skill(self, skill_name: str, load_level: str = "L1") -> Optional[Dict]:
        """
        激活指定 SKILL 并加载到指定层级
        
        Args:
            skill_name: SKILL 名称
            load_level: 加载层级 (L1/L2/L3)
            
        Returns:
            SKILL 上下文或 None
        """
        if skill_name not in self.active_skills:
            print(f"❌ SKILL 不存在: {skill_name}")
            return None
        
        info = self.active_skills[skill_name]
        
        print(f"🎯 激活 SKILL: {skill_name} (加载层级: {load_level})")
        
        context = {
            'name': skill_name,
            'level': load_level
        }
        
        # L1: 元数据（已预加载）
        if load_level in ["L1", "L2", "L3"]:
            context['metadata'] = self.exposure_engine.l1_metadata.get(skill_name, {})
        
        # L2: Body
        if load_level in ["L2", "L3"]:
            body = self.exposure_engine.load_l2_body(info.path)
            if body:
                context['body'] = body
                print(f"   ✓ 加载 L2 Body ({len(body)} 字符)")
        
        # L3: 资源列表
        if load_level == "L3":
            resources = self.exposure_engine.list_l3_resources(info.path)
            context['resources'] = resources
            print(f"   ✓ 加载 L3 资源列表")
        
        return context
    
    def execute_skill_script(self, skill_name: str, script_name: str, 
                            args: List[str] = None) -> Optional[str]:
        """
        执行 SKILL 的脚本（L3 层级）
        
        Args:
            skill_name: SKILL 名称
            script_name: 脚本名称
            args: 脚本参数
            
        Returns:
            脚本输出或 None
        """
        if skill_name not in self.active_skills:
            return None
        
        info = self.active_skills[skill_name]
        script_path = info.path / "scripts" / script_name
        
        if not script_path.exists():
            print(f"❌ 脚本不存在: {script_path}")
            return None
        
        # 构建命令
        import subprocess
        
        cmd = ["python", str(script_path)]
        if args:
            cmd.extend(args)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nErrors:\n{result.stderr}"
            
            return output
        
        except Exception as e:
            return f"执行失败: {str(e)}"
    
    def get_skill_registry_summary(self) -> str:
        """
        生成精简的 Skill 注册表摘要，用于注入系统提示词。
        只包含 name + description + whenToUse，不加载正文。
        
        Returns:
            格式化的注册表字符串
        """
        if not self.active_skills:
            return ""
        
        lines = []
        lines.append("## 可用 Skills（注册表摘要）")
        lines.append("以下是已注册的 Skills 摘要。根据 description 和 whenToUse 判断是否需要调用某个 Skill。")
        lines.append("")
        
        for name, info in self.active_skills.items():
            lines.append(f"### {info.name}")
            lines.append(f"- **description**: {info.description}")
            if info.when_to_use:
                lines.append(f"- **whenToUse**: {info.when_to_use}")
            if info.has_scripts:
                # 只列出脚本名，不读内容
                scripts_dir = info.path / "scripts"
                if scripts_dir.exists():
                    scripts = [f.name for f in scripts_dir.iterdir() if f.is_file() and f.suffix == '.py']
                    if scripts:
                        lines.append(f"- **scripts**: {', '.join(scripts)}")
            lines.append("")
        
        return "\n".join(lines)
    
    def load_skill_body(self, skill_name: str, variables: Dict[str, str] = None) -> Optional[str]:
        """
        按需加载 Skill 的 SKILL.md 正文（L2）。
        只在模型命中该 Skill 后才调用。
        
        Args:
            skill_name: Skill 名称
            variables: 占位符变量字典，用于展开 $ARGUMENTS、${KIMI_SKILL_DIR} 等
            
        Returns:
            SKILL.md 正文内容，或 None
        """
        if skill_name not in self.active_skills:
            return None
        
        info = self.active_skills[skill_name]
        body = self.exposure_engine.load_l2_body(info.path, variables=variables)
        
        if self.verbose:
            print(f"📖 [L2] 加载 Skill 正文: {skill_name} ({len(body) if body else 0} 字符)")
        
        return body
    
    def clear_skill_body(self, skill_name: str = None):
        """
        清除已加载的 Skill 正文缓存，实现「用完即弃」策略。
        SKILL.md 正文在命中并注入系统提示词后应立即清除，
        不持久化到对话历史，以节省 token。
        
        Args:
            skill_name: 指定 Skill 名称，None 则清除所有
        """
        self.exposure_engine.clear_l2_body(skill_name)
    
    def get_skill_prompt_context(self, user_query: str) -> str:
        """
        已废弃：渐进式调用下不再按查询注入 Skill 上下文。
        Skill 摘要已在系统提示词中始终注入。
        正文在命中后按需加载。
        
        保留此方法以兼容旧调用，返回空字符串。
        """
        return ""
    
    def reload_all(self):
        """重新加载所有 SKILL"""
        print("🔄 重新加载所有 SKILL...")
        self.exposure_engine.clear_cache()
        self.initialize()
    
    def add_skill_directory(self, directory: str):
        """添加新的 SKILL 目录"""
        self.loader.skill_dirs.append(Path(directory))
        print(f"✓ 添加 SKILL 目录: {directory}")
        self.reload_all()


def main():
    """命令行测试"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="SKILL 管理器"
    )
    parser.add_argument(
        "--dirs", "-d",
        nargs="+",
        default=["./skills"],
        help="SKILL 目录"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出所有 SKILL"
    )
    parser.add_argument(
        "--match", "-m",
        metavar="QUERY",
        help="匹配相关 SKILL"
    )
    parser.add_argument(
        "--activate", "-a",
        metavar="NAME",
        help="激活指定 SKILL"
    )
    parser.add_argument(
        "--level",
        choices=["L1", "L2", "L3"],
        default="L2",
        help="加载层级"
    )
    
    args = parser.parse_args()
    
    manager = SkillManager(args.dirs)
    manager.initialize()
    
    if args.list:
        skills = manager.list_active_skills()
        print(f"\n已激活 {len(skills)} 个 SKILL:\n")
        for i, skill in enumerate(skills, 1):
            print(f"{i}. {skill['name']}")
            print(f"   {skill['description'][:100]}...")
    
    elif args.match:
        print(f"\n匹配查询: '{args.match}'\n")
        matches = manager.match_skills(args.match)
        
        if matches:
            for info in matches:
                print(f"• {info.name}")
                print(f"  相关性: 高")
                print(f"  {info.description[:150]}")
        else:
            print("未找到匹配的 SKILL")
    
    elif args.activate:
        context = manager.activate_skill(args.activate, args.level)
        if context:
            print(f"\n激活成功!")
            print(f"层级: {context['level']}")
            if 'metadata' in context:
                print(f"元数据: {context['metadata']}")


if __name__ == "__main__":
    main()
