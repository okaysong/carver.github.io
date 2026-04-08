import os
import feedparser
import json
import datetime
import requests
import re  # 👇 新增：引入正则表达式库，用来“提取”地图链接和清理内容

# ==========================================
# 1. 基础 RSS 抓取模块 (电影、阅读、音乐、足迹)
# ==========================================
FEEDS = {
    "🎬 电影": "https://rsshub.rssforever.com/imdb/list/ls001577067",
    "📚 阅读": "https://www.goodreads.com/review/list_rss/2055861?key=iyISFZZeSgNPyClqkXkYc75_ToCciDCuQjs4WB2on-6Va1U7&shelf=read",
    "🎵 音乐": "https://listenbrainz.org/syndication-feed/user/carver6/listens?minutes=480",
    "📍 足迹": "https://okay85.blogspot.com/feeds/posts/default?alt=rss"
}

timeline = []

for category, url in FEEDS.items():
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            raw_summary = entry.get('summary', '')
            item_link = entry.link # 默认的跳转链接（通常是该平台自己的网页）
            
            # 🎯 足迹专属魔法：拦截并提取真实的地图链接
            if category == "📍 足迹":
                # 使用正则扫描正文里所有的网址 (http/https开头)
                urls = re.findall(r'(https?://[^\s<"\'>]+)', raw_summary)
                for u in urls:
                    # 只要不是 Blogger 自身的内部链接，就认为它是地图链接！
                    if 'blogspot.com' not in u and 'blogger.com' not in u:
                        item_link = u # 偷天换日：用地图链接替换原来的博客链接
                        break
            
            # 🧹 视觉清理魔法：
            # 1. 删掉乱七八糟的 HTML 标签
            note_text = re.sub(r'<[^>]+>', ' ', raw_summary) 
            # 2. 既然标题已经能跳转地图了，就把正文里那串长长的网址抹掉，只保留你的“文字碎碎念”
            note_text = re.sub(r'https?://[^\s]+', '', note_text).strip()
            
            timeline.append({
                "category": category,
                "title": entry.title,
                "link": item_link,  # 👈 现在这里已经是真实的地图链接了！
                "time": entry.get('published', datetime.datetime.now().isoformat()),
                "note": note_text
            })
        print(f"✅ 成功抓取: {category}")
    except Exception as e:
        print(f"❌ 抓取 {category} 失败，已跳过: {e}")

# ==========================================
# 2. Strava 高级 API 抓取模块
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
            distance_km = act['distance'] / 1000
            moving_time_mins = act['moving_time'] // 60
            sport_type = "🏃‍♂️ 跑步" if act['sport_type'] == 'Run' else ("🚴‍♂️ 骑行" if act['sport_type'] == 'Ride' else "⛰️ 徒步/健走")
            
            timeline.append({
                "category": sport_type,
                "title": act['name'],
                "link": f"https://www.strava.com/activities/{act['id']}",
                "time": act['start_date'],
                "note": f"距离: {distance_km:.2f} km | 耗时: {moving_time_mins} 分钟"
            })
        print("✅ Strava 运动数据抓取完成！")
    except Exception as e:
        print(f"❌ 抓取 Strava 失败: {e}")
else:
    print("⚠️ 未找到 Strava 密钥，已跳过运动抓取。")

# ==========================================
# 3. 排序并保存数据
# ==========================================
timeline.sort(key=lambda x: x['time'], reverse=True)

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(timeline, f, ensure_ascii=False, indent=2)
    
print("🎉 所有数据抓取完成，已更新 data.json！")
