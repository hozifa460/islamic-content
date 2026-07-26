import sys
import os
import time
import socket
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.extractive_engine import ExtractiveIslamicEngine

app = FastAPI(title="رفيق - المستشار الإسلامي")

print("[*] Pre-warming Extractive Islamic Engine on server boot...")
engine = ExtractiveIslamicEngine()

def get_engine():
    global engine
    if engine is None:
        engine = ExtractiveIslamicEngine()
    return engine

class QueryRequest(BaseModel):
    query: str

def find_free_port(starting_port=8080):
    for port in range(starting_port, starting_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            res = sock.connect_ex(('127.0.0.1', port))
            if res != 0:
                return port
    return starting_port

@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_content = r"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>رفيق - المستشار الإسلامي</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700&family=Amiri:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #212121;
            --bg-sidebar: #171717;
            --bg-chat: #212121;
            --bg-user-bubble: #2f2f2f;
            --accent-gold: #fbbf24;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --text-main: #ececf1;
            --text-sub: #b4b4b4;
            --border-color: #333333;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Cairo', sans-serif; background-color: var(--bg-dark); color: var(--text-main); height: 100vh; display: flex; overflow: hidden; font-size: 14px; }
        .sidebar { width: 250px; background-color: var(--bg-sidebar); border-left: 1px solid var(--border-color); display: flex; flex-direction: column; padding: 0.7rem; }
        .new-chat-btn { background: transparent; border: 1px solid var(--border-color); color: #fff; padding: 0.55rem 0.8rem; border-radius: 8px; font-family: 'Cairo', sans-serif; font-size: 0.85rem; font-weight: 600; display: flex; align-items: center; gap: 8px; cursor: pointer; width: 100%; transition: background 0.2s; }
        .new-chat-btn:hover { background: #2a2b32; }
        .sidebar-footer { margin-top: auto; border-top: 1px solid var(--border-color); padding-top: 0.6rem; font-size: 0.75rem; color: var(--text-sub); }
        
        .main-chat { flex: 1; display: flex; flex-direction: column; background-color: var(--bg-dark); position: relative; }
        .chat-header { padding: 0.65rem 1rem; border-bottom: 1px solid var(--border-color); text-align: center; font-weight: 600; font-size: 0.9rem; background: rgba(33, 33, 33, 0.95); color: var(--text-sub); }
        .chat-messages { flex: 1; overflow-y: auto; padding: 1.2rem 1rem 7rem 1rem; display: flex; flex-direction: column; align-items: center; }
        .messages-container { max-width: 740px; width: 100%; display: flex; flex-direction: column; gap: 1rem; }
        
        .message-row { display: flex; gap: 0.7rem; width: 100%; transition: all 0.2s ease; }
        .message-row.user { flex-direction: row-reverse; }
        .avatar { width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.85rem; flex-shrink: 0; margin-top: 2px; }
        .avatar.user-avatar { background: #3b82f6; color: #fff; }
        .avatar.bot-avatar { background: #10b981; color: #fff; }
        
        /* Ultra Crisp Minimal ChatGPT Style */
        .bubble { max-width: 92%; padding: 0.2rem 0.1rem; line-height: 1.65; font-size: 0.88rem; word-break: break-word; position: relative; }
        .user .bubble { background-color: var(--bg-user-bubble); color: #fff; padding: 0.6rem 0.95rem; border-radius: 14px; border-top-left-radius: 3px; }
        .bot .bubble { background: transparent; color: #ececf1; border: none; box-shadow: none; }
        
        /* Compact Media Players & Download Buttons */
        .audio-player-box {
            width: 100%;
            margin: 0.4rem 0;
            background: #18181b;
            border: 1px solid #333333;
            border-radius: 8px;
            padding: 0.4rem;
        }
        audio.audio-element {
            width: 100%;
            height: 34px;
            outline: none;
        }

        .video-player-box {
            width: 100%;
            margin: 0.4rem 0;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #333333;
        }
        .video-player-box iframe {
            width: 100%;
            height: 200px;
            border: none;
        }

        .btn-download-direct {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            background: #059669;
            color: #ffffff !important;
            padding: 0.35rem 0.85rem;
            border-radius: 6px;
            text-decoration: none !important;
            font-weight: 600;
            font-size: 0.8rem;
            margin-top: 0.3rem;
            transition: background 0.2s ease;
            cursor: pointer;
        }
        .btn-download-direct:hover { background: #047857; }

        /* Animated 3-Dot Pulsing Thinking Indicator */
        .typing-dots {
            display: inline-flex;
            align-items: center;
            gap: 3px;
            margin-right: 4px;
        }
        .typing-dots span {
            width: 5px;
            height: 5px;
            background: var(--accent-gold);
            border-radius: 50%;
            animation: pulseDots 1.2s infinite ease-in-out;
        }
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes pulseDots {
            0%, 100% { transform: scale(0.6); opacity: 0.4; }
            50% { transform: scale(1.2); opacity: 1; }
        }

        .queue-badge {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 6px;
            background: rgba(251, 191, 36, 0.1);
            border: 1px solid rgba(251, 191, 36, 0.3);
            color: var(--accent-gold);
            padding: 0.2rem 0.45rem;
            border-radius: 6px;
            font-size: 0.75rem;
            margin-top: 0.3rem;
            font-weight: 600;
        }

        .cancel-btn {
            background: rgba(239, 68, 68, 0.15);
            color: var(--accent-red);
            border: 1px solid var(--accent-red);
            padding: 0.1rem 0.35rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.7rem;
            font-family: 'Cairo', sans-serif;
        }
        .cancel-btn:hover { background: var(--accent-red); color: #fff; }

        .section-title { color: var(--accent-gold); font-size: 0.95rem; font-weight: 700; margin: 0.6rem 0 0.3rem 0; display: flex; align-items: center; gap: 6px; border-bottom: 1px solid rgba(251, 191, 36, 0.15); padding-bottom: 0.15rem; }
        .quote-card { font-family: 'Amiri', serif; font-size: 1.1rem; line-height: 1.8; background: #181818; border-right: 3px solid var(--accent-gold); padding: 0.7rem 0.9rem; border-radius: 6px; margin: 0.4rem 0 0.6rem 0; color: #f1f5f9; }
        .meta-tag { background: rgba(16, 185, 129, 0.08); color: var(--accent-green); border: 1px solid rgba(16, 185, 129, 0.2); padding: 0.25rem 0.5rem; border-radius: 5px; font-size: 0.8rem; font-weight: 600; display: inline-block; margin-top: 0.25rem; }
        .thinking-status { color: var(--accent-gold); font-size: 0.82rem; font-style: italic; display: flex; align-items: center; gap: 6px; }
        
        .input-container { position: absolute; bottom: 0; left: 0; right: 0; padding: 1rem; background: linear-gradient(180deg, rgba(33,33,33,0) 0%, #212121 40%); display: flex; justify-content: center; }
        .input-box { max-width: 740px; width: 100%; background: #2f2f2f; border: 1px solid var(--border-color); border-radius: 12px; padding: 0.6rem 0.8rem; display: flex; align-items: center; gap: 8px; }
        .input-box textarea { flex: 1; background: transparent; border: none; outline: none; color: #fff; font-size: 0.88rem; font-family: 'Cairo', sans-serif; resize: none; max-height: 100px; height: 22px; }
        .send-btn { background: var(--accent-green); color: #fff; border: none; width: 30px; height: 30px; border-radius: 7px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 0.95rem; font-weight: bold; }
        .cursor { display: inline-block; width: 5px; height: 13px; background: var(--accent-gold); margin-right: 2px; animation: blink 0.8s infinite; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
    </style>
</head>
<body>
    <div class="sidebar">
        <button class="new-chat-btn" onclick="startNewChat()"><span>+</span> محادثة جديدة</button>
        <div class="sidebar-footer"><span>🟢 رفيق | دقة عالية وتدفق سلاسة</span></div>
    </div>

    <div class="main-chat">
        <div class="chat-header"><span>✨ رفيق | واجهة ChatGPT الفائقة بالبث السلس</span></div>
        <div class="chat-messages" id="chatMessages">
            <div class="messages-container" id="messagesContainer">
                <div class="message-row bot">
                    <div class="avatar bot-avatar">🤖</div>
                    <div class="bubble">
                        أهلاً بك يا رفيق! 🌸 أنا مستشارك الإسلامي الذكي.
                        <br>تفضل بطلب أي تلاوة أو فيديو أو سؤال وسيظهر لك الرد بدقة عالية وبث سلس كلمة بكلمة!
                    </div>
                </div>
            </div>
        </div>

        <div class="input-container">
            <div class="input-box">
                <textarea id="userInput" placeholder="اطرح سؤالك الشرعي هنا أو اطلب التلاوة والفيديو..." onkeydown="handleKeyDown(event)"></textarea>
                <button class="send-btn" id="sendBtn" onclick="sendMessage()">⬆</button>
            </div>
        </div>
    </div>

    <script>
        let isGenerating = false;
        let queryQueue = [];

        function handleKeyDown(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        }

        function startNewChat() {
            if (isGenerating || queryQueue.length > 0) return;
            const container = document.getElementById('messagesContainer');
            container.innerHTML = `
                <div class="message-row bot">
                    <div class="avatar bot-avatar">🤖</div>
                    <div class="bubble">بدأت محادثة جديدة! 🌸 تفضل بطرح سؤالك الشرعي أو طلب التلاوة.</div>
                </div>
            `;
        }

        function cancelQueuedMsg(msgId) {
            const idx = queryQueue.findIndex(item => item.id === msgId);
            if (idx !== -1) {
                const item = queryQueue[idx];
                queryQueue.splice(idx, 1);
                if (item.userRow) item.userRow.remove();
            }
        }

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const query = input.value.trim();
            if (!query) return;

            const msgId = 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5);
            const container = document.getElementById('messagesContainer');

            const userRow = document.createElement('div');
            userRow.className = 'message-row user';
            userRow.id = msgId;

            let bubbleHTML = escapeHtml(query);

            if (isGenerating) {
                bubbleHTML += `
                    <div class="queue-badge" id="badge_${msgId}">
                        <span>⏳ في قائمة الانتظار...</span>
                        <button class="cancel-btn" onclick="cancelQueuedMsg('${msgId}')">❌ تراجع</button>
                    </div>
                `;
            }

            userRow.innerHTML = `<div class="avatar user-avatar">👤</div><div class="bubble">${bubbleHTML}</div>`;
            container.appendChild(userRow);
            input.value = '';
            scrollToBottom();

            if (isGenerating) {
                queryQueue.push({ id: msgId, query: query, userRow: userRow });
                return;
            }

            processQueryItem({ id: msgId, query: query, userRow: userRow });
        }

        async function processQueryItem(item) {
            isGenerating = true;
            const container = document.getElementById('messagesContainer');

            const badge = document.getElementById('badge_' + item.id);
            if (badge) badge.remove();

            const botRow = document.createElement('div');
            botRow.className = 'message-row bot';
            const botBubble = document.createElement('div');
            botBubble.className = 'bubble';
            botRow.innerHTML = `<div class="avatar bot-avatar">🤖</div>`;
            botRow.appendChild(botBubble);
            container.appendChild(botRow);

            // Animated 3-Dot Pulsing Thinking Indicator
            botBubble.innerHTML = `<div class="thinking-status">💭 جاري التفكير والبحث <span class="typing-dots"><span></span><span></span><span></span></span></div>`;
            scrollToBottom();

            try {
                const res = await fetch('/api/query', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query: item.query})
                });
                
                if (!res.ok) throw new Error("HTTP error " + res.status);

                const data = await res.json();
                const rawText = data.raw_response || "عذراً، لم تتوصل الخدمة لنتيجة.";

                // Smooth Word-by-Word Streaming Typewriter Animation (ChatGPT Style)
                const words = rawText.split(' ');
                let currentText = '';
                botBubble.innerHTML = '<span class="cursor"></span>';

                for (let i = 0; i < words.length; i++) {
                    const word = words[i];
                    currentText += word + ' ';
                    botBubble.innerHTML = formatMarkdown(currentText) + '<span class="cursor"></span>';
                    scrollToBottom();

                    let delay = 45;
                    if (word.endsWith('.') || word.endsWith('،') || word.endsWith('!') || word.includes('\n')) {
                        delay = 140;
                    }
                    await new Promise(r => setTimeout(r, delay));
                }

                botBubble.innerHTML = formatMarkdown(currentText.trim());

            } catch (err) {
                botBubble.innerHTML = `<span style="color:#ef4444;">حدث خطأ في الاستجابة: ${err.message}</span>`;
            } finally {
                isGenerating = false;
                scrollToBottom();

                if (queryQueue.length > 0) {
                    const nextItem = queryQueue.shift();
                    processQueryItem(nextItem);
                }
            }
        }

        function formatMarkdown(text) {
            if (!text) return '';
            let html = text;

            // 1. Replace [PLAYER:url] with Compact Interactive Audio or YouTube Iframe
            html = html.replace(/\[PLAYER:(.*?)\]/g, function(match, url) {
                url = url.trim();
                if (url.includes('youtube.com') || url.includes('youtu.be')) {
                    let videoId = '';
                    if (url.includes('v=')) {
                        videoId = url.split('v=')[1].split('&')[0];
                    } else if (url.includes('youtu.be/')) {
                        videoId = url.split('youtu.be/')[1].split('?')[0];
                    }
                    if (videoId) {
                        return `<div class="video-player-box"><iframe src="https://www.youtube.com/embed/${videoId}" allowfullscreen></iframe></div>`;
                    }
                }
                return `<div class="audio-player-box"><audio controls class="audio-element" src="${url}"></audio></div>`;
            });

            // 2. Replace [DOWNLOAD:url] with Compact Interactive Download Button
            html = html.replace(/\[DOWNLOAD:(.*?)\]/g, function(match, url) {
                url = url.trim();
                return `<a href="${url}" target="_blank" download class="btn-download-direct">📥 اضغط هنا للتحميل المباشر (MP3 / MP4)</a>`;
            });

            // 3. Format Headings & Quote Cards
            html = html.replace(/###\s*(.*?)(\n|<br>|$)/g, '<div class="section-title">$1</div>');
            html = html.replace(/>\s*"([\s\S]*?)"/g, '<div class="quote-card">"$1"</div>');
            html = html.replace(/📌\s*(.*?)(\n|<br>|$)/g, '<div class="meta-tag">📌 $1</div>');
            html = html.replace(/---/g, '<hr style="border:0; border-top:1px solid #333333; margin:0.6rem 0;">');
            html = html.replace(/\n/g, '<br>');

            return html;
        }

        function scrollToBottom() {
            const chatMessages = document.getElementById('chatMessages');
            if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function escapeHtml(text) {
            return text
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/query")
async def process_query(req: QueryRequest):
    eng = get_engine()
    raw_answer = eng.answer_query(req.query)
    return JSONResponse(content={"raw_response": raw_answer})

if __name__ == "__main__":
    port = find_free_port(8080)
    print("\n==================================================================")
    print("  [+] Server running successfully! Open browser at:")
    print(f"      http://127.0.0.1:{port}")
    print("==================================================================\n")
    uvicorn.run(app, host="127.0.0.1", port=port)
