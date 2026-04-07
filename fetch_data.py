import feedparser
import json
import datetime

# 替换为你之前拼接好的真实 RSS 链接
FEEDS = {
    "🎬 电影": "https://rsshub.app/imdb/user/你的ID/ratings",
    "📚 阅读": "https://www.goodreads.com/review/list_rss/你的ID?shelf=read",
    "🎵 音乐": "https://ws.audioscrobbler.com/2.0/user/你的ID/recenttracks.rss",
    "📍 足迹": "https://feeds.foursquare.com/history/你的ID.rss?signature=你的密钥"
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
