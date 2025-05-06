# app.py — Car-Tinder 2025 UI リニューアル最終版
import streamlit as st, sqlite3, numpy as np, base64
import streamlit.components.v1 as components

# ── レイアウト & グローバル CSS ───────────────────────
st.set_page_config(page_title="car-tinder", page_icon="🚗", layout="centered")
components.html("""
<style>
:root {
  --bg-main: #000;
  --accent: #FFC107;
  --like: #30E89F;
  --dislike: #FF5B5B;
  --card-radius: 18px;
  --header-h: 56px;
}
/* 以下、ヘッダー・フッター・カードデザイン・ボタン・プログレスバーの CSS を含む */
:root {
  --bg-main: #000;
  --accent: #FFC107;    /* Bumble のイエロー */
  --like: #30E89F;
  --dislike: #FF5B5B;
  --card-radius: 18px;
  --header-h: 56px;
}

/* ページ全体の背景・フォント */
body, .stApp {
  background: var(--bg-main);
  color: #fff;
  margin: 0;
  padding: 0;
  font-family: 'Inter', sans-serif;
}

/* ヘッダー/フッター */
header, footer {
  height: var(--header-h);
  display: flex;
  align-items: center;
  padding: 0 20px;
}
header {
  justify-content: flex-start;
  font: 700 20px/1 sans-serif;
  border-bottom: 1px solid #222;
}
footer {
  justify-content: center;
  font-size: 12px;
  opacity: 0.6;
  border-top: 1px solid #222;
}

/* プログレスバー */
progress {
  width: 100%;
  height: 6px;
  appearance: none;
  border: none;
  border-radius: 3px;
  background: #333;
  margin: 0;
}
progress::-webkit-progress-value {
  background: var(--accent);
}

/* カード */
#card {
  width: 100%;
  max-width: 480px;
  margin: 20px auto;
  border-radius: var(--card-radius);
  box-shadow: 0 10px 24px rgba(0,0,0,0.3);
  overflow: hidden;
  position: relative;
}
#card img {
  display: block;
  width: 100%;
  height: auto;
  object-fit: contain;
  background: #111;
}

/* モデル／年式バッジ */
.badge {
  background: var(--accent);
  color: #111;
  font-size: 11px;
  font-weight: 700;
  border-radius: 999px;
  padding: 2px 8px;
  margin-right: 6px;
}

/* Like/Dislike ボタン行 */
.btn-row {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin: 18px 0;
}
.btn {
  width: 64px;
  height: 64px;
  border: none;
  border-radius: 50%;
  font-size: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 6px 14px rgba(0,0,0,0.25);
  transition: transform .15s;
}
.btn:hover {
  transform: translateY(-2px);
}
.btn-like {
  background: var(--like);
  color: #fff;
}
.btn-dis {
  background: #222;
  color: var(--dislike);
}

/* レスポンシブ調整 */
@media (max-width: 640px) {
  header, footer {
    padding: 0 10px;
  }
  .btn-row {
    gap: 1rem;
    margin: 12px 0;
  }
}

</style>
<header>car-tinder</header>
""", height=0, scrolling=False)

# ── DB 接続 & Session 初期化 ───────────────────────
con = sqlite3.connect("cars.db", check_same_thread=False)
con.row_factory = sqlite3.Row
Ymin, Ymax = con.execute("SELECT MIN(year), MAX(year) FROM cars").fetchone()
if Ymax == Ymin: Ymax += 1
def get_random(): return con.execute("SELECT * FROM cars ORDER BY RANDOM() LIMIT 1").fetchone()
for key in ("likes","dislikes"): st.session_state.setdefault(key,[])
st.session_state.setdefault("row", get_random())
row = st.session_state["row"]

# ── 進捗バー（%表示付き） ────────────────────────
done  = len(st.session_state.likes) + len(st.session_state.dislikes)
TOTAL = 20
pct   = int(done / TOTAL * 100)
st.markdown(f\"\"\"
<div style='max-width:480px;margin:0 auto;'>
  <progress value='{done}' max='{TOTAL}'></progress>
  <p style='text-align:center;margin:4px 0 12px;'>{done}/{TOTAL} ({pct}%)</p>
</div>
\"\"\", unsafe_allow_html=True)

# ── カード表示 ────────────────────────────────
with open(row["file"], "rb") as imgf:
    img_b64 = base64.b64encode(imgf.read()).decode()
abbr = (row["make"][0] + row["model"][0]).upper()
card_html = f\"\"\"
<div id='card'>
  <img src='data:image/jpeg;base64,{img_b64}' alt='Car' />
  <div style='position:absolute;bottom:16px;left:16px;z-index:2;color:#fff;'>
    <h2 style='margin:0;font:700 28px/1.2 Inter,sans-serif'>{row['model']}</h2>
    <p style='margin:4px 0 8px;opacity:.85'>{row['make']} · {row['year']}</p>
    <span class='badge'>{abbr}</span>
  </div>
</div>
\"\"\"
components.html(card_html, height=520, scrolling=False)

# ── Like/Dislike ボタン ─────────────────────────
col1, col2 = st.columns(2)
with col1:
    if st.button("👎", key="dis", type="secondary"):
        st.session_state.dislikes.append(row["vec"])
        st.session_state["row"] = get_random()
with col2:
    if st.button("👍", key="lik", type="primary"):
        st.session_state.likes.append(row["vec"])
        st.session_state["row"] = get_random()

# ── 推薦ロジック & フッター ───────────────────────
if done >= TOTAL:
    like_v = np.mean([np.frombuffer(v,np.float32) for v in st.session_state.likes],axis=0)
    dis_v  = np.mean([np.frombuffer(v,np.float32) for v in st.session_state.dislikes],axis=0)
    pref   = like_v - dis_v
    alpha  = st.sidebar.slider("Year weight (α)",0.0,0.2,0.05,0.01)
    def score(r):
        img_s = np.dot(pref,np.frombuffer(r["vec"],np.float32))
        yr    = (r["year"]-Ymin)/(Ymax-Ymin)
        return img_s + alpha*yr
    best = max(con.execute("SELECT * FROM cars"), key=score)
    st.success(f"{best['make']} {best['model']} ({best['year']})")
    st.image(best["file"])
components.html("<footer>© 2025 car-tinder</footer>", height=0, scrolling=False)
