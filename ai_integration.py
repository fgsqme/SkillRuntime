#!/usr/bin/env python3
"""
ai_integration.py - AI 集成接口

功能：
- 连接 OpenAI API
- 注入 SKILL 上下文到 prompt
- 处理用户查询并返回结果
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import requests


class AIIntegration:
    """AI 集成接口"""
    
    def __init__(self, api_url: str = "http://localhost:8080", 
                 api_key: str = "test",
                 model: str = "gpt-4",
                 verbose: bool = True):
        """
        初始化 AI 集成
        
        Args:
            api_url: API 地址
            api_key: API Key
            model: 模型名称
            verbose: 是否显示详细日志
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.verbose = verbose
        self.skill_registry_summary = ""  # Skill 注册表摘要（启动时注入）
        self._system_prompt_template = None  # 延迟加载系统提示词模板
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def set_skill_registry(self, summary: str):
        """
        设置 Skill 注册表摘要，会在每次 AI 调用时注入系统提示词。
        在启动时调用一次即可。
        
        Args:
            summary: 精简的 Skill 注册表字符串
        """
        self.skill_registry_summary = summary
        if self.verbose:
            print(f"📋 [AI] 已注入 Skill 注册表 ({len(summary)} 字符)")
    
    def chat_with_skills(self, user_message: str, 
                        skill_context: str = "",
                        conversation_history: List[Dict] = None,
                        skill_body: str = "") -> str:
        """
        带 SKILL 上下文的对话
        
        核心原则（参考 Kimi Code CLI 渐进式披露机制）：
        - 启动时：只注入 Skill 注册表摘要（L1 元数据）到系统提示词
        - 命中时：将 SKILL.md 正文临时注入系统提示词
        - 用完后：正文不持久化到对话历史，下次调用不再包含
        
        Args:
            user_message: 用户消息
            skill_context: 已废弃，保留兼容。Skill 摘要已在系统提示词中始终注入
            conversation_history: 对话历史
            skill_body: 命中的 Skill 正文，仅注入本次 API 调用的系统提示词，
                       调用结束后不保留，等待下次命中再加载
            
        Returns:
            AI 回复
        """
        # 构建系统提示（始终包含 Skill 注册表摘要）
        system_prompt = self._build_system_prompt()
        
        # 命中时临时注入 Skill 正文到系统提示词
        # 该正文只在本次 API 调用中有效，调用结束后即丢弃
        if skill_body:
            system_prompt += "\n\n---\n\n"
            system_prompt += "## 当前命中的 Skill 详细指引\n\n"
            system_prompt += skill_body
            # print(f"📖 [AI] 临时注入 Skill 正文 ({len(skill_body)} 字符)，调用结束后将丢弃")
        
        # 构建消息列表（skill_body 只存在于 system_prompt 中，不进入 history）
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加对话历史（不包含任何 skill_body 内容）
        if conversation_history:
            messages.extend(conversation_history)
        
        # 添加当前消息
        messages.append({"role": "user", "content": user_message})
        
        # 调用 API
        try:
            response = self._call_api(messages)
            return response
        except Exception as e:
            return f"❌ API 调用失败: {str(e)}"
    
    def _load_system_prompt_template(self) -> str:
        """
        从 prompts/system_prompt.txt 加载系统提示词模板。
        使用延迟加载，只在首次调用时读取文件。
        
        Returns:
            系统提示词模板文本
        """
        if self._system_prompt_template is not None:
            return self._system_prompt_template
        
        prompt_path = Path(__file__).parent / "prompts" / "system_prompt.txt"
        if prompt_path.exists():
            self._system_prompt_template = prompt_path.read_text(encoding='utf-8').strip()
        else:
            # 回退：如果文件不存在，使用空模板（不应发生）
            self._system_prompt_template = ""
            if self.verbose:
                print(f"⚠️  [AI] 系统提示词文件不存在: {prompt_path}")
        
        return self._system_prompt_template
    
    def _build_system_prompt(self) -> str:
        """
        构建系统提示，始终注入 Skill 注册表摘要
        
        Returns:
            系统提示文本
        """
        base_prompt = self._load_system_prompt_template()
        
        # 始终注入 Skill 注册表摘要（渐进式调用：阶段 2）
        if self.skill_registry_summary:
            base_prompt += "\n\n"
            base_prompt += self.skill_registry_summary
        
        return base_prompt
    
    def _call_api(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """
        调用 OpenAI API
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            
        Returns:
            AI 回复文本
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4096
        }
        
        if self.verbose:
            print(f"   🌐 [API] 发送请求:")
            print(f"      URL: {self.api_url}/v1/chat/completions")
            print(f"      Model: {self.model}")
            print(f"      Temperature: {temperature}")
            print(f"      Messages Count: {len(messages)}")
            print(f"      Payload Size: {len(str(payload))} bytes\n")
        
        response = self.session.post(
            f"{self.api_url}/v1/chat/completions",
            json=payload,
            timeout=60
        )
        
        if self.verbose:
            print(f"   📡 [API] 收到响应:")
            print(f"      Status Code: {response.status_code}")
            print(f"      Response Size: {len(response.text)} bytes\n")
        
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            if self.verbose:
                print(f"   ✅ [API] 解析成功:")
                print(f"      Content Length: {len(content)} chars")
                print(f"      Token Usage: {data.get('usage', {}).get('total_tokens', 'N/A')}\n")
            return content
        else:
            if self.verbose:
                print(f"   ❌ [API] 请求失败:")
                print(f"      Error: {response.text[:500]}\n")
            raise Exception(f"API 错误 {response.status_code}: {response.text}")
    
    def test_connection(self) -> bool:
        """
        测试 API 连接
        
        Returns:
            是否成功
        """
        try:
            messages = [
                {"role": "user", "content": "Hello"}
            ]
            response = self._call_api(messages, temperature=0)
            return len(response) > 0
        except Exception as e:
            if self.verbose:
                print(f"连接测试失败: {e}")
            return False


def main():
    """测试 AI 集成"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="AI 集成测试"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8080",
        help="API 地址"
    )
    parser.add_argument(
        "--api-key",
        default="test",
        help="API Key"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="测试连接"
    )
    parser.add_argument(
        "--chat",
        metavar="MESSAGE",
        help="发送消息"
    )
    
    args = parser.parse_args()
    
    ai = AIIntegration(args.api_url, args.api_key)
    
    if args.test:
        print("测试 API 连接...")
        if ai.test_connection():
            print("✅ 连接成功")
        else:
            print("❌ 连接失败")
    
    elif args.chat:
        print(f"发送消息: {args.chat}\n")
        response = ai.chat_with_skills(args.chat)
        print(f"AI 回复:\n{response}")


if __name__ == "__main__":
    main()
