import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
from urllib.parse import urlparse

# 普通网站列表
normal_urls = [
    "https://cf.vvhan.com/",
    "https://ip.164746.xyz",
    "http://ip.flares.cloud/",
    "https://vps789.com/cfip/?remarks=ip",
    "https://ipdb.030101.xyz/bestcfv4/",
    "https://www.wetest.vip/"
]

# JS 站点 API（直接返回文本或 JSON）
api_urls_text = [
    "https://addressesapi.090227.xyz/ct",  # 电信
    "https://addressesapi.090227.xyz/cm",  # 移动
    "https://addressesapi.090227.xyz/cu"   # 联通
]

api_urls_json = [
    "https://stock.hostmonit.com/CloudFlareYes"
]

# 正则表达式
ip_pattern = r"\b\d{1,3}(?:\.\d{1,3}){3}\b"
domain_pattern = r"\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def get_current_time():
    """获取当前时间格式化为字符串"""
    return datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

def extract_domain_from_url(url):
    """从URL中提取域名"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        # 移除www前缀
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return "unknown"

def fetch_normal():
    ip_set, domain_set = set(), set()
    for url in normal_urls:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            text_all = soup.get_text(separator="\n")
            
            # 提取域名来源
            source_domain = extract_domain_from_url(url)
            
            # 提取IP并添加端口和来源信息
            ips = re.findall(ip_pattern, text_all)
            for ip in ips:
                ip_with_info = f"{ip}:443#{get_current_time()}_{source_domain}"
                ip_set.add(ip_with_info)
            
            # 提取域名
            domains = re.findall(domain_pattern, text_all)
            for domain in domains:
                # 过滤掉明显不是优选域名的（如常见域名）
                if not any(common in domain.lower() for common in ['cloudflare', 'google', 'baidu', 'qq.com', 'localhost', 'example.com']):
                    domain_set.add(domain)
            
            print(f"✅ 普通 {url} -> {len(ips)} IP, {len(domains)} 域名")
        except Exception as e:
            print(f"❌ 普通 {url}: {e}")
    return ip_set, domain_set

def fetch_api_text():
    ip_set, domain_set = set(), set()
    for url in api_urls_text:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            text = r.text
            
            # 提取域名来源
            source_domain = extract_domain_from_url(url)
            # 添加运营商标识
            operator = url.split('/')[-1]  # ct, cm, cu
            source_with_operator = f"{source_domain}_{operator}"
            
            # 提取IP并添加端口和来源信息
            ips = re.findall(ip_pattern, text)
            for ip in ips:
                ip_with_info = f"{ip}:443#{get_current_time()}_{source_with_operator}"
                ip_set.add(ip_with_info)
            
            # 提取域名
            domains = re.findall(domain_pattern, text)
            for domain in domains:
                if not any(common in domain.lower() for common in ['cloudflare', 'google', 'baidu', 'qq.com', 'localhost', 'example.com']):
                    domain_set.add(domain)
            
            print(f"✅ API文本 {url} -> {len(ips)} IP, {len(domains)} 域名")
        except Exception as e:
            print(f"❌ API文本 {url}: {e}")
    return ip_set, domain_set

def fetch_api_json():
    ip_set, domain_set = set(), set()
    for url in api_urls_json:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            data = r.json()
            
            # 提取域名来源
            source_domain = extract_domain_from_url(url)
            
            # 处理不同的JSON格式
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        ip = item.get("ip")
                        if ip and re.match(ip_pattern, ip):
                            ip_with_info = f"{ip}:443#{get_current_time()}_{source_domain}"
                            ip_set.add(ip_with_info)
                        
                        domain = item.get("domain")
                        if domain and re.match(domain_pattern, domain):
                            if not any(common in domain.lower() for common in ['cloudflare', 'google', 'baidu', 'qq.com', 'localhost', 'example.com']):
                                domain_set.add(domain)
                    elif isinstance(item, str) and re.match(ip_pattern, item):
                        ip_with_info = f"{item}:443#{get_current_time()}_{source_domain}"
                        ip_set.add(ip_with_info)
            
            print(f"✅ API JSON {url} -> {len(ip_set)} IP, {len(domain_set)} 域名")
        except Exception as e:
            print(f"❌ API JSON {url}: {e}")
    return ip_set, domain_set

def clean_and_sort_ips(ip_set):
    """清理和排序IP地址"""
    cleaned_ips = []
    for ip_info in ip_set:
        # 提取纯IP用于排序
        ip_match = re.search(ip_pattern, ip_info)
        if ip_match:
            ip_pure = ip_match.group()
            # 将IP转换为数字用于排序
            ip_num = tuple(map(int, ip_pure.split('.')))
            cleaned_ips.append((ip_num, ip_info))
    
    # 按IP数字排序
    cleaned_ips.sort(key=lambda x: x[0])
    return [ip_info for _, ip_info in cleaned_ips]

if __name__ == "__main__":
    ip_total, domain_total = set(), set()

    print("🚀 开始获取Cloudflare优选IP和域名...")
    
    # 普通网站
    ip1, d1 = fetch_normal()
    ip_total.update(ip1); domain_total.update(d1)

    # API 文本接口
    ip2, d2 = fetch_api_text()
    ip_total.update(ip2); domain_total.update(d2)

    # API JSON接口
    ip3, d3 = fetch_api_json()
    ip_total.update(ip3); domain_total.update(d3)

    # 清理和排序IP
    sorted_ips = clean_and_sort_ips(ip_total)
    sorted_domains = sorted(domain_total)

    # 保存结果
    with open("ip.txt", "w", encoding="utf-8") as f:
        f.write(f"# Cloudflare优选IP和域名\n")
        f.write(f"# 生成时间: {get_current_time().replace('_', ' ')}\n")
        f.write(f"# 总计: {len(sorted_ips)} 个IP, {len(sorted_domains)} 个域名\n\n")
        
        f.write("# 优选IP (格式: IP:端口#时间_来源)\n")
        for ip_info in sorted_ips:
            f.write(ip_info + "\n")
        
        f.write("\n# 优选域名\n")
        for domain in sorted_domains:
            f.write(domain + "\n")

    print(f"\n🎉 完成！共获取 {len(sorted_ips)} 个IP, {len(sorted_domains)} 个域名")
    print(f"💾 结果已保存到 ip.txt")
    
    # 显示几个示例
    if sorted_ips:
        print(f"📝 IP格式示例: {sorted_ips[0]}")
