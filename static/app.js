document.addEventListener("DOMContentLoaded", () => {
    // Setup Filter Toggle
    const filterBtn = document.getElementById("toggle-filter-btn");
    const filterDrawer = document.getElementById("filter-drawer");
    filterBtn.addEventListener("click", () => {
        filterDrawer.classList.toggle("hidden");
    });

    // Setup Bottom Nav Tabs
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetTab = item.getAttribute("data-tab");
            switchTab(targetTab);
        });
    });

    // Run initial search
    handleSearch();
});

function switchTab(tabId) {
    document.querySelectorAll(".nav-item").forEach(el => {
        el.classList.toggle("active", el.getAttribute("data-tab") === tabId);
    });
    document.querySelectorAll(".tab-content").forEach(el => {
        el.classList.toggle("active", el.id === tabId);
        el.classList.toggle("hidden", el.id !== tabId);
    });

    if (tabId === "tab-history") {
        loadHistory();
    }
}

async function handleSearch() {
    const query = document.getElementById("search-input").value.trim();
    if (!query) {
        showToast("검색어를 입력해 주세요!");
        return;
    }

    const paperSort = document.getElementById("paper-sort").value;
    const newsPeriod = document.getElementById("news-period").value;
    const youtubeSort = document.getElementById("youtube-sort").value;
    const autoTranslate = document.getElementById("auto-translate").checked;

    // Show loading
    document.getElementById("loading-state").classList.remove("hidden");
    
    // Clear list content while loading
    document.getElementById("papers-list").innerHTML = "";
    document.getElementById("news-list").innerHTML = "";
    document.getElementById("youtube-list").innerHTML = "";

    try {
        const url = `/api/search?q=${encodeURIComponent(query)}&paper_sort=${encodeURIComponent(paperSort)}&news_period=${encodeURIComponent(newsPeriod)}&youtube_sort=${encodeURIComponent(youtubeSort)}&auto_translate=${autoTranslate}`;
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error("서버 응답 오류");
        }
        const data = await response.json();

        renderPapers(data.papers || []);
        renderNews(data.news || []);
        renderYouTube(data.youtube || []);

        // Update badges
        updateBadge("badge-papers", (data.papers || []).length);
        updateBadge("badge-news", (data.news || []).length);
        updateBadge("badge-youtube", (data.youtube || []).length);

    } catch (err) {
        showToast("검색 중 오류가 발생했습니다: " + err.message);
    } finally {
        document.getElementById("loading-state").classList.add("hidden");
    }
}

function updateBadge(id, count) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = count;
        if (count > 0) {
            el.classList.add("show");
        } else {
            el.classList.remove("show");
        }
    }
}

function renderPapers(papers) {
    const container = document.getElementById("papers-list");
    if (!papers || papers.length === 0) {
        container.innerHTML = `<div class="empty-state"><span class="empty-icon">📄</span><p>검색된 논문이 없습니다.</p></div>`;
        return;
    }

    let html = "";
    papers.forEach(p => {
        let htmlBtn = "";
        if (p.html_link) {
            htmlBtn = `<a href="${p.html_link}" target="_blank" class="btn-link btn-web">🌐 웹 번역보기 ↗</a>`;
        }
        html += `
        <div class="card">
            <div class="card-title">${escapeHtml(p.title)}</div>
            <div class="card-meta">👤 ${escapeHtml(p.authors)} | 📅 ${p.year}</div>
            <div class="card-abstract">${escapeHtml(p.abstract)}</div>
            <div class="card-actions">
                <a href="${p.link}" target="_blank" class="btn-link">📄 PDF 원문보기</a>
                ${htmlBtn}
                <button class="btn-save" onclick='saveItem("논문", ${JSON.stringify(p.title)}, ${JSON.stringify(p.link)}, ${JSON.stringify(p.authors)})'>💾 저장</button>
            </div>
        </div>`;
    });
    container.innerHTML = html;
}

function renderNews(news) {
    const container = document.getElementById("news-list");
    if (!news || news.length === 0) {
        container.innerHTML = `<div class="empty-state"><span class="empty-icon">📰</span><p>검색된 뉴스가 없습니다.</p></div>`;
        return;
    }

    let html = "";
    news.forEach(n => {
        html += `
        <div class="card">
            <div class="card-title">${escapeHtml(n.title)}</div>
            <div class="card-meta">🏢 ${escapeHtml(n.source)} | 📅 ${escapeHtml(n.date)}</div>
            <div class="card-abstract">${escapeHtml(n.summary)}</div>
            <div class="card-actions">
                <a href="${n.link}" target="_blank" class="btn-link">📰 기사 읽기 ↗</a>
                <button class="btn-save" onclick='saveItem("뉴스", ${JSON.stringify(n.title)}, ${JSON.stringify(n.link)}, ${JSON.stringify(n.source)})'>💾 저장</button>
            </div>
        </div>`;
    });
    container.innerHTML = html;
}

function renderYouTube(videos) {
    const container = document.getElementById("youtube-list");
    if (!videos || videos.length === 0) {
        container.innerHTML = `<div class="empty-state"><span class="empty-icon">🎥</span><p>검색된 영상이 없습니다.</p></div>`;
        return;
    }

    let html = "";
    videos.forEach(v => {
        html += `
        <div class="yt-card">
            <img src="${v.thumbnail}" class="yt-thumb" alt="thumbnail">
            <div class="yt-body">
                <div class="yt-title">${escapeHtml(v.title)}</div>
                <div class="yt-meta">📺 ${escapeHtml(v.channel)} | 👁️ ${escapeHtml(v.views)}</div>
                <div class="card-actions">
                    <a href="${v.link}" target="_blank" class="btn-link">Watch ▶</a>
                    <button class="btn-save" onclick='saveItem("유튜브", ${JSON.stringify(v.title)}, ${JSON.stringify(v.link)}, ${JSON.stringify(v.channel)})'>💾 저장</button>
                </div>
            </div>
        </div>`;
    });
    container.innerHTML = html;
}

async function saveItem(type, title, link, meta) {
    try {
        const response = await fetch("/api/history", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ type, title, link, meta })
        });
        const res = await response.json();
        if (res.success) {
            showToast("✅ 기록에 저장되었습니다!");
        } else {
            showToast("ℹ️ 이미 저장된 자료입니다.");
        }
    } catch (err) {
        showToast("저장 실패: " + err.message);
    }
}

async function loadHistory() {
    const container = document.getElementById("history-container");
    container.innerHTML = `<div class="loading-state"><div class="spinner"></div></div>`;

    try {
        const response = await fetch("/api/history");
        const data = await response.json();
        const history = data.history;

        if (!history || Object.keys(history).length === 0) {
            container.innerHTML = `<div class="empty-state"><span class="empty-icon">📅</span><p>아직 저장된 자료가 없습니다.</p></div>`;
            return;
        }

        let html = "";
        for (const [dateKey, items] of Object.entries(history)) {
            html += `<div class="history-group"><div class="history-date">📆 ${dateKey}</div>`;
            items.forEach(item => {
                const icon = item.type === "논문" ? "📄" : item.type === "뉴스" ? "📰" : "🎥";
                html += `
                <div class="history-item">
                    <div class="history-title">
                        ${icon} [${item.type}] <a href="${item.link}" target="_blank">${escapeHtml(item.title)}</a>
                    </div>
                    <div class="history-meta">정보: ${escapeHtml(item.meta)} | 저장: ${item.date}</div>
                </div>`;
            });
            html += `</div>`;
        }
        container.innerHTML = html;
    } catch (err) {
        container.innerHTML = `<div class="empty-state"><p>기록을 불러오지 못했습니다.</p></div>`;
    }
}

function showToast(msg) {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 2500);
}

function escapeHtml(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
