import feedparser
import urllib.parse
from deep_translator import GoogleTranslator

def search_news(query, max_results=10, time_range="전체", auto_translate=False):
    try:
        encoded_query = urllib.parse.quote(query)
        time_param = ""
        if time_range == "최근 1주일":
            time_param = "+when:7d"
        elif time_range == "최근 1개월":
            time_param = "+when:1m"
        elif time_range == "최근 1년":
            time_param = "+when:1y"
            
        url = f"https://news.google.com/rss/search?q={encoded_query}{time_param}&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(url)
        
        translator = GoogleTranslator(source='auto', target='ko') if auto_translate else None
        
        results = []
        for entry in feed.entries[:max_results]:
            title_parts = entry.title.rsplit(" - ", 1)
            title = title_parts[0]
            source = title_parts[1] if len(title_parts) > 1 else "Google News"
            
            date_str = entry.published if hasattr(entry, 'published') else ""
            if date_str:
                parts = date_str.split(" ")
                if len(parts) >= 4:
                    date_str = f"{parts[3]}-{parts[2]}-{parts[1]}"
            
            summary = "기사 원문을 통해 상세한 내용을 확인해 보세요."
            
            if auto_translate:
                try:
                    title = translator.translate(title)
                except Exception:
                    pass
            
            results.append({
                "title": title,
                "source": source,
                "date": date_str,
                "summary": summary,
                "link": entry.link
            })
        return results
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []
