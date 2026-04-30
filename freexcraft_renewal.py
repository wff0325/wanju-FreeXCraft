import requests
import os
import json
import base64
import time
import re
from datetime import datetime, timezone, timedelta

# ================= 配置 =================
# 从环境变量读取配置
SERVER_ID = os.getenv("FXC_SERVER_ID") or os.getenv("SERVER_ID") or "你的服务器ID"
EMAIL = os.getenv("FXC_EMAIL") or "你的邮箱"
PASSWORD = os.getenv("FXC_PASS") or "你的密码"

# 代理配置 (可选)
PROXY_URL = os.getenv("PROXY_URL")
PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")

# Telegram 通知配置
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_USER_ID")

def get_proxies():
    """构造代理配置"""
    if PROXY_URL:
        if PROXY_USER and PROXY_PASS:
            # 带认证的代理
            proxy_url = PROXY_URL.replace("://", f"://{PROXY_USER}:{PROXY_PASS}@")
        else:
            proxy_url = PROXY_URL
        
        # 确保使用 socks5h 协议（支持域名解析）
        if proxy_url.startswith("socks5"):
            return {
                "http": proxy_url,
                "https": proxy_url
            }
        else:
            return {
                "http": proxy_url,
                "https": proxy_url
            }
    return None

PROXIES = get_proxies()

def send_tg_notification(content):
    """发送 Telegram 通知"""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("⚠️ 未配置 TG 通知环境变量")
        return
    
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": content, "parse_mode": "HTML"}
    
    try:
        # 如果有代理则使用代理
        proxies = PROXIES or {}
        response = requests.post(url, json=payload, timeout=15, proxies=proxies)
        
        if response.status_code == 200:
            print("📢 Telegram 通知已发送")
        else:
            print(f"❌ TG 通知发送失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ TG 通知发送失败: {e}")

def fetch_live_configs(session):
    """全自动抓取动态配置"""
    configs = {"action_id": None, "url": None, "key": None}
    try:
        print("🕵️ 正在抓取动态配置...")
        res = session.get(f"https://freexcraft.com/dashboard/server/{SERVER_ID}", timeout=15)
        
        # 查找JS文件
        js_files = re.findall(r'/_next/static/chunks/[^"]+\.js', res.text)
        print(f"🔍 找到 {len(js_files)} 个JS文件")
        
        for js_path in reversed(js_files):
            try:
                js_url = f"https://freexcraft.com{js_path}"
                js_response = session.get(js_url, timeout=10)
                js_content = js_response.text
                
                # 查找 action_id (40-45字符的十六进制字符串)
                if "Extend Time" in js_content and not configs["action_id"]:
                    match = re.search(r'[a-f0-9]{40,45}', js_content)
                    if match: 
                        configs["action_id"] = match.group(0)
                        print(f"✅ 找到 action_id: {configs['action_id'][:10]}...")
                
                # 查找 JWT key (eyJ开头的JWT令牌)
                if "eyJ" in js_content and not configs["key"]:
                    match = re.search(r'eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*', js_content)
                    if match: 
                        configs["key"] = match.group(0)
                        print(f"✅ 找到 API key")
                
                # 查找 supabase URL
                if "supabase.co" in js_content and not configs["url"]:
                    match = re.search(r'https://[a-z0-9]+\.supabase\.co', js_content)
                    if match: 
                        configs["url"] = match.group(0)
                        print(f"✅ 找到 Supabase URL: {configs['url']}")
                
                if all(configs.values()): 
                    break
            except Exception as e:
                print(f"⚠️ 读取JS文件失败 {js_path}: {e}")
                continue
        
        return configs
    except Exception as e:
        print(f"❌ 抓取配置失败: {e}")
        return configs

def run_task():
    """执行续期任务"""
    # 创建会话
    session = requests.Session()
    
    # 设置代理（如果有）
    if PROXIES:
        session.proxies.update(PROXIES)
    
    # 设置请求头
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    })
    
    print("🚀 开始执行 FreeXCraft 续期任务")
    print(f"📧 邮箱: {EMAIL}")
    print(f"🆔 服务器ID: {SERVER_ID}")
    
    # 获取动态配置
    live = fetch_live_configs(session)
    
    if not live['action_id']:
        error_msg = "❌ 自动提取参数失败，请检查服务器ID是否正确"
        print(error_msg)
        send_tg_notification(f"<b>FreeXCraft 续期失败</b>\n━━━━━━━━━━━━━━━━━━\n{error_msg}")
        return
    
    print(f"✅ 配置捕获成功! ID: {live['action_id'][:10]}...")
    
    try:
        # 1. 登录
        login_headers = {
            "apikey": live['key'],
            "Content-Type": "application/json"
        }
        
        print("🔐 正在登录...")
        r_login = session.post(
            f"{live['url']}/auth/v1/token?grant_type=password",
            json={"email": EMAIL, "password": PASSWORD},
            headers=login_headers,
            timeout=15
        )
        
        if r_login.status_code != 200:
            error_msg = f"❌ 登录失败: {r_login.status_code} - {r_login.text[:100]}"
            print(error_msg)
            send_tg_notification(f"<b>FreeXCraft 续期失败</b>\n━━━━━━━━━━━━━━━━━━\n{error_msg}")
            return
        
        auth_data = r_login.json()
        print("✅ 登录成功")
        
        # 2. 构造 Cookie
        cookie_dict = {
            "access_token": auth_data["access_token"],
            "refresh_token": auth_data["refresh_token"],
            "user": auth_data["user"]
        }
        
        cookie_val = f"base64-{base64.b64encode(json.dumps(cookie_dict).encode()).decode()}"
        project_id = live['url'].split('//')[1].split('.')[0]
        session.cookies.set(f"sb-{project_id}-auth-token", cookie_val, domain="freexcraft.com")
        
        # 3. 发送续期请求
        print("📡 正在发送续期指令...")
        
        action_headers = {
            "Accept": "text/x-component",
            "Content-Type": "text/plain;charset=UTF-8",
            "Next-Action": live['action_id'],
            "Next-Router-State-Tree": "%5B%22%22%2C%7B%22children%22%3A%5B%22dashboard%22%2C%7B%22children%22%3A%5B%22server%22%2C%7B%22children%22%3A%5B%5B%22id%22%2C%22" + SERVER_ID + "%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%2Ctrue%5D",
            "Referer": f"https://freexcraft.com/dashboard/server/{SERVER_ID}",
            "Origin": "https://freexcraft.com"
        }
        
        r_action = session.post(
            f"https://freexcraft.com/dashboard/server/{SERVER_ID}",
            data=f'["{SERVER_ID}"]',
            headers=action_headers,
            timeout=15
        )
        
        if r_action.status_code == 200:
            print("🎉 续期请求发送成功，查询结果中...")
            time.sleep(5)  # 等待服务器处理
            
            # 获取最新服务器信息
            info_headers = {
                "apikey": live['key'],
                "Authorization": f"Bearer {auth_data['access_token']}"
            }
            
            r_info = session.get(
                f"{live['url']}/rest/v1/servers?id=eq.{SERVER_ID}&select=*",
                headers=info_headers,
                timeout=15
            )
            
            if r_info.status_code == 200 and r_info.json():
                data = r_info.json()[0]
                deadline_str = data.get('renewal_deadline')
                server_name = data.get('name', 'Unknown')
                
                # 时间格式化处理
                try:
                    # 假设返回的是 UTC 时间
                    if deadline_str.endswith('Z'):
                        utc_dt = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                    else:
                        utc_dt = datetime.fromisoformat(deadline_str)
                    
                    # 转换为北京时间 (UTC+8)
                    bj_dt = utc_dt + timedelta(hours=8)
                    bj_time_str = bj_dt.strftime('%Y-%m-%d %H:%M')
                    
                    report = (
                        f"✅ <b>FreeXCraft 续期成功</b>\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"🖥 <b>服务器:</b> {server_name}\n"
                        f"📅 <b>过期时间:</b> {bj_time_str} (北京时间)\n"
                        f"🚀 <b>状态:</b> 自动续期任务已完成"
                    )
                    
                    send_tg_notification(report)
                    print(f"🎉 任务圆满完成! 服务器: {server_name}, 下次到期: {bj_time_str}")
                    
                except Exception as time_error:
                    print(f"⚠️ 时间解析失败: {time_error}")
                    send_tg_notification(
                        f"✅ <b>FreeXCraft 续期成功</b>\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"🖥 <b>服务器:</b> {server_name}\n"
                        f"📅 <b>过期时间:</b> {deadline_str}\n"
                        f"⚠️ <b>注意:</b> 时间解析失败，请检查面板"
                    )
            else:
                error_msg = f"❌ 获取服务器信息失败: {r_info.status_code}"
                print(error_msg)
                send_tg_notification(f"<b>FreeXCraft 续期警告</b>\n━━━━━━━━━━━━━━━━━━\n续期请求已发送，但无法验证结果\n状态码: {r_info.status_code}")
        else:
            error_msg = f"❌ 续期请求失败: {r_action.status_code}"
            print(error_msg)
            send_tg_notification(f"<b>FreeXCraft 续期失败</b>\n━━━━━━━━━━━━━━━━━━\n{error_msg}")
            
    except Exception as e:
        error_msg = f"❌ 任务执行异常: {str(e)}"
        print(error_msg)
        send_tg_notification(f"<b>FreeXCraft 续期失败</b>\n━━━━━━━━━━━━━━━━━━\n{error_msg}")

if __name__ == "__main__":
    run_task()
