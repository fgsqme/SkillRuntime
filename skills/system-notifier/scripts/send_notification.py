#!/usr/bin/env python3
"""
send_notification.py - 跨平台系统通知发送器

功能：
- 支持 Linux (notify-send)
- 支持 macOS (osascript)
- 支持 Windows (PowerShell)
- 自动检测操作系统
- 自定义标题、消息、紧急程度
- 可选超时控制
"""

import sys
import platform
import subprocess
from typing import Optional


def send_notification_linux(
    title: str,
    message: str,
    urgency: str = "normal",
    timeout: int = 5,
    icon: Optional[str] = None
) -> bool:
    """
    在 Linux 上发送通知（使用 notify-send）
    
    Args:
        title: 通知标题
        message: 通知消息
        urgency: 紧急程度 (low/normal/critical)
        timeout: 超时时间（秒），0 表示等待点击
        icon: 图标名称
        
    Returns:
        是否成功发送
    """
    try:
        # 检查 notify-send 是否可用
        result = subprocess.run(
            ['which', 'notify-send'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("❌ notify-send not found. Install with: sudo apt-get install libnotify-bin")
            return False
        
        # 构建命令
        cmd = ['notify-send']
        
        # 添加图标
        if icon:
            cmd.extend(['-i', icon])
        else:
            # 根据紧急程度选择默认图标
            icon_map = {
                'low': 'dialog-information',
                'normal': 'dialog-information',
                'critical': 'dialog-warning'
            }
            cmd.extend(['-i', icon_map.get(urgency, 'dialog-information')])
        
        # 添加超时（毫秒）
        if timeout > 0:
            cmd.extend(['-t', str(timeout * 1000)])
        
        # 添加紧急程度
        cmd.extend(['-u', urgency])
        
        # 添加标题和消息
        cmd.extend([title, message])
        
        # 执行
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Notification sent (Linux)")
            return True
        else:
            print(f"❌ Failed to send notification: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending notification: {e}")
        return False


def send_notification_macos(
    title: str,
    message: str,
    urgency: str = "normal",
    timeout: int = 5,
    icon: Optional[str] = None
) -> bool:
    """
    在 macOS 上发送通知（使用 osascript）
    
    Args:
        title: 通知标题
        message: 通知消息
        urgency: 紧急程度 (未使用，保留兼容性)
        timeout: 超时时间（未使用，保留兼容性）
        icon: 图标名称（未使用，保留兼容性）
        
    Returns:
        是否成功发送
    """
    try:
        # 构建 AppleScript
        script = f'''
        display notification "{message}" with title "{title}"
        '''
        
        # 执行
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Notification sent (macOS)")
            return True
        else:
            print(f"❌ Failed to send notification: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending notification: {e}")
        return False


def send_notification_windows(
    title: str,
    message: str,
    urgency: str = "normal",
    timeout: int = 5,
    icon: Optional[str] = None
) -> bool:
    """
    在 Windows 上发送通知（使用 PowerShell）
    
    Args:
        title: 通知标题
        message: 通知消息
        urgency: 紧急程度 (未使用，保留兼容性)
        timeout: 超时时间（未使用，保留兼容性）
        icon: 图标名称（未使用，保留兼容性）
        
    Returns:
        是否成功发送
    """
    try:
        # 构建 PowerShell 脚本
        ps_script = f'''
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        $template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
        $toastXml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template)
        $toastXml.GetElementsByTagName("text")[0].AppendChild($toastXml.CreateTextNode("{title}")) | Out-Null
        $toastXml.GetElementsByTagName("text")[1].AppendChild($toastXml.CreateTextNode("{message}")) | Out-Null
        $toast = [Windows.UI.Notifications.ToastNotification]::new($toastXml)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("").Show($toast)
        '''
        
        # 执行
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Notification sent (Windows)")
            return True
        else:
            print(f"❌ Failed to send notification: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending notification: {e}")
        return False


def send_notification(
    title: str,
    message: str,
    urgency: str = "normal",
    timeout: int = 5,
    icon: Optional[str] = None
) -> bool:
    """
    跨平台发送系统通知（自动检测操作系统）
    
    Args:
        title: 通知标题
        message: 通知消息
        urgency: 紧急程度 (low/normal/critical)
        timeout: 超时时间（秒）
        icon: 图标名称
        
    Returns:
        是否成功发送
    """
    # 验证参数
    if not title or not title.strip():
        print("❌ Title cannot be empty")
        return False
    
    if not message or not message.strip():
        print("❌ Message cannot be empty")
        return False
    
    if urgency not in ['low', 'normal', 'critical']:
        print(f"❌ Invalid urgency: {urgency}. Must be low/normal/critical")
        return False
    
    # 检测操作系统
    system = platform.system()
    
    if system == "Linux":
        return send_notification_linux(title, message, urgency, timeout, icon)
    elif system == "Darwin":  # macOS
        return send_notification_macos(title, message, urgency, timeout, icon)
    elif system == "Windows":
        return send_notification_windows(title, message, urgency, timeout, icon)
    else:
        print(f"❌ Unsupported operating system: {system}")
        return False


def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="发送系统通知"
    )
    parser.add_argument(
        "--title", "-t",
        required=True,
        help="通知标题"
    )
    parser.add_argument(
        "--message", "-m",
        required=True,
        help="通知消息"
    )
    parser.add_argument(
        "--urgency", "-u",
        choices=["low", "normal", "critical"],
        default="normal",
        help="紧急程度 (default: normal)"
    )
    parser.add_argument(
        "--timeout", "-T",
        type=int,
        default=5,
        help="显示时长（秒），0=等待点击 (default: 5)"
    )
    parser.add_argument(
        "--icon", "-i",
        default=None,
        help="图标名称 (optional)"
    )
    
    args = parser.parse_args()
    
    # 发送通知
    success = send_notification(
        title=args.title,
        message=args.message,
        urgency=args.urgency,
        timeout=args.timeout,
        icon=args.icon
    )
    
    # 返回码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
