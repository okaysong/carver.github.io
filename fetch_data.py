import os
import feedparser
import json
import datetime
import requests
import re

# ==========================================
# 0. 核心升级：读取历史档案，建立去重数据库
# ==========================================
timeline = []
existing_fingerprints = set() # 🌟 升级：用“分类+标题+链接”做超级指纹

if os.path.exists('data.json'):
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            timeline = json.load(f)
        for item in timeline:
            # 提取已有的超级指纹防重
            fp = f"{item.get('category', '')}_{item.get('title', '')}_{item.get('link', '')}"
            existing_fingerprints.add(fp)
        print(f"📦 成功读取历史档案，当前已累计 {len(timeline)} 条记录。")
    except Exception as e:
        print(f"⚠️ 读取历史数据失败: {e}")

new_items_count = 0

# ==========================================
# 1. 🎬 MDbList 电影专属抓取模块 (API 模式)
# ==========================================
print("🎬 正在同步 MDbList 电影数据...")
try:
    mdb_url = "https://mdblist.com/lists/carver.song/external/125740"
    api_url = mdb_url if mdb_url.endswith('json') else mdb_url + "/json"
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(api_url, headers=headers)
    
    if res.status_code == 200:
        movies = res.json()
        for movie in movies[:50]:
            imdb_id = movie.get('imdb_id', '')
            item_link = f"https://www.imdb.com/title/{imdb_id}/" if imdb_id else mdb_url
            title = movie.get('title', '未知电影')
            
            fp = f"🎬 电影_{title}_{item_link}"
            if fp not in existing_fingerprints:
                timeline.append({
                    "category": "🎬 电影",
                    "title": title,
                    "link": item_link,
                    # 👇 强制使用 UTC 时间并加上 Z 尾缀
                    "time": datetime.datetime.utcnow().isoformat() + "Z",
                    "note": f"上映年份: {movie.get('year', '未知')} | 评分: {movie.get('score', '暂无')}"
                })
                existing_fingerprints.add(fp)
                new_items_count += 1
        print("✅ 成功抓取: MDbList 电影")
    else:
        print(f"❌ MDbList 接口拒绝访问，状态码: {res.status_code}")
except Exception as e:
    print(f"❌ 抓取 MDbList 失败: {e}")

# ==========================================
# 2. 基础 RSS 抓取模块 (阅读、音乐、足迹)
# ==========================================
RSS_FEEDS = {
    "📚 阅读": "https://www.goodreads.com/review/list_rss/2055861?key=iyISFZZeSgNPyClqkXkYc75_ToCciDCuQjs4WB2on-6Va1U7&shelf=read",
    "🎵 音乐": "https://listenbrainz.org/syndication-feed/user/carver6/listens?minutes=480",
    "📍 足迹": "https://okay85.blogspot.com/feeds/posts/default?alt=rss"
}

for category, url in RSS_FEEDS.items():
    try:
        # 🚀 突破反爬虫限制
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        res = requests.get(url, headers=headers, timeout=15)
        
        feed = feedparser.parse(res.content)
        
        for entry in feed.entries[:50]:
            raw_summary = entry.get('summary', '')
            item_link = entry.link 
            title = entry.title
            
            if category == "📍 足迹":
                urls = re.findall(r'(https?://[^\s<"\'>]+)', raw_summary)
                for u in urls:
                    if 'blogspot.com' not in u and 'blogger.com' not in u:
                        item_link = u 
                        break
            
            # 🔮 生成超级指纹防重
            fp = f"{category}_{title}_{item_link}"
            if fp in existing_fingerprints:
                continue

            note_text = re.sub(r'<[^>]+>', ' ', raw_summary) 
            note_text = re.sub(r'https?://[^\s]+', '', note_text).strip()
            
            # 👇 时间翻译魔法：强制转为标准 UTC 格式并带上 Z
            parsed_time = entry.get('published_parsed') or entry.get('updated_parsed')
            if parsed_time:
                final_time = datetime.datetime(*parsed_time[:6]).isoformat() + "Z"
            else:
                final_time = datetime.datetime.utcnow().isoformat() + "Z"
            
            timeline.append({
                "category": category,
                "title": title,
                "link": item_link, 
                "time": final_time,
                "note": note_text
            })
            existing_fingerprints.add(fp)
            new_items_count += 1
            
        print(f"✅ 成功抓取: {category}")
    except Exception as e:
        print(f"❌ 抓取 {category} 失败，已跳过: {e}")

# ==========================================
# 3. Strava 高级 API 抓取模块
# ==========================================
STRAVA_CLIENT_ID = os.environ.get('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.environ.get('STRAVA_CLIENT_SECRET')
STRAVA_REFRESH_TOKEN = os.environ.get('STRAVA_REFRESH_TOKEN')

if STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET and STRAVA_REFRESH_TOKEN:
    try:
        print("🏃‍♂️ 正在连接 Strava...")
        auth_url = "https://www.strava.com/oauth/token"
        payload = {
            'client_id': STRAVA_CLIENT_ID,
            'client_secret': STRAVA_CLIENT_SECRET,
            'refresh_token': STRAVA_REFRESH_TOKEN,
            'grant_type': 'refresh_token'
        }
        res = requests.post(auth_url, data=payload)
        access_token = res.json().get('access_token')

        activities_url = "https://www.strava.com/api/v3/athlete/activities?per_page=5"
        headers = {'Authorization': f'Bearer {access_token}'}
        act_res = requests.get(activities_url, headers=headers)
        activities = act_res.json()

        for act in activities:
            act_link = f"https://www.strava.com/activities/{act['id']}"
            title = act['name']
            sport_type = "🏃‍♂️ 跑步" if act['sport_type'] == 'Run' else ("🚴‍♂️ 骑行" if act['sport_type'] == 'Ride' else "⛰️ 徒步/健走")
            
            fp = f"{sport_type}_{title}_{act_link}"
            if fp in existing_fingerprints:
                continue

            distance_km = act['distance'] / 1000
            moving_time_mins = act['moving_time'] // 60
            
            timeline.append({
                "category": sport_type,
                "title": title,
                "link": act_link,
                "time": act['start_date'], # Strava 官方 API 已经自带 Z 了，无需修改
                "note": f"距离: {distance_km:.2f} km | 耗时: {moving_time_mins} 分钟"
            })
            existing_fingerprints.add(fp)
            new_items_count += 1
        print("✅ Strava 运动数据同步完成！")
    except Exception as e:
        print(f"❌ 抓取 Strava 失败: {e}")
else:
    print("⚠️ 未找到 Strava 密钥，已跳过运动抓取。")

# ==========================================
# 4. 全局排序并保存档案
# ==========================================
timeline.sort(key=lambda x: x['time'], reverse=True)

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(timeline, f, ensure_ascii=False, indent=2)
    
print(f"🎉 档案更新完毕！本次共新增 {new_items_count} 条记录。")
