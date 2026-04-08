import os
import feedparser
import json
import datetime
import requests

# ==========================================
# 1. 基础 RSS 抓取模块 (电影、阅读、音乐、足迹)
# ==========================================
FEEDS = {
    "🎬 电影": "https://rsshub.rssforever.com/imdb/list/ls001577067", # 如果报错可以考虑换成 Letterboxd
    "📚 阅读": "https://www.goodreads.com/review/list_rss/2055861?key=iyISFZZeSgNPyClqkXkYc75_ToCciDCuQjs4WB2on-6Va1U7&shelf=read",
    "🎵 音乐": "https://listenbrainz.org/syndication-feed/user/carver6/listens?minutes=480",
    "📍 足迹": "https://okay85.blogspot.com/feeds/posts/default?alt=rss"
}

timeline = []

for category, url in FEEDS.items():
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            # 兼容处理正文内容
            note_text = entry.get('summary', '').replace('<br>', '').replace('<br />', '').strip()
            
            timeline.append({
                "category": category,
                "title": entry.title,
                "link": entry.link,
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
        # 步骤 A：用 Refresh Token 换取最新的通行证 (Access Token)
        auth_url = "https://www.strava.com/oauth/token"
        payload = {
            'client_id': STRAVA_CLIENT_ID,
            'client_secret': STRAVA_CLIENT_SECRET,
            'refresh_token': STRAVA_REFRESH_TOKEN,
            'grant_type': 'refresh_token'
        }
        res = requests.post(auth_url, data=payload)
        access_token = res.json().get('access_token')

        # 步骤 B：用通行证去获取最近的 5 次运动记录
        activities_url = "https://www.strava.com/api/v3/athlete/activities?per_page=5"
        headers = {'Authorization': f'Bearer {access_token}'}
        act_res = requests.get(activities_url, headers=headers)
        activities = act_res.json()

        for act in activities:
            # 计算距离 (千米) 和时间 (分钟)
            distance_km = act['distance'] / 1000
            moving_time_mins = act['moving_time'] // 60
            
            # 判断运动类型，给个好看的 emoji
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
# 按照时间从新到旧排序
timeline.sort(key=lambda x: x['time'], reverse=True)

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(timeline, f, ensure_ascii=False, indent=2)
    
print("🎉 所有数据抓取完成，已更新 data.json！")
