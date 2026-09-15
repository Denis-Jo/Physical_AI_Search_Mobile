import requests
import re
import json
from deep_translator import GoogleTranslator

def search_youtube(query, max_results=10, sort_by="관련성순", auto_translate=False):
    try:
        url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"
        if sort_by == "최신순":
            url += "&sp=CAI%253D"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        match = re.search(r'var ytInitialData = ({.*?});</script>', response.text)
        if not match:
            return []
            
        data = json.loads(match.group(1))
        contents = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
        
        translator = GoogleTranslator(source='auto', target='ko') if auto_translate else None
        
        results = []
        for item in contents:
            if 'videoRenderer' in item:
                video = item['videoRenderer']
                
                video_id = video.get('videoId', '')
                title = video.get('title', {}).get('runs', [{}])[0].get('text', '')
                
                thumbnails = video.get('thumbnail', {}).get('thumbnails', [])
                thumbnail_url = thumbnails[-1]['url'] if thumbnails else ""
                
                channel = video.get('ownerText', {}).get('runs', [{}])[0].get('text', 'Unknown')
                views = video.get('viewCountText', {}).get('simpleText', 'N/A')
                
                if auto_translate and title:
                    try:
                        title = translator.translate(title)
                    except Exception:
                        pass
                
                if video_id and title:
                    results.append({
                        "title": title,
                        "channel": channel,
                        "views": views,
                        "thumbnail": thumbnail_url,
                        "link": f"https://www.youtube.com/watch?v={video_id}"
                    })
                    
            if len(results) >= max_results:
                break
                
        return results
    except Exception as e:
        print(f"Error fetching youtube videos: {e}")
        return []
