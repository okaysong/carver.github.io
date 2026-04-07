import feedparser
import json
import datetime

# 替换为你之前拼接好的真实 RSS 链接
FEEDS = {
    "🎬 电影": "https://rsshub.app/imdb/list/ls001577067",
    "📚 阅读": "https://www.goodreads.com/review/list_rss/2055861?key=iyISFZZeSgNPyClqkXkYc75_ToCciDCuQjs4WB2on-6Va1U7&shelf=read",
    "🎵 音乐": "https://ws.audioscrobbler.com/2.0/user/carver6/recenttracks.rss",
    "📍 足迹": "https://feeds.foursquare.com/history/369346.rss?signature=rss_16-5805c5050fd378b4845672834f4d4dbc"
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

# 将抓取到的数据写入 data.json 文件
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(timeline, f, ensure_ascii=False, indent=2)
    
print("✅ 数据抓取完成，已更新 data.json")
