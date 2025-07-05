# 文件名: update_clash.py
import os
import re
import requests
import yaml
from datetime import datetime

# --- 配置区 ---
RAW_URL = 'https://raw.githubusercontent.com/TopChina/proxy-list/main/README.md'
OUTPUT_YAML_FILENAME = '1.yaml' # 直接在当前目录生成

# Clash 模板 (API部分可以保留，不影响使用)
CLASH_TEMPLATE = r"""
mixed-port: 7890
allow-lan: true
bind-address: '*'
mode: rule
log-level: info
external-controller: '127.0.0.1:9090'
secret: ''
dns:
    enable: true
    ipv6: false
    default-nameserver: [223.5.5.5, 119.29.29.29]
    enhanced-mode: fake-ip
    fake-ip-range: 198.18.0.1/16
    use-hosts: true
    nameserver: ['https://doh.pub/dns-query', 'https://dns.alidns.com/dns-query']
    fallback: ['https://doh.dns.sb/dns-query', 'https://dns.cloudflare.com/dns-query', 'https://dns.twnic.tw/dns-query', 'tls://8.8.4.4:853']
    fallback-filter: { geoip: true, ipcidr: [240.0.0.0/4, 0.0.0.0/32] }
proxies:
    - { name: 'placeholder', type: ss, server: 1.1.1.1, port: 80, cipher: aes-256-gcm, password: "password" }
proxy-groups:
    - { name: '🚀 节点选择', type: select, proxies: [♻️ 自动选择, 💥 故障转移, DIRECT] }
    - { name: '♻️ 自动选择', type: url-test, proxies: [], url: 'http://www.gstatic.com/generate_204', interval: 300 }
    - { name: '💥 故障转移', type: fallback, proxies: [], url: 'http://www.gstatic.com/generate_204', interval: 300 }
    - { name: '国外网站', type: select, proxies: [🚀 节点选择, ♻️ 自动选择, 💥 故障转移, DIRECT] }
    - { name: '国内网站', type: select, proxies: [DIRECT, 🚀 节点选择] }
rules:
    - 'GEOIP,LAN,DIRECT'
    - 'GEOIP,CN,国内网站'
    - 'MATCH,国外网站'
"""

def get_country_emoji_map_extended():
    return { "中国": "🇨🇳", "香港": "🇭🇰", "澳门": "🇲🇴", "台湾": "🇹🇼", "日本": "🇯🇵", "韩国": "🇰🇷", "新加坡": "🇸🇬", "马来西亚": "🇲🇾", "泰国": "🇹🇭", "越南": "🇻🇳", "菲律宾": "🇵🇭", "印度尼西亚": "🇮🇩", "印度": "🇮🇳", "土耳其": "🇹🇷", "阿联酋": "🇦🇪", "俄罗斯": "🇷🇺", "乌克兰": "🇺🇦", "英国": "🇬🇧", "法国": "🇫🇷", "德国": "🇩🇪", "荷兰": "🇳🇱", "瑞士": "🇨🇭", "西班牙": "🇪🇸", "意大利": "🇮🇹", "瑞典": "🇸🇪", "美国": "🇺🇸", "加拿大": "🇨🇦", "墨西哥": "🇲🇽", "巴西": "🇧🇷", "阿根廷": "🇦🇷", "澳大利亚": "🇦🇺", "新西兰": "🇳🇿", "南非": "🇿🇦", "埃及": "🇪🇬", "未知地区": "🏳️" }

def parse_proxies_from_readme(content):
    print("正在解析代理信息...")
    proxies = []
    pattern = re.compile(r'\|\s*([^|]+?:\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|')
    emoji_map = get_country_emoji_map_extended()
    for line in content.splitlines():
        match = pattern.match(line)
        if match:
            ip_port, country, username = (g.strip() for g in match.groups())
            if 'IP地址' in ip_port or '---' in ip_port: continue
            try:
                server, port_str = ip_port.split(':')
                emoji = emoji_map.get(country, '🏳️')
                proxies.append({"server": server, "port": int(port_str), "country": country, "emoji": emoji, "username": username, "password": "1"})
            except ValueError:
                print(f"警告: 无法解析行 -> {line}")
                continue
    print(f"成功解析到 {len(proxies)} 个代理节点。")
    return proxies

def generate_clash_config(proxies_data, template_str):
    print("正在生成 Clash 配置文件...")
    config = yaml.safe_load(template_str)
    new_proxies_list, proxy_names, country_count = [], [], {}
    for proxy in proxies_data:
        country = proxy['country']
        country_count[country] = country_count.get(country, 0) + 1
        node_name = f"{proxy['emoji']} {country} {country_count[country]:02d}"
        proxy_names.append(node_name)
        new_proxies_list.append({'name': node_name, 'type': 'http', 'server': proxy['server'], 'port': proxy['port'], 'username': proxy['username'], 'password': proxy['password']})
    config['proxies'] = new_proxies_list
    for group in config['proxy-groups']:
        if group['name'] in ['🚀 节点选择', '国外网站']: group['proxies'].extend(proxy_names)
        elif group['name'] in ['♻️ 自动选择', '💥 故障转移']: group['proxies'] = proxy_names
    update_time_str = f"# 配置生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n# 节点总数: {len(new_proxies_list)}\n# 数据来源: {RAW_URL}\n\n"
    final_yaml_str = yaml.dump(config, sort_keys=False, allow_unicode=True, indent=2)
    return update_time_str + final_yaml_str

def main():
    print("开始执行任务...")
    try:
        response = requests.get(RAW_URL, timeout=20)
        response.raise_for_status()
        readme_content = response.text
    except requests.exceptions.RequestException as e:
        print(f"下载 README 文件失败: {e}")
        return
        
    proxies = parse_proxies_from_readme(readme_content)
    if not proxies:
        print("未能解析到任何代理，程序终止。")
        return
    
    final_config = generate_clash_config(proxies, CLASH_TEMPLATE)
    with open(OUTPUT_YAML_FILENAME, 'w', encoding='utf-8') as f:
        f.write(final_config)
    print(f"🎉 配置文件已成功生成: {OUTPUT_YAML_FILENAME}")

if __name__ == '__main__':
    main()

