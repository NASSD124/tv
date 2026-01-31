from flask import Flask, request, jsonify
import json
import urllib.parse
import requests
import time
import random
import re

app = Flask(__name__)

class NetflixGCSpider:
    def __init__(self):
        self.base_url = "https://www.netflixgc.com"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/121.0"
        ]
        self.headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        self.session = requests.Session()
    
    def get_page(self, url, retries=3):
        """获取页面内容"""
        for i in range(retries):
            # 随机更换 User-Agent
            self.headers["User-Agent"] = random.choice(self.user_agents)
            
            try:
                # 发送请求
                response = self.session.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                
                # 随机延迟，模拟人类行为
                time.sleep(random.uniform(0.5, 1.0))
                
                return response.text
            except Exception:
                # 等待后重试
                time.sleep(random.uniform(1.0, 1.5))
                continue
        
        return None
    
    def parse_homepage(self):
        """解析首页分类"""
        # 直接返回默认分类，减少网络请求
        default_categories = [
            {"name": "电影", "url": "https://www.netflixgc.com/vodshow/1-----------.html"},
            {"name": "连续剧", "url": "https://www.netflixgc.com/vodshow/2-----------.html"},
            {"name": "纪录片", "url": "https://www.netflixgc.com/vodshow/24-----------.html"},
            {"name": "漫剧", "url": "https://www.netflixgc.com/vodshow/3-----------.html"},
            {"name": "综艺", "url": "https://www.netflixgc.com/vodshow/23-----------.html"},
            {"name": "伦理", "url": "https://www.netflixgc.com/vodshow/30-----------.html"}
        ]
        return default_categories
    
    def parse_category(self, html):
        """解析分类页面"""
        if not html:
            return []
        
        items = []
        try:
            # 尝试从 maccms 系统的 AJAX 接口获取数据
            aid_match = re.search(r'aid":"(\d+)"', html)
            aid = aid_match.group(1) if aid_match else "12"
            
            # 构建 AJAX 请求 URL
            ajax_url = f"{self.base_url}/index.php/ajax/data.html?mid=1&aid={aid}&pg=1&t=json"
            ajax_html = self.get_page(ajax_url)
            
            if ajax_html:
                # 尝试解析 JSON
                try:
                    # 提取 JSON 部分
                    json_start = ajax_html.find('{')
                    json_end = ajax_html.rfind('}') + 1
                    if json_start != -1 and json_end != -1:
                        json_str = ajax_html[json_start:json_end]
                        data = json.loads(json_str)
                        
                        # 提取内容
                        if "list" in data:
                            for item in data["list"]:
                                vod_id = str(item.get("vod_id", ""))
                                vod_name = item.get("vod_name", "")
                                vod_pic = item.get("vod_pic", "")
                                
                                if vod_id and vod_name:
                                    # 构建详情页 URL
                                    detail_url = f"{self.base_url}/vodshow/2-{vod_id}.html"
                                    
                                    item_info = {
                                        "id": vod_id,
                                        "title": vod_name,
                                        "url": detail_url,
                                        "img": vod_pic
                                    }
                                    items.append(item_info)
                except:
                    pass
            
            # 如果 AJAX 失败，尝试使用正则解析
            if not items:
                pattern = r'<a\s+href="(/vodshow/\d+-\d+[^"]+)"[^>]*><img\s+src="([^"]+)"[^>]*alt="([^"]+)"[^>]*></a>'
                matches = re.findall(pattern, html)
                
                for href, img, title in matches:
                    if href and title:
                        item_info = {
                            "id": href.split("-")[-1].split(".")[0],
                            "title": title.strip(),
                            "url": self.base_url + href,
                            "img": img.strip()
                        }
                        items.append(item_info)
            
            # 限制最多返回15个内容
            return items[:15]
        except:
            return []
    
    def parse_detail(self, html):
        """解析详情页"""
        if not html:
            return {}
        
        detail = {}
        try:
            # 尝试从 maccms 系统的 AJAX 接口获取数据
            aid_match = re.search(r'aid":"(\d+)"', html)
            aid = aid_match.group(1) if aid_match else "12"
            
            vod_id_match = re.search(r'vod_id":"(\d+)"', html)
            vod_id = vod_id_match.group(1) if vod_id_match else ""
            
            # 构建 AJAX 请求 URL
            ajax_url = f"{self.base_url}/index.php/ajax/data.html?mid=1&aid={aid}&pg=1&t=json"
            ajax_html = self.get_page(ajax_url)
            
            if ajax_html:
                # 尝试解析 JSON
                try:
                    # 提取 JSON 部分
                    json_start = ajax_html.find('{')
                    json_end = ajax_html.rfind('}') + 1
                    if json_start != -1 and json_end != -1:
                        json_str = ajax_html[json_start:json_end]
                        data = json.loads(json_str)
                        
                        # 提取内容
                        if "list" in data:
                            for item in data["list"]:
                                if str(item.get("vod_id")) == vod_id:
                                    detail["title"] = item.get("vod_name", "")
                                    detail["description"] = item.get("vod_content", "")
                                    detail["img"] = item.get("vod_pic", "")
                                    break
                except:
                    pass
            
            # 如果 AJAX 失败，尝试使用正则解析
            if not detail.get("title"):
                # 提取标题
                title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
                if title_match:
                    detail["title"] = title_match.group(1).strip()
                
                # 提取描述
                desc_match = re.search(r'<div\s+class="vod-content"[^>]*>([\s\S]*?)</div>', html)
                if desc_match:
                    detail["description"] = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()
                
                # 提取图片
                img_match = re.search(r'<img\s+src="([^"]+)"[^>]*alt="[^"]+"[^>]*>', html)
                if img_match:
                    detail["img"] = img_match.group(1).strip()
            
            # 生成播放链接
            if detail.get("title"):
                play_links = []
                # 模拟生成播放链接
                for i in range(1, 6):
                    link = {
                        "name": f"播放源 {i}",
                        "url": f"{self.base_url}/play/{vod_id}-1-{i}.html"
                    }
                    play_links.append(link)
                detail["play_links"] = play_links
        except:
            pass
        
        return detail

@app.route('/api', methods=['GET'])
def api_handler():
    # 解析请求参数
    action = request.args.get('action', 'home')
    
    # 初始化爬虫
    spider = NetflixGCSpider()
    
    # 处理请求
    try:
        if action == "home":
            # 获取首页分类
            categories = spider.parse_homepage()
            response = {
                "code": 200,
                "msg": "success",
                "data": {
                    "categories": categories
                }
            }
        elif action == "category":
            # 获取分类内容
            category_url = request.args.get('url', '')
            if category_url:
                html = spider.get_page(category_url)
                items = spider.parse_category(html)
                response = {
                    "code": 200,
                    "msg": "success",
                    "data": {
                        "items": items
                    }
                }
            else:
                response = {
                    "code": 400,
                    "msg": "缺少 url 参数",
                    "data": {}
                }
        elif action == "detail":
            # 获取详情页
            detail_url = request.args.get('url', '')
            if detail_url:
                html = spider.get_page(detail_url)
                detail = spider.parse_detail(html)
                response = {
                    "code": 200,
                    "msg": "success",
                    "data": detail
                }
            else:
                response = {
                    "code": 400,
                    "msg": "缺少 url 参数",
                    "data": {}
                }
        elif action == "search":
            # 搜索内容
            keyword = request.args.get('keyword', '')
            if keyword:
                search_url = f"https://www.netflixgc.com/search/{urllib.parse.quote(keyword)}"
                html = spider.get_page(search_url)
                items = spider.parse_category(html)  # 复用分类解析逻辑
                response = {
                    "code": 200,
                    "msg": "success",
                    "data": {
                        "items": items
                    }
                }
            else:
                response = {
                    "code": 400,
                    "msg": "缺少 keyword 参数",
                    "data": {}
                }
        else:
            # 未知 action
            response = {
                "code": 400,
                "msg": "未知的 action",
                "data": {}
            }
    except Exception as e:
        # 处理服务器内部错误
        response = {
            "code": 500,
            "msg": f"服务器内部错误: {str(e)}",
            "data": {}
        }
    
    # 返回响应
    return jsonify(response)

@app.route('/')
def home():
    return "TVBOX API Service is running!"

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)