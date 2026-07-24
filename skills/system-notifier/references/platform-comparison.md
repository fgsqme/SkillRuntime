# 跨平台通知系统对比

## 平台支持概览

| 特性 | Linux | macOS | Windows |
|------|-------|-------|---------|
| 默认工具 | notify-send | osascript | PowerShell |
| 需要安装 | ✅ (libnotify-bin) | ❌ (内置) | ❌ (内置) |
| 自定义图标 | ✅ | ⚠️ (有限) | ⚠️ (有限) |
| 紧急程度 | ✅ (3级) | ❌ | ⚠️ (2级) |
| 超时控制 | ✅ | ❌ | ❌ |
| 动作按钮 | ⚠️ (需额外配置) | ❌ | ✅ |
| 通知中心 | 依赖DE | ✅ | ✅ |
| 持久化 | 依赖DE | ✅ | ✅ |

## Linux (notify-send)

### 优势
- ✅ 完全控制所有参数
- ✅ 丰富的图标选择
- ✅ 三级紧急程度
- ✅ 精确的超时控制
- ✅ 支持通知替换和更新

### 劣势
- ❌ 需要安装 libnotify-bin
- ❌ 依赖桌面环境的通知守护进程
- ❌ 在某些窗口管理器中不工作

### 典型用法
```bash
notify-send -u critical -t 10000 -i dialog-warning "警告" "磁盘空间不足"
```

### 适用场景
- Ubuntu/Debian 桌面环境
- GNOME, KDE, XFCE 等主流桌面
- 需要精细控制通知行为

---

## macOS (osascript / AppleScript)

### 优势
- ✅ 系统内置，无需安装
- ✅ 与通知中心完美集成
- ✅ 自动持久化到通知历史
- ✅ 简洁的 API

### 劣势
- ❌ 不支持自定义图标
- ❌ 不支持超时控制
- ❌ 不支持紧急程度
- ❌ 功能相对有限

### 典型用法
```applescript
display notification "消息内容" with title "标题"
```

### Python 调用
```python
import subprocess
subprocess.run([
    'osascript', '-e',
    'display notification "Message" with title "Title"'
])
```

### 适用场景
- macOS 原生应用
- 简单的用户提醒
- 不需要复杂定制的场景

---

## Windows (PowerShell Toast)

### 优势
- ✅ 系统内置，无需安装
- ✅ 现代化的 Toast 通知样式
- ✅ 与操作中心集成
- ✅ 支持动作按钮

### 劣势
- ❌ PowerShell 脚本较复杂
- ❌ 首次运行可能需要权限确认
- ❌ 旧版本 Windows 不支持（需要 Win10+）

### 典型用法
```powershell
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
$template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
$toastXml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template)
$toastXml.GetElementsByTagName("text")[0].AppendChild($toastXml.CreateTextNode("Title")) | Out-Null
$toastXml.GetElementsByTagName("text")[1].AppendChild($toastXml.CreateTextNode("Message")) | Out-Null
$toast = [Windows.UI.Notifications.ToastNotification]::new($toastXml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("").Show($toast)
```

### 适用场景
- Windows 10/11 系统
- 需要现代化通知样式
- 与 UWP 应用集成

---

## 代码实现策略

### 自动检测平台

```python
import platform

system = platform.system()

if system == "Linux":
    use_notify_send()
elif system == "Darwin":  # macOS
    use_osascript()
elif system == "Windows":
    use_powershell()
else:
    raise UnsupportedPlatformError(system)
```

### 统一接口

```python
def send_notification(title, message, urgency="normal", timeout=5):
    """跨平台发送通知的统一接口"""
    system = platform.system()
    
    if system == "Linux":
        return send_linux(title, message, urgency, timeout)
    elif system == "Darwin":
        return send_macos(title, message)
    elif system == "Windows":
        return send_windows(title, message)
    else:
        return False
```

### 降级策略

```python
def send_with_fallback(title, message):
    """尝试多种方法，确保通知送达"""
    
    # 尝试 1: 使用主方法
    if try_primary_method(title, message):
        return True
    
    # 尝试 2: 备选方法（如写入日志文件）
    if try_fallback_method(title, message):
        return True
    
    # 尝试 3: 打印到控制台
    print(f"[NOTIFICATION] {title}: {message}")
    return False
```

---

## 测试建议

### 跨平台测试清单

- [ ] Linux (Ubuntu 20.04+)
  - [ ] GNOME 桌面
  - [ ] KDE Plasma
  - [ ] XFCE
  - [ ] 无桌面环境（服务器）

- [ ] macOS (10.14+)
  - [ ] Catalina
  - [ ] Big Sur
  - [ ] Monterey
  - [ ] Ventura

- [ ] Windows (10+)
  - [ ] Windows 10
  - [ ] Windows 11
  - [ ] 旧版本（应优雅失败）

### 测试用例

```python
# 测试 1: 基本通知
send_notification("Test", "Basic notification")

# 测试 2: 不同紧急程度
for urgency in ['low', 'normal', 'critical']:
    send_notification(f"Urgency: {urgency}", "Test message", urgency)

# 测试 3: 长文本
send_notification(
    "Long Message Test",
    "This is a very long message that should be truncated or wrapped properly."
)

# 测试 4: 特殊字符
send_notification(
    "Special Characters",
    "Emoji: ✅ ❌ ⚠️\nUnicode: 中文 日本語 العربية"
)

# 测试 5: 空值处理
send_notification("", "")  # 应该失败并给出错误信息
```

---

## 最佳实践总结

### 1. 平台适配

```python
# ✅ 好的做法：检测平台并使用适当的方法
system = platform.system()
if system in SUPPORTED_SYSTEMS:
    send_notification(title, message)
else:
    log_warning(f"Unsupported platform: {system}")
```

### 2. 错误处理

```python
# ✅ 好的做法：捕获异常并提供反馈
try:
    success = send_notification(title, message)
    if not success:
        log_error("Failed to send notification")
except Exception as e:
    log_error(f"Notification error: {e}")
```

### 3. 用户偏好

```python
# ✅ 好的做法：尊重用户设置
if user_prefs.get('notifications_enabled', True):
    send_notification(title, message)
```

### 4. 频率控制

```python
# ✅ 好的做法：避免通知洪水
if not rate_limiter.allow_notification():
    log_debug("Notification rate limited")
else:
    send_notification(title, message)
```

---

## 常见问题

### Q: 为什么我的通知没有显示？

**A:** 检查以下几点：
1. 桌面环境是否支持通知
2. 通知守护进程是否运行
3. 用户是否禁用了通知
4. 是否在免打扰模式

### Q: 如何添加声音？

**A:** 
- **Linux**: 使用 `paplay` 播放声音后发送通知
- **macOS**: AppleScript 不支持自定义声音
- **Windows**: PowerShell Toast 不支持自定义声音

### Q: 可以添加点击事件吗？

**A:**
- **Linux**: 需要 D-Bus 回调支持
- **macOS**: 不支持
- **Windows**: 支持动作按钮

### Q: 通知会保存多久？

**A:**
- **Linux**: 取决于桌面环境
- **macOS**: 保存在通知中心，直到用户清除
- **Windows**: 保存在操作中心，直到用户清除

---

## 相关资源

- [Linux Desktop Notifications](https://specifications.freedesktop.org/notification-spec/)
- [macOS Notification Programming Guide](https://developer.apple.com/documentation/usernotifications)
- [Windows Toast Notifications](https://learn.microsoft.com/en-us/windows/apps/design/shell/tiles-and-notifications/)
- [Cross-platform Python Libraries](https://pypi.org/search/?q=notification)
