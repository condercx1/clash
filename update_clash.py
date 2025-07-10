# 文件名: update_clash.py
import os
import re
import requests
import yaml
from datetime import datetime

# --- 配置区 ---
RAW_URL = 'https://raw.githubusercontent.com/TopChina/proxy-list/main/README.md'
OUTPUT_YAML_FILENAME = '1.yaml' # 直接在当前目录生成

# 【新增】中转节点配置
# 这个节点将被用作所有HTTP代理的前置代理，但不会显示在用户的选择列表中。
TRANSIT_PROXY = {
    'name': '🇭🇰 香港Hytron中转',
    'type': 'ss',
    'server': '36.141.40.61',
    'port': 27490,
    'password': '67c5ce45-7b48-473e-bf25-e4c830b0ed24',
    'cipher': 'aes-128-gcm',
    'udp': True
}


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

# proxies部分由脚本完全重写，此处内容会被覆盖
proxies:
    - { name: 'placeholder', type: ss, server: 1.1.1.1, port: 80, cipher: aes-256-gcm, password: "password" }

# proxy-groups部分，脚本会在此基础上填充节点
proxy-groups:
    - { name: '🚀 节点选择', type: select, proxies: ['♻️ 自动选择', '💥 故障转移', 'DIRECT'] }
    - { name: '♻️ 自动选择', type: url-test, proxies: [], url: 'http://www.gstatic.com/generate_204', interval: 300 }
    - { name: '💥 故障转移', type: fallback, proxies: [], url: 'http://www.gstatic.com/generate_204', interval: 300 }
    - { name: '国外网站', type: select, proxies: ['🚀 节点选择', '♻️ 自动选择', '💥 故障转移', 'DIRECT'] }
    - { name: '国内网站', type: select, proxies: ['DIRECT', '🚀 节点选择'] }

rules:
    - 'GEOIP,LAN,DIRECT'
    - 'GEOIP,CN,国内网站'
    - 'MATCH,国外网站'
"""

def get_country_emoji_map_extended():
    """返回一个详尽的、基于中文名称的国家/地区到国旗 Emoji 的映射字典。"""
    # (此函数内容未改变，保持原样)
    return {
        # 亚洲
        "中国": "🇨🇳", "香港": "🇭🇰", "澳门": "🇲🇴", "台湾": "🇹🇼",
        "日本": "🇯🇵", "韩国": "🇰🇷", "朝鲜": "🇰🇵", "蒙古": "🇲🇳",
        "新加坡": "🇸🇬", "马来西亚": "🇲🇾", "泰国": "🇹🇭", "越南": "🇻🇳",
        "菲律宾": "🇵🇭", "印度尼西亚": "🇮🇩", "文莱": "🇧🇳", "柬埔寨": "🇰🇭",
        "老挝": "🇱🇦", "缅甸": "🇲🇲", "东帝汶": "🇹🇱",
        "印度": "🇮🇳", "巴基斯坦": "🇵🇰", "孟加拉国": "🇧🇩", "尼泊尔": "🇳🇵", # 修正了拼写
        "不丹": "🇧🇹", "斯里兰卡": "🇱🇰", "马尔代夫": "🇲🇻",
        "哈萨克斯坦": "🇰🇿", "乌兹别克斯坦": "🇺🇿", "吉尔吉斯斯坦": "🇰🇬", "塔吉克斯坦": "🇹🇯", "土库曼斯坦": "🇹🇲",
        "阿富汗": "🇦🇫", "伊朗": "🇮🇷", "伊拉克": "🇮🇶", "叙利亚": "🇸🇾",
        "约旦": "🇯🇴", "黎巴嫩": "🇱🇧", "巴勒斯坦": "🇵🇸", "以色列": "🇮🇱",
        "沙特阿拉伯": "🇸🇦", "阿拉伯联合酋长国": "🇦🇪", "阿联酋": "🇦🇪", "卡塔尔": "🇶🇦",
        "科威特": "🇰🇼", "巴林": "🇧🇭", "阿曼": "🇴🇲", "也门": "🇾🇪",
        "土耳其": "🇹🇷", "塞浦路斯": "🇨🇾", "格鲁吉亚": "🇬🇪", "亚美尼亚": "🇦🇲", "阿塞拜疆": "🇦🇿",
        # 欧洲
        "俄罗斯": "🇷🇺", "乌克兰": "🇺🇦", "白俄罗斯": "🇧🇾", "摩尔多瓦": "🇲🇩",
        "英国": "🇬🇧", "爱尔兰": "🇮🇪", "法国": "🇫🇷", "德国": "🇩🇪",
        "荷兰": "🇳🇱", "比利时": "🇧🇪", "卢森堡": "🇱🇺", "瑞士": "🇨🇭",
        "奥地利": "🇦🇹", "列支敦士登": "🇱🇮",
        "西班牙": "🇪🇸", "葡萄牙": "🇵🇹", "意大利": "🇮🇹", "希腊": "🇬🇷",
        "梵蒂冈": "🇻🇦", "圣马力诺": "🇸🇲", "马耳他": "🇲🇹", "安道尔": "🇦🇩",
        "挪威": "🇳🇴", "瑞典": "🇸🇪", "芬兰": "🇫🇮", "丹麦": "🇩🇰", "冰岛": "🇮🇸",
        "波兰": "🇵🇱", "捷克": "🇨🇿", "斯洛伐克": "🇸🇰", "匈牙利": "🇭🇺",
        "罗马尼亚": "🇷🇴", "保加利亚": "🇧🇬", "塞尔维亚": "🇷🇸", "克罗地亚": "🇭🇷",
        "斯洛文尼亚": "🇸🇮", "波斯尼亚和黑塞哥维那": "🇧🇦", "波黑": "🇧🇦", "黑山": "🇲🇪",
        "北马其顿": "🇲🇰", "阿尔巴尼亚": "🇦🇱", "科索沃": "🇽🇰",
        "立陶宛": "🇱🇹", "拉脱维亚": "🇱🇻", "爱沙尼亚": "🇪🇪",
        # 北美洲
        "美国": "🇺🇸", "加拿大": "🇨🇦", "墨西哥": "🇲🇽",
        "格陵兰": "🇬🇱", "百慕大": "🇧🇲",
        "危地马拉": "🇬🇹", "伯利兹": "🇧🇿", "萨尔瓦多": "🇸🇻", "洪都拉斯": "🇭🇳",
        "尼加拉瓜": "🇳🇮", "哥斯达黎加": "🇨🇷", "巴拿马": "🇵🇦",
        "古巴": "🇨🇺", "牙买加": "🇯🇲", "海地": "🇭🇹", "多米尼加": "🇩🇴",
        "波多黎各": "🇵🇷",
        # 南美洲
        "巴西": "🇧🇷", "阿根廷": "🇦🇷", "智利": "🇨🇱", "哥伦比亚": "🇨🇴",
        "秘鲁": "🇵🇪", "委内瑞拉": "🇻🇪", "厄瓜多尔": "🇪🇨", "玻利维亚": "🇧🇴",
        "巴拉圭": "🇵🇾", "乌拉圭": "🇺🇾", "圭亚那": "🇬🇾", "苏里南": "🇸🇷",
        # 非洲
        "埃及": "🇪🇬", "利比亚": "🇱🇾", "苏丹": "🇸🇩", "突尼斯": "🇹🇳",
        "阿尔及利亚": "🇩🇿", "摩洛哥": "🇲🇦",
        "埃塞俄比亚": "🇪🇹", "索马里": "🇸🇴", "肯尼亚": "🇰🇪", "坦桑尼亚": "🇹🇿",
        "乌干达": "🇺🇬", "卢旺达": "🇷🇼",
        "尼日利亚": "🇳🇬", "加纳": "🇬🇭", "科特迪瓦": "🇨🇮", "塞内加尔": "🇸🇳",
        "南非": "🇿🇦", "津巴布韦": "🇿🇼", "赞比亚": "🇿🇲", "纳米比亚": "🇳🇦", "博茨瓦纳": "🇧🇼",
        # 大洋洲
        "澳大利亚": "🇦🇺", "新西兰": "🇳🇿", "斐济": "🇫🇯", "巴布亚新几内亚": "🇵🇬",
        # 默认
        "未知地区": "🏳️"
    }

def parse_update_time(content):
    """从 README 内容中解析更新时间并格式化。"""
    # (此函数内容未改变，保持原样)
    try:
        section_match = re.search(r'## \*\*更新日期\*\*(.+?)(?=##|$)', content, re.DOTALL)
        if not section_match:
            print("警告: 未在README中找到“更新日期”部分。")
            return None
        
        section_content = section_match.group(1)
        
        date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日\s*(\d{2}:\d{2})', section_content)
        if not date_match:
            print("警告: 未能解析出具体的更新日期时间。")
            return None
            
        _year, month, day, time = date_match.groups()
        formatted_time = f"{int(month)}.{int(day)}/{time}"
        print(f"成功解析并格式化更新时间: {formatted_time}")
        return formatted_time
    except Exception as e:
        print(f"解析更新时间时发生错误: {e}")
        return None


def parse_proxies_from_readme(content):
    """从 README 内容中解析代理信息。"""
    # (此函数内容未改变，保持原样)
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


# --- 【核心修改】修改此函数以实现链式代理 ---
def generate_clash_config(proxies_data, template_str, update_time_str=None):
    """根据抓取的节点、更新时间和模板生成Clash配置，并实现链式代理。"""
    print("正在生成 Clash 配置文件...")
    config = yaml.safe_load(template_str)

    # 初始化节点列表和名称列表
    new_proxies_list = []
    # proxy_names 用于填充 proxy-groups，这是用户在UI上看到的列表
    proxy_names_for_user_selection = []
    
    # --- 步骤 1: 添加“假”的信息节点 (如果存在更新时间) ---
    if update_time_str:
        info_node_name = f"⏰: {update_time_str}"
        proxy_names_for_user_selection.append(info_node_name)
        new_proxies_list.append({
            'name': info_node_name,
            'type': 'ss',
            'server': 'update.time.info',
            'port': 1,
            'cipher': 'aes-256-gcm',
            'password': '0'
        })
    
    # --- 步骤 2: 添加“隐身”的中转节点 ---
    # 这个节点被添加到总的 proxies 列表中，但它的名字不会被加入到 proxy_names_for_user_selection
    # 因此它在后端存在，可以被链式调用，但在前端UI上不可见。
    new_proxies_list.append(TRANSIT_PROXY)
    print(f"已添加隐身中转节点: '{TRANSIT_PROXY['name']}'")


    # --- 步骤 3: 生成所有HTTP代理节点，并让他们通过中转节点 ---
    country_count = {}
    for proxy in proxies_data:
        country = proxy['country']
        country_count[country] = country_count.get(country, 0) + 1
        node_name = f"{proxy['emoji']} {country} {country_count[country]:02d}"
        
        # 将此节点名称添加到用户可选列表中
        proxy_names_for_user_selection.append(node_name)
        
        # 创建HTTP代理配置，并使用 'chain' 关键字指向中转节点
        http_proxy_with_chain = {
            'name': node_name,
            'type': 'http',
            'server': proxy['server'],
            'port': proxy['port'],
            'username': proxy['username'],
            'password': proxy['password'],
            # --- 这是实现链式代理的关键 ---
            'chain': TRANSIT_PROXY['name'] 
        }
        new_proxies_list.append(http_proxy_with_chain)

    # 1. 完全替换模板中的proxies部分
    config['proxies'] = new_proxies_list
    print(f"已将模板中的 'proxies' 替换为 {len(new_proxies_list)} 个节点 (包含信息节点和隐身中转节点)。")

    # 2. 遍历代理组，用我们准备好的、用户可见的节点列表来填充
    for group in config['proxy-groups']:
        # 对于自动测试组，只填充真实可用的HTTP代理节点
        # 我们通过切片 proxy_names_for_user_selection[1:] 来排除信息节点
        if group['name'] in ['♻️ 自动选择', '💥 故障转移']:
            real_proxy_names = proxy_names_for_user_selection[1:] if update_time_str else proxy_names_for_user_selection
            group['proxies'] = real_proxy_names
            print(f"已为代理组 '{group['name']}' 填充 {len(real_proxy_names)} 个真实节点。")
        
        # 对于手动选择组，添加所有用户可见的节点（包括信息节点）
        elif group['name'] in ['🚀 节点选择', '国外网站']:
            group['proxies'].extend(proxy_names_for_user_selection)
            print(f"已向代理组 '{group['name']}' 追加 {len(proxy_names_for_user_selection)} 个用户可见节点。")

    # 添加文件顶部的注释信息
    update_time_str_comment = f"# 配置生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
                              f"# 节点总数 (HTTP): {len(proxies_data)}\n" \
                              f"# 数据来源: {RAW_URL}\n" \
                              f"# 特别说明: 所有HTTP节点已配置通过 '{TRANSIT_PROXY['name']}' 进行链式代理。\n\n"
    
    # 将配置字典转换回YAML字符串
    final_yaml_str = yaml.dump(config, sort_keys=False, allow_unicode=True, indent=2)

    return update_time_str_comment + final_yaml_str

def main():
    """主执行流程"""
    print("开始执行任务...")
    try:
        response = requests.get(RAW_URL, timeout=30)
        response.raise_for_status()
        readme_content = response.text
    except requests.exceptions.RequestException as e:
        print(f"下载 README 文件失败: {e}")
        return
    
    formatted_update_time = parse_update_time(readme_content)
        
    proxies = parse_proxies_from_readme(readme_content)
    if not proxies:
        print("未能解析到任何代理，程序终止。")
        return
    
    final_config = generate_clash_config(proxies, CLASH_TEMPLATE, formatted_update_time)

    with open(OUTPUT_YAML_FILENAME, 'w', encoding='utf-8') as f:
        f.write(final_config)
    print(f"\n🎉 配置文件已成功生成: {OUTPUT_YAML_FILENAME}")

if __name__ == '__main__':
    main()
