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
existing_links = set() # 用来记录已经存过的“指纹”

# 检查是否存在历史数据文件
if os.path.exists('data.json'):
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            timeline = json.load(f)
        # 提取所有已存在的链接，用作“指纹”防伪验证
        existing_links = {item.get('link', '') for item in timeline if 'link' in item}
        print(f"📦 成功读取历史档案，当前已累计 {len(timeline)} 条记录。")
    except Exception as e:
        print(f"⚠️ 读取历史数据失败，将创建新档案: {e}")

new_items_count = 0  # 记录这次新增了多少条

# ==========================================
# 1. 🎬 MDbList 电影专属抓取模块 (API 模式)
# ==========================================
print("🎬 正在同步 MDbList 电影数据...")
try:
    mdb_url = "https://mdblist.com/lists/carver.song/external/125740"
    # MDbList 极客小技巧：在普通网页链接末尾加上 /json 就能直接调出干净的 API 数据
    api_url = mdb_url if mdb_url.endswith('json') else mdb_url + "/json"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(api_url, headers=headers)
    
    if res.status_code == 200:
        movies = res.json()
        # 遍历列表里最新添加的 5 部电影
        for movie in movies[:5]:
            imdb_id = movie.get('imdb_id', '')
            # 如果有 IMDb ID，就拼装出真实的 IMDb 网页链接
            item_link = f"https://www.imdb.com/title/{imdb_id}/" if imdb_id else mdb_url
            
            # 🔮 去重核心：如果这部电影已经在档案里了，就跳过！
            if item_link not in existing_links:
                timeline.append({
                    "category": "🎬 电影",
                    "title": movie.get('title', '未知电影'),
                    "link": item_link,
                    # MDbList 接口通常不带收藏时间，我们用抓取的当前时间作为时间戳
                    "time": datetime.datetime.now().isoformat(),
                    "note": f"上映年份: {movie.get('year', '未知')} | 评分: {movie.get('score', '暂无')}"
                })
                existing_links.add(item_link)
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
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            raw_summary = entry.get('summary', '')
            item_link = entry.link 
            
            # 足迹提取真实地图链接逻辑
            if category == "📍 足迹":
                urls = re.findall(r'(https?://[^\s<"\'>]+)', raw_summary)
                for u in urls:
                    if 'blogspot.com' not in u and 'blogger.com' not in u:
                        item_link = u 
                        break
            
            # 🔮 去重核心：重复的文章或音乐，一律拦截跳过
            if item_link in existing_links:
                continue

            note_text = re.sub(r'<[^>]+>', ' ', raw_summary) 
            note_text = re.sub(r'https?://[^\s]+', '', note_text).strip()
            
            timeline.append({
                "category": category,
                "title": entry.title,
                "link": item_link, 
                "time": entry.get('published', datetime.datetime.now().isoformat()),
                "note": note_text
            })
            existing_links.add(item_link)
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
            
            # 🔮 去重核心：这条跑步记录存过了吗？
            if act_link in existing_links:
                continue

            distance_km = act['distance'] / 1000
            moving_time_mins = act['moving_time'] // 60
            sport_type = "🏃‍♂️ 跑步" if act['sport_type'] == 'Run' else ("🚴‍♂️ 骑行" if act['sport_type'] == 'Ride' else "⛰️ 徒步/健走")
            
            timeline.append({
                "category": sport_type,
                "title": act['name'],
                "link": act_link,
                "time": act['start_date'],
                "note": f"距离: {distance_km:.2f} km | 耗时: {moving_time_mins} 分钟"
            })
            existing_links.add(act_link)
            new_items_count += 1
        print("✅ Strava 运动数据同步完成！")
    except Exception as e:
        print(f"❌ 抓取 Strava 失败: {e}")
else:
    print("⚠️ 未找到 Strava 密钥，已跳过运动抓取。")

# ==========================================
# 4. 全局排序并保存档案 (滚雪球机制)
# ==========================================
# 不管是旧档案还是刚抓的新动态，统统按时间重新排队
timeline.sort(key=lambda x: x['time'], reverse=True)

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(timeline, f, ensure_ascii=False, indent=2)
    
print(f"🎉 档案更新完毕！本次共新增 {new_items_count} 条记录，个人数据库总计容量: {len(timeline)} 条。")
