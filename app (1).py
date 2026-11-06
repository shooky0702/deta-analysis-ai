import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sympy as sp
from google import genai
import io
import os
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont

# --- 基本設定とCSS ---
st.set_page_config(page_title="QUANTUM ANALYTICS AI", layout="wide")
st.markdown("""
<style>
div.stDownloadButton > button {
    font-size: 1.5rem !important;
    font-weight: bold !important;
    padding: 1rem 2rem !important;
    height: auto !important;
    width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

# --- 1. 背景風の薄い3Dグラフ ---
st.markdown("<h1 style='text-align: center; color: #00E5FF; margin-bottom: 0;'>QUANTUM ANALYTICS AI</h1>", unsafe_allow_html=True)

x_bg = np.linspace(-5, 5, 50)
y_bg = np.linspace(-5, 5, 50)
X_bg, Y_bg = np.meshgrid(x_bg, y_bg)
Z_bg = np.sin(np.sqrt(X_bg**2 + Y_bg**2)) * np.exp(-0.2 * np.sqrt(X_bg**2 + Y_bg**2))

fig_bg = go.Figure(data=[go.Surface(z=Z_bg, x=X_bg, y=Y_bg, colorscale='Blues', opacity=0.15, showscale=False)])
fig_bg.update_layout(
    height=250, margin=dict(l=0, r=0, b=0, t=0),
    scene=dict(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
        zaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
        bgcolor='rgba(0,0,0,0)', camera=dict(eye=dict(x=1.5, y=1.5, z=0.5))
    ),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", dragmode=False
)
st.plotly_chart(fig_bg, use_container_width=True)

# --- 2. リアルタイム数式解析＆プロット ---
st.markdown("<h2 style='font-size: 1.8em; font-weight: bold;'>リアルタイム数式可視化エンジン</h2>", unsafe_allow_html=True)
st.markdown("SymPyエンジンを搭載。変数 `x` を用いた数式を入力すると即座にプロットします。")
user_eq = st.text_input("数式を入力（例: sin(x) * exp(-0.1*x) , x**2 - 4*x）", "sin(x) * exp(-0.1*x)")

if user_eq:
    try:
        x_sym = sp.Symbol('x')
        expr = sp.sympify(user_eq)
        f = sp.lambdify(x_sym, expr, 'numpy')
        
        x_vals = np.linspace(-10, 10, 500)
        y_vals = f(x_vals)
        
        fig_eq = go.Figure(go.Scatter(x=x_vals, y=y_vals, mode='lines', line=dict(color='#00E5FF', width=2)))
        fig_eq.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=300, margin=dict(l=0, r=0, b=0, t=30),
            xaxis=dict(showgrid=True, gridcolor='#151C2C'), yaxis=dict(showgrid=True, gridcolor='#151C2C')
        )
        st.plotly_chart(fig_eq, use_container_width=True)
    except Exception as e:
        st.warning("数式のパースに失敗しました。Pythonの記法（掛け算は *、累乗は **）で入力してください。")

st.markdown("---")

# --- 3. AIチャットエリア (Powered by Gemini) ---
st.markdown("<h2 style='font-size: 1.8em; font-weight: bold;'>AI解析アシスタント</h2>", unsafe_allow_html=True)

try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
    api_ready = True
except Exception as e:
    st.error("APIキーが設定されていないか、間違っています。")
    api_ready = False

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("AIに解析の指示や質問を入力してください..."):
    if api_ready:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        with st.chat_message("assistant"):
            with st.spinner("量子ネットワーク経由でAIが思考中..."):
                try:
                    response = client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=user_input,
                    )
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"通信エラーが発生しました: {e}")

# --- 4. PDF出力機能（サイドバー） ---
st.sidebar.markdown("<h1 style='font-size: 2em; font-weight: bold;'>レポート出力</h1>", unsafe_allow_html=True)
st.sidebar.markdown("現在の数式とAIとの解析履歴をPDFとして保存します。")

def create_pdf(equation, chat_history):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    
    font_path = r"C:\Windows\Fonts\meiryo.ttc"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('Meiryo', font_path))
        font_name = 'Meiryo'
    else:
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
        font_name = 'HeiseiKakuGo-W5'
    
    c.setFont(font_name, 16)
    c.drawString(50, 800, "QUANTUM ANALYTICS - 解析レポート")
    c.setFont(font_name, 12)
    c.drawString(50, 760, f"【可視化エンジン 入力数式】")
    c.drawString(70, 740, f"f(x) = {equation}")
    
    # グラフ出力処理を排除し、すぐ下に会話履歴を配置
    current_y = 700
    
    c.setFont(font_name, 12)
    c.drawString(50, current_y, "【AI 解析・対話履歴】")
    textobject = c.beginText(50, current_y - 30)
    textobject.setFont(font_name, 10)
    textobject.setLeading(14)
    
    if not chat_history:
        textobject.textLine("履歴はありません。")
    else:
        for msg in chat_history:
            role = "ユーザー" if msg["role"] == "user" else "AI"
            content = msg['content'].replace('\n', ' ')
            lines = [content[i:i+40] for i in range(0, len(content), 40)]
            textobject.textLine(f"■ {role}:")
            for line in lines:
                textobject.textLine(f"  {line}")
                if textobject.getY() < 50:
                    c.drawText(textobject)
                    c.showPage()
                    textobject = c.beginText(50, 800)
                    textobject.setFont(font_name, 10)
                    textobject.setLeading(14)
            textobject.textLine("")
            
    c.drawText(textobject)
    c.save()
    buffer.seek(0)
    return buffer

pdf_data = create_pdf(user_eq, st.session_state.messages)
st.sidebar.download_button(
    label="レポートをPDFでダウンロード",
    data=pdf_data,
    file_name="Quantum_Analytics_Report.pdf",
    mime="application/pdf"
)
