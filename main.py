import os
import uvicorn
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from modules.paper_search import search_papers
from modules.news_search import search_news
from modules.youtube_search import search_youtube
from modules.history_manager import save_to_history, get_history_by_date

app = FastAPI(title="Physical AI Search Mobile API")

# Enable CORS for local network testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SaveHistoryRequest(BaseModel):
    type: str
    title: str
    link: str
    meta: str

@app.get("/api/search")
def api_search(
    q: str = Query(..., description="Search query"),
    paper_sort: str = Query("연관성순"),
    news_period: str = Query("전체"),
    youtube_sort: str = Query("관련성순"),
    auto_translate: bool = Query(False)
):
    if not q.strip():
        raise HTTPException(status_code=400, detail="검색어를 입력해 주세요.")
        
    papers = search_papers(q, sort_by=paper_sort, auto_translate=auto_translate)
    news = search_news(q, time_range=news_period, auto_translate=auto_translate)
    youtube = search_youtube(q, sort_by=youtube_sort, auto_translate=auto_translate)
    
    return {
        "query": q,
        "papers": papers,
        "news": news,
        "youtube": youtube
    }

@app.get("/api/history")
def api_get_history():
    history_data = get_history_by_date()
    return {"history": history_data}

@app.post("/api/history")
def api_save_history(req: SaveHistoryRequest):
    success = save_to_history(req.type, req.title, req.link, req.meta)
    if success:
        return {"success": True, "message": "기록에 저장되었습니다."}
    else:
        return {"success": False, "message": "이미 저장된 자료입니다."}

# Mount static files for PWA Web App
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)


