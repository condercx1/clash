# 文件名: update_clash.py
import os
import re
import requests
import yaml
from datetime import datetime

# --- 配置区 ---
RAW_URL = 'https://raw.githubusercontent.com/TopChina/proxy-list/main/README.md'
OUTPUT_YAML_FILENAME = '1.yaml'


CLASH_TEMPLATE = r"""
# =============================== 代理配置 ===============================
# 此部分由脚本自动管理，保留用于定义锚点
dy: &dy
    type: http
    udp: true
    interval: 86400
    proxy: DIRECTLY
    lazy: true
    health-check:
      enable: true
      url: https://cp.cloudflare.com/generate_204
      interval: 600
      timeout: 5 # 秒
      lazy: true
      expected-status: "204"
      method: HEAD
    smux:
      enabled: true
      padding: true
      protocol: smux

# --- 占位符锚点，脚本将填充节点到引用此锚点的组 ---
# 我们不再使用 proxy-providers，而是直接填充 proxies 列表
# 但保留 *u 锚点，以便脚本识别需要填充的组
u: &u
  use: [] # 此处留空，脚本会动态填充 proxies

# =============================== 节点信息 (由脚本生成) ===============================
proxies:
  - {name: DIRECTLY, type: direct, udp: true}

# =============================== DNS 配置 ===============================
dns:
  enable: true
  ipv6: false
  listen: 0.0.0.0:1053
  prefer-h3: true
  respect-rules: true
  enhanced-mode: fake-ip
  cache-algorithm: arc
  cache-size: 2048
  use-hosts: false
  use-system-hosts: false
  fake-ip-range: 198.18.0.1/16
  fake-ip-filter-mode: blacklist
  fake-ip-filter:
    - "rule-set:private_domain,cn_domain"
    - "geosite:connectivity-check"
    - "geosite:private"
    - "rule-set:fake_ip_filter_DustinWin"
    - "*"
  default-nameserver: [223.5.5.5, 119.29.29.29, system]
  proxy-server-nameserver: [https://1.1.1.1/dns-query, https://dns.google/dns-query, 1.1.1.1, 8.8.8.8]
  nameserver: [https://1.1.1.1/dns-query, https://dns.google/dns-query, https://dns.alidns.com/dns-query, https://doh.pub/dns-query]
  nameserver-policy:
    "geosite:cn,private": [https://223.5.5.5/dns-query, https://doh.pub/dns-query]
    "geo:cn": [https://223.5.5.5/dns-query]
  fallback: [1.1.1.1, 8.8.8.8]

# =============================== 控制面板 ===============================
external-controller: 127.0.0.1:9090
secret: "123465."
external-ui: "./ui"
external-ui-url: "https://github.com/Zephyruso/zashboard/releases/latest/download/dist.zip"

# =============================== 全局设置 ===============================
port: 7890
socks-port: 7891
redir-port: 7892
mixed-port: 7893
tproxy-port: 7894
allow-lan: true
mode: rule
bind-address: "*"
ipv6: false
unified-delay: true
tcp-concurrent: true
log-level: warning
find-process-mode: 'strict'
global-client-fingerprint: chrome
keep-alive-idle: 600
keep-alive-interval: 15
disable-keep-alive: false
profile:
  store-selected: true
  store-fake-ip: true

# =============================== 流量嗅探配置 ===============================
sniffer:
  enable: true
  sniff:
    HTTP: {ports: [80, 8080-8880], override-destination: true}
    TLS: {ports: [443, 8443]}
  force-domain: ["+.v2ex.com"]
  skip-domain: ["+.baidu.com", "+.bilibili.com"]

# =============================== TUN 配置 ===============================
tun:
  enable: true
  stack: mixed
  auto-route: true
  auto-redirect: true
  auto-detect-interface: true
  strict-route: true
  dns-hijack: [any:53]
  mtu: 1500
  gso: true
  gso-max-size: 65536
  udp-timeout: 300

# =============================== GEO 数据库配置 ===============================
geodata-mode: true
geodata-loader: memconservative
geo-auto-update: true
geo-update-interval: 48
geox-url:
  geoip: "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geoip.dat"
  geosite: "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geosite.dat"
  mmdb: "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geoip.metadb"

# =============================== 代理组设置 ===============================
proxy-groups:
  - name: Proxy
    type: select
    proxies:
      - AI
      - 自动选择
      - 全部节点
      - DIRECTLY
    icon: "https://raw.githubusercontent.com/Mithcell-Ma/icon/refs/heads/main/Manual_Test_Log.png"

  - name: AI
    type: select
    proxies: [AI_稳定节点, AI_自动优选]
    icon: "https://github.com/DustinWin/ruleset_geodata/releases/download/icons/ai.png"

  - name: AI_稳定节点
    type: fallback
    proxies: [] # 脚本将填充
    url: https://cp.cloudflare.com/generate_204
    interval: 7200
    lazy: true
    filter: "(?i)(🇺🇸|美国|US|🇸🇬|新加坡)" # 简单筛选美、新节点作为AI备选
    icon: "https://testingcf.jsdelivr.net/gh/aihdde/Rules@master/icon/ai.png"

  - name: AI_自动优选
    type: url-test
    proxies: [] # 脚本将填充
    url: https://cp.cloudflare.com/generate_204
    interval: 3600
    lazy: false
    filter: "(?i)(🇺🇸|美国|US|🇸🇬|新加坡)" # 简单筛选美、新节点作为AI备选
    icon: "https://raw.githubusercontent.com/Mithcell-Ma/icon/refs/heads/main/ai_backup.png"

  - name: 自动选择
    type: url-test
    proxies: [] # 脚本将填充
    url: https://cp.cloudflare.com/generate_204
    interval: 1800
    lazy: false
    icon: "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/icon/color/urltest.png"

  - {name: TikTok, type: select, proxies: [自动选择, 全部节点, DIRECTLY], icon: "https://testingcf.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/TikTok.png"}
  - {name: YouTube, type: select, proxies: [Proxy, DIRECTLY], icon: "https://testingcf.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/YouTube.png"}
  - {name: Speedtest, type: select, proxies: [DIRECTLY, Proxy], icon: "https://testingcf.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Speedtest.png"}
  - {name: OneDrive, type: select, proxies: [DIRECTLY, Proxy], icon: "https://testingcf.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/OneDrive.png"}
  - {name: Trackerslist, type: select, proxies: [DIRECTLY, Proxy], icon: "https://github.com/DustinWin/ruleset_geodata/releases/download/icons/trackerslist.png"}


  - name: 全部节点
    type: select
    proxies: [] # 脚本将填充
    icon: "https://testingcf.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/World_Map.png"

  - name: 漏网之鱼
    type: select
    proxies: [Proxy, DIRECTLY]
    icon: "https://testingcf.jsdelivr.net/gh/aihdde/Rules@master/icon/fish.png"

# =============================== 规则设置 ===============================
rules:
  - RULE-SET,AWAvenue_Ads_Rule,REJECT
  - RULE-SET,blackmatrix7_ad,REJECT
  - RULE-SET,porn,REJECT
  - RULE-SET,cn_ip,DIRECTLY,no-resolve
  - RULE-SET,telegram_ip,Proxy,no-resolve
  - RULE-SET,Telegram_No_Resolve,Proxy,no-resolve
  - RULE-SET,geoip_cloudflare,AI,no-resolve
  - RULE-SET,geoip_cloudfront,DIRECTLY,no-resolve
  - RULE-SET,geoip_facebook,Proxy,no-resolve
  - RULE-SET,geoip_netflix,Proxy,no-resolve
  - RULE-SET,geoip_twitter,Proxy,no-resolve
  - DOMAIN-SUFFIX,julebu.co,DIRECTLY
  - RULE-SET,blackmatrix7_direct,DIRECTLY
  - RULE-SET,private_domain,DIRECTLY
  - RULE-SET,cn_domain,DIRECTLY
  - RULE-SET,apple_cn_domain,DIRECTLY
  - DOMAIN-SUFFIX,lingq.com,AI
  - DOMAIN-SUFFIX,youglish.com,AI
  - DOMAIN-SUFFIX,deepl.com,AI
  - DOMAIN-SUFFIX,chat.openai.com,AI
  - DOMAIN-SUFFIX,grammarly.com,AI
  - DOMAIN-KEYWORD,sci-hub,AI
  - RULE-SET,ai,AI
  - RULE-SET,youtube_domain,YouTube
  - RULE-SET,tiktok_domain,TikTok
  - RULE-SET,netflix_domain,Proxy
  - RULE-SET,disney_domain,Proxy
  - RULE-SET,onedrive_domain,OneDrive
  - RULE-SET,speedtest_domain,Speedtest
  - RULE-SET,telegram_domain,Proxy
  - RULE-SET,gfw_domain,Proxy
  - RULE-SET,geolocation-!cn,Proxy
  - RULE-SET,proxy,Proxy
  - RULE-SET,trackerslist,Trackerslist
  - MATCH,漏网之鱼

# =============================== 规则提供者 ===============================
rule-anchor:
  ip: &ip {type: http, interval: 86400, behavior: ipcidr, format: mrs}
  domain: &domain {type: http, interval: 86400, behavior: domain, format: mrs}
  class: &class {type: http, interval: 86400, behavior: classical, format: text}
  yaml: &yaml {type: http, interval: 86400, behavior: domain, format: yaml}
  classical_yaml: &classical_yaml {type: http, interval: 86400, behavior: classical, format: yaml}
rule-providers:
  AWAvenue_Ads_Rule: {<<: *yaml, path: ./ruleset/AWAvenue_Ads_Rule_Clash.yaml, url: "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main//Filters/AWAvenue-Ads-Rule-Clash.yaml"}
  blackmatrix7_ad: {<<: *yaml, path: ./ruleset/blackmatrix7_ad.yaml, url: "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Advertising/Advertising.yaml"}
  porn: {<<: *domain, path: ./ruleset/category-porn.mrs, url: "https://github.com/MetaCubeX/meta-rules-dat/raw/refs/heads/meta/geo/geosite/category-porn.mrs"}
  fake_ip_filter_DustinWin: {<<: *domain, path: ./ruleset/fake_ip_filter_DustinWin.mrs, url: "https://github.com/DustinWin/ruleset_geodata/releases/download/mihomo-ruleset/fakeip-filter.mrs"}
  blackmatrix7_direct: {<<: *yaml, path: ./ruleset/blackmatrix7_direct.yaml, url: "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Direct/Direct.yaml"}
  private_domain: {<<: *domain, path: ./ruleset/private_domain.mrs, url: "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/private.mrs"}
  cn_domain: {<<: *domain, path: ./ruleset/cn_domain.mrs, url: "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/cn.mrs"}
  cn_ip: {<<: *ip, path: ./ruleset/cn_ip.mrs, url: "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geoip/cn.mrs"}
  trackerslist: {<<: *domain, path: ./ruleset/trackerslist.mrs, url: "https://github.com/DustinWin/ruleset_geodata/raw/refs/heads/mihomo-ruleset/trackerslist.mrs"}
  proxy: {<<: *domain, path: ./ruleset/proxy.mrs, url: "https://github.com/DustinWin/ruleset_geodata/releases/download/mihomo-ruleset/proxy.mrs"}
  gfw_domain: {<<: *domain, path: ./ruleset/gfw_domain.mrs, url: "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/gfw.mrs"}
  geolocation-!cn: {<<: *domain, path: ./ruleset/geolocation-!cn.mrs, url: "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/geolocation-!cn.mrs"}
  ai: {<<: *domain, path: ./ruleset/ai, url: "https://github.com/DustinWin/ruleset_geodata/releases/download/mihomo-ruleset/ai.mrs"}
  geoip_cloudflare: {<<: *ip, path: ./ruleset/geoip_cloudflare.mrs, url: "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/raw/refs/heads/meta/geo/geoip/cloudflare.mrs"}
  youtube_domain: {<<: *domain, path: ./ruleset/youtube_domain.mrs, url: "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/youtube.mrs"}
  tiktok_domain: {<<: *domain, path: ./ruleset/tiktok_domain.mrs, url: "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/tiktok.mrs"}
  netflix_domain: {<<: *domain, path: ./ruleset/netflix_domain.mrs, url: "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/refs/heads/meta/geo/geosite/netflix.mrs"}
  disney_domain: {<<: *domain, path: ./ruleset/disney_domain.mrs, url: "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/refs/heads/meta/geo/geosite/disney.mrs"}
  geoip_netflix: {<<: *ip, path: ./ruleset/geoip_netflix.mrs, url: "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geoip/netflix.mrs"}
  geoip_twitter: {<<: *ip, path: ./ruleset/geoip_twitter.mrs, url: "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geoip/twitter.mrs"}
  geoip_facebook: {<<: *ip, path: ./ruleset/geoip_facebook.mrs, url: "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geoip/facebook.mrs"}
  telegram_domain: {<<: *yaml, path: ./ruleset/telegram_domain.yaml, url: "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Telegram/Telegram.yaml"}
  telegram_ip: {<<: *ip, path: ./ruleset/telegram_ip.mrs, url: "https://github.com/DustinWin/ruleset_geodata/raw/refs/heads/mihomo-ruleset/telegramip.mrs"}
  Telegram_No_Resolve: {<<: *classical_yaml, path: ./ruleset/Telegram_No_Resolve.yaml, url: "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/Telegram/Telegram_No_Resolve.yaml"}
  apple_cn_domain: {<<: *domain, path: ./ruleset/apple_cn_domain.mrs, url: "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/apple-cn.mrs"}
  onedrive_domain: {<<: *domain, path: ./ruleset/onedrive_domain.mrs, url: "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/onedrive.mrs"}
  speedtest_domain: {<<: *domain, path: ./ruleset/speedtest_domain.mrs, url: "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/ookla-speedtest.mrs"}
  geoip_cloudfront: {<<: *ip, path: ./ruleset/geoip_cloudfront.mrs, url: "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geoip/cloudfront.mrs"}
"""

# --- 函数区 (大部分函数与之前相同) ---

def get_country_emoji_map_extended():
    """返回一个详尽的、基于中文名称的国家/地区到国旗 Emoji 的映射字典。"""
    return {
        # 亚洲
        "中国": "🇨🇳", "香港": "🇭🇰", "澳门": "🇲🇴", "台湾": "🇹🇼",
        "日本": "🇯🇵", "韩国": "🇰🇷", "朝鲜": "🇰🇵", "蒙古": "🇲🇳",
        "新加坡": "🇸🇬", "马来西亚": "🇲🇾", "泰国": "🇹🇭", "越南": "🇻🇳",
        "菲律宾": "🇵🇭", "印度尼西亚": "🇮🇩", "文莱": "🇧🇳", "柬埔寨": "🇰🇭",
        "老挝": "🇱🇦", "缅甸": "🇲🇲", "东帝汶": "🇹🇱",
        "印度": "🇮🇳", "巴基斯坦": "🇵🇰", "孟加拉国": "🇧🇩", "尼泊尔": "🇳🇵",
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

def parse_proxies_from_readme(content):
    """从 README 内容中解析代理信息。"""
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

# --- 【关键修改】生成配置文件的函数 ---
def generate_clash_config(proxies_data, template_str):
    """使用高级模板生成 Clash 配置文件。"""
    print("正在基于高级模板生成 Clash 配置文件...")
    
    # 加载 YAML 模板
    config = yaml.safe_load(template_str)
    
    # 生成新的代理节点列表和节点名称列表
    new_proxies_list = []
    proxy_names = []
    country_count = {}
    
    for proxy in proxies_data:
        country = proxy['country']
        country_count[country] = country_count.get(country, 0) + 1
        # 格式化节点名称，例如：🇭🇰 香港 01
        node_name = f"{proxy['emoji']} {country} {country_count[country]:02d}"
        proxy_names.append(node_name)
        
        # 创建代理节点字典
        new_proxies_list.append({
            'name': node_name,
            'type': 'http',
            'server': proxy['server'],
            'port': proxy['port'],
            'username': proxy['username'],
            'password': proxy['password']
        })
        
    # 保留模板中原有的 DIRECTLY 节点，并添加所有新抓取的节点
    # config['proxies'] 的初始值是: [{'name': 'DIRECTLY', 'type': 'direct', 'udp': True}]
    config['proxies'].extend(new_proxies_list)

    # 需要自动填充节点列表的代理组
    groups_to_fill = [
        "AI_稳定节点", "AI_自动优选", "自动选择", 
        "全部节点", "香港节点", "美国节点", "新加坡节点", "日本节点"
    ]
    
    # 遍历所有代理组，为需要填充的组添加节点名称列表
    for group in config['proxy-groups']:
        if group['name'] in groups_to_fill:
            # 直接将所有抓取到的节点名称赋给这些组的 proxies 列表
            # Clash 的 filter 功能会自动筛选出符合条件的节点
            group['proxies'] = proxy_names
            print(f"已为代理组 '{group['name']}' 填充 {len(proxy_names)} 个备选节点。")

    # 准备最终输出的 YAML 字符串
    # 添加更新信息注释头
    update_time_str = f"# =============================== 更新信息 ===============================\n" \
                      f"# 配置生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
                      f"# 节点总数: {len(new_proxies_list)}\n" \
                      f"# 数据来源: {RAW_URL}\n#\n"

    # 使用PyYAML库将配置字典转换回YAML格式字符串
    # sort_keys=False 保持原始顺序
    # allow_unicode=True 支持中文和Emoji
    final_yaml_str = yaml.dump(config, sort_keys=False, allow_unicode=True, indent=2)
    
    return update_time_str + final_yaml_str

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
        
    proxies = parse_proxies_from_readme(readme_content)
    if not proxies:
        print("未能解析到任何代理，程序终止。")
        return
    
    final_config = generate_clash_config(proxies, CLASH_TEMPLATE)
    with open(OUTPUT_YAML_FILENAME, 'w', encoding='utf-8') as f:
        f.write(final_config)
    print(f"\n🎉 配置文件已成功生成: {OUTPUT_YAML_FILENAME}")

if __name__ == '__main__':
    main()
