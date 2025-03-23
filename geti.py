import requests
from concurrent.futures import ThreadPoolExecutor
import time
import string
import itertools
import os
from queue import Queue
import threading

# 目标 URL
url = "http://mt316.com/e/search/index.php"

# 请求数据模板
data_template = {
    "keyboard": None,  # 关键字将被动态替换
    "submit": "",
    "show": "title",
    "tempid": "1",
    "tbname": "news",
    "mid": "1",
    "dopost": "search"
}

# 请求头（可根据需要添加更多头信息）
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 已请求关键词的文件路径
requested_keywords_file = "geti.txt"

# 线程安全的队列，用于存储已请求的关键词
requested_keywords_queue = Queue()

def generate_keywords():
    """生成关键词列表：1-10000 和 a-zzz"""
    keywords = []

    # 添加数字 1 到 10001
    for i in range(1, 10001):
        keywords.append(str(i))

    # 添加字母组合 a 到 zzz
    alphabet = string.ascii_lowercase  # a-z
    for i in range(1, 4):  # 生成长度为 1 到 3 的组合
        for combination in itertools.product(alphabet, repeat=i):
            keywords.append("".join(combination))

    return keywords

def read_requested_keywords():
    """读取已请求的关键词"""
    if not os.path.exists(requested_keywords_file):
        return set()
    
    with open(requested_keywords_file, "r") as file:
        requested_keywords = set(line.strip() for line in file)
    return requested_keywords

def save_requested_keywords():
    """从队列中读取已请求的关键词并保存到文件"""
    while True:
        time.sleep(3)  # 每三秒执行一次
        requested_keywords = set()
        while not requested_keywords_queue.empty():
            requested_keywords.add(requested_keywords_queue.get())
        
        if requested_keywords:
            with open(requested_keywords_file, "a") as file:
                for keyword in requested_keywords:
                    file.write(f"{keyword}\n")
            print(f"已保存 {len(requested_keywords)} 个关键词到 {requested_keywords_file}")

def send_request(keyword):
    """发送单个请求的函数"""
    data = data_template.copy()  # 复制模板数据
    data["keyboard"] = keyword  # 替换关键字
    try:
        response = requests.post(url, data=data, headers=headers, allow_redirects=True)  # 允许重定向
        response.raise_for_status()  # 检查请求是否成功

        # 解析 searchid
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(response.url)
        query_params = parse_qs(parsed_url.query)
        searchid = query_params.get("searchid", ["N/A"])[0]  # 获取 searchid 参数

        # 只显示 keyword 和 searchid
        print(f"关键字: {keyword}, searchid: {searchid}")
    except requests.RequestException as e:
        print(f"请求失败 - 关键字: {keyword}, 错误: {e}")
    finally:
        requested_keywords_queue.put(keyword)  # 将已请求的关键词放入队列

def main():
    """主函数，使用多线程发送请求"""
    max_threads = 1024  # 最大线程数（可根据需要调整）
    all_keywords = generate_keywords()  # 生成关键词列表
    requested_keywords = read_requested_keywords()  # 读取已请求的关键词
    keywords_to_request = [kw for kw in all_keywords if kw not in requested_keywords]  # 需要请求的关键词

    print(f"开始发送请求，关键字总数: {len(keywords_to_request)}，线程数: {max_threads}")
    
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        executor.map(send_request, keywords_to_request)  # 并发执行请求
    end_time = time.time()
    
    print(f"所有请求完成，耗时: {end_time - start_time:.2f}秒")

if __name__ == "__main__":
    # 启动保存关键词的线程
    save_thread = threading.Thread(target=save_requested_keywords, daemon=True)
    save_thread.start()

    main()
