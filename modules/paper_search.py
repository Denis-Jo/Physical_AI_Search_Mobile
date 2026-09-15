import arxiv
import re
import requests
import concurrent.futures
from deep_translator import GoogleTranslator

def check_html_availability(short_id):
    url = f"https://arxiv.org/html/{short_id}"
    try:
        if requests.head(url, timeout=2).status_code == 200:
            return url
    except Exception:
        pass
    return None

def search_openalex_papers(query, max_results=10, auto_translate=False):
    """Fallback paper search using OpenAlex API when ArXiv is slow or unavailable."""
    try:
        url = f"https://api.openalex.org/works?search={requests.utils.quote(query)}&per-page={max_results}"
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return []
            
        data = resp.json()
        results = []
        translator = GoogleTranslator(source='auto', target='ko') if auto_translate else None
        
        for item in data.get("results", []):
            title = item.get("title") or "Untitled Paper"
            
            # Extract authors
            authorships = item.get("authorships", [])
            author_names = [a.get("author", {}).get("display_name", "") for a in authorships if a.get("author", {}).get("display_name")]
            authors = ", ".join(author_names[:3]) if author_names else "Unknown Authors"
            if len(author_names) > 3:
                authors += " et al."
                
            year = item.get("publication_year") or "N/A"
            
            # Reconstruct abstract from inverted index if available
            abstract_idx = item.get("abstract_inverted_index")
            abstract = ""
            if abstract_idx:
                try:
                    word_pos = sorted([(pos, word) for word, positions in abstract_idx.items() for pos in positions])
                    full_abstract = " ".join([w[1] for w in word_pos])
                    abstract = full_abstract[:300] + ("..." if len(full_abstract) > 300 else "")
                except Exception:
                    abstract = "요약 정보를 불러올 수 없습니다."
            else:
                abstract = "요약 정보가 제공되지 않는 논문입니다."
                
            # Links
            oa_info = item.get("open_access", {})
            link = oa_info.get("oa_url") or item.get("doi") or item.get("id") or "https://openalex.org"
            
            if auto_translate:
                try:
                    title = translator.translate(title)
                    if abstract and abstract != "요약 정보가 제공되지 않는 논문입니다.":
                        abstract = translator.translate(abstract)
                except Exception:
                    pass
                    
            results.append({
                "title": title,
                "authors": authors,
                "year": year,
                "abstract": abstract,
                "link": link
            })
        return results
    except Exception as e:
        print(f"Error fetching OpenAlex papers: {e}")
        return []

def fetch_arxiv_papers(translated_query, max_results, sort_criterion):
    client = arxiv.Client(page_size=max_results, delay_seconds=0.5, num_retries=1)
    search = arxiv.Search(
        query=translated_query,
        max_results=max_results,
        sort_by=sort_criterion
    )
    return list(client.results(search))

def search_papers(query, max_results=10, sort_by="연관성순", auto_translate=False):
    translated_query = query
    if re.search(r'[가-힣]', query):
        try:
            translated_query = GoogleTranslator(source='ko', target='en').translate(query)
            print(f"Translated query for paper search: {translated_query}")
        except Exception as e:
            print(f"Translation failed, using original query: {e}")
            translated_query = query

    # Try ArXiv search with a strict 3-second timeout
    arxiv_results = []
    sort_criterion = arxiv.SortCriterion.Relevance
    if sort_by == "최신순":
        sort_criterion = arxiv.SortCriterion.SubmittedDate

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(fetch_arxiv_papers, translated_query, max_results, sort_criterion)
        papers_list = future.result(timeout=3.0)
        
        if papers_list:
            translator = GoogleTranslator(source='auto', target='ko') if auto_translate else None
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as html_executor:
                html_links = list(html_executor.map(lambda p: check_html_availability(p.get_short_id()), papers_list))
            
            for i, r in enumerate(papers_list):
                authors = ", ".join([a.name for a in r.authors])
                title = r.title
                abstract = r.summary[:300] + ("..." if len(r.summary) > 300 else "")
                
                if auto_translate:
                    try:
                        title = translator.translate(title)
                        abstract = translator.translate(abstract)
                    except Exception:
                        pass
                
                paper_data = {
                    "title": title,
                    "authors": authors,
                    "year": r.published.year,
                    "abstract": abstract,
                    "link": r.pdf_url
                }
                
                if html_links[i]:
                    paper_data["html_link"] = html_links[i]
                    
                arxiv_results.append(paper_data)
    except Exception as e:
        print(f"ArXiv search encountered error/timeout (falling back to OpenAlex): {e}")
    finally:
        executor.shutdown(wait=False)

    if arxiv_results:
        return arxiv_results

    # Fallback to OpenAlex API if ArXiv search yielded no results or timed out
    print("Falling back to OpenAlex paper search...")
    return search_openalex_papers(translated_query, max_results=max_results, auto_translate=auto_translate)
