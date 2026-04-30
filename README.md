# FreeXCraft 自动续期 GitHub Actions 版

本项目提供 FreeXCraft 服务器的自动续期功能，通过 GitHub Actions 实现定时自动运行，无需本地部署。

## 功能特点

- ✅ 全自动动态抓取配置参数
- ✅ 自动登录 FreeXCraft 账号
- ✅ 自动执行续期操作
- ✅ Telegram 通知结果
- ✅ 支持手动触发和定时触发
- ✅ 支持代理配置（可选）

## 使用方法

### 步骤1：Fork 本仓库

点击页面右上角的 "Fork" 按钮，将仓库复制到自己的 GitHub 账户。

### 步骤2：配置 Secrets

在 Fork 后的仓库中，进入 "Settings" → "Secrets and variables" → "Actions" → "New repository secret"：

需要添加以下 Secrets：

| Secret 名称 | 说明 | 获取方法 |
|------------|------|----------|
| `FXC_EMAIL` | FreeXCraft 登录邮箱 | 你的 FreeXCraft 账号邮箱 |
| `FXC_PASS` | FreeXCraft 登录密码 | 你的 FreeXCraft 账号密码 |
| `FXC_SERVER_ID` | 服务器ID | FreeXCraft 面板中的服务器ID |
| `TG_BOT_TOKEN` | Telegram Bot Token | 创建 Bot 后从 @BotFather 获取 |
| `TG_USER_ID` | Telegram 用户ID | 从 @userinfobot 获取 |

可选 Secrets（如果需要代理）：

| Secret 名称 | 说明 |
|------------|------|
| `PROXY_URL` | 代理地址，如 `socks5h://host:port` |
| `PROXY_USER` | 代理用户名（如需认证） |
| `PROXY_PASS` | 代理密码（如需认证） |

### 步骤3：获取服务器ID

1. 登录 FreeXCraft 控制面板
2. 进入你的服务器页面
3. 查看浏览器地址栏，格式如：`https://freexcraft.com/dashboard/server/c2c11e40-1821-47c2-bd50-5651cdcbf268`
4. 最后一部分 (`c2c11e40-...`) 就是服务器ID

### 步骤4：配置定时任务（可选）

默认已配置每天北京时间 12:00（UTC 04:00）运行。如需修改：

1. 打开 `.github/workflows/freexcraft-renewal.yml`
2. 修改 `schedule.cron` 表达式
3. GitHub Actions 使用 UTC 时间，注意时区转换

### 步骤5：手动运行测试

1. 进入仓库的 "Actions" 选项卡
2. 选择 "FreeXCraft Auto Renewal" 工作流
3. 点击 "Run workflow" 手动触发
4. 查看运行日志，确认是否成功

## 文件说明
