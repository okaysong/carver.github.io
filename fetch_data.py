import feedparser
import json
import datetime

# 替换为你之前拼接好的真实 RSS 链接
FEEDS = {
    "🎬 电影": "https://rsshub.rssforever.com/imdb/list/ls001577067",
    "📚 阅读": "https://www.goodreads.com/review/list_rss/2055861?key=iyISFZZeSgNPyClqkXkYc75_ToCciDCuQjs4WB2on-6Va1U7&shelf=read",
    "🎵 音乐": "https://listenbrainz.org/syndication-feed/user/carver6/listens?minutes=480",
    "📍 足迹": "https://okay85.blogspot.com/feeds/posts/default?alt=rss"
}

timeline = []

for category, url in FEEDS.items():
    feed = feedparser.parse(url)
    # 每个平台抓取最近的 5 条动态
    for entry in feed.entries[:5]: 
        timeline.append({
            "category": category,
            "title": entry.title,
            "link": entry.link,
            # 如果没有时间戳，默认用当前时间
            "time": entry.get('published', datetime.datetime.now().isoformat()) 
        })
- name: 运行抓取脚本
        env: 
          # 之前的 Trello 密钥（如果你还在用的话）
          # TRELLO_KEY: ${{ secrets.TRELLO_KEY }}
          # TRELLO_TOKEN: ${{ secrets.TRELLO_TOKEN }}
          
          # 👇 新增：将 Strava 密钥传给 Python
          STRAVA_CLIENT_ID: ${{ secrets.STRAVA_CLIENT_ID }}
          STRAVA_CLIENT_SECRET: ${{ secrets.STRAVA_CLIENT_SECRET }}
          STRAVA_REFRESH_TOKEN: ${{ secrets.STRAVA_REFRESH_TOKEN }}
        run: python fetch_data.py
# 将抓取到的数据写入 data.json 文件
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(timeline, f, ensure_ascii=False, indent=2)
    
print("✅ 数据抓取完成，已更新 data.json")
