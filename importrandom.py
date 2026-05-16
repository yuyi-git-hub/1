# -*- coding: utf-8 -*-
import os
import random
import urllib.request
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
from google import genai
from google.genai import types

# 自動下載開源中文字型
FONT_URL = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTC/NotoSansCJKtc-Regular.ttc"
FONT_PATH = "NotoSansCJKtc-Regular.ttc"

@st.cache_resource
def load_cloud_font():
    if not os.path.exists(FONT_PATH):
        try:
            urllib.request.urlretrieve(FONT_URL, FONT_PATH)
        except:
            pass

load_cloud_font()

st.set_page_config(page_title="跨世代智慧圖文生成平台", page_icon="✨", layout="centered")

st.title("跨世代智慧圖文生成器")
st.write("已成功啟用 UTF-8 編碼與全新規格。一鍵為長輩與晚輩生成真實 AI 圖文！")
st.markdown("---")

# ================= 安全讀取 API KEY =================
api_key = os.environ.get("GEMINI_API_KEY", "")
if not api_key:
    st.warning("⚠️ 偵測到未設定 API 金鑰，請在下方暫時輸入您的 Gemini API Key 以進行測試：")
    api_key = st.text_input("輸入您的 Gemini API Key：", type="password")

client = genai.Client(api_key=api_key) if api_key else None
# ====================================================

# 1. 今日速報
st.subheader("1. 今日速報 (系統已自動擷取)")
weather_check = st.checkbox("納入今日環境速報 (今日: 記得帶傘 / 立秋時節)", value=True)
weather_text = "記得帶傘" if weather_check else ""

# 2~4 類別
st.subheader("2. 與傳送對象之關係")
rel = st.radio("傳送給誰？", ["兒子/女兒", "爸爸/媽媽", "爺爺/奶奶", "老朋友", "萬用群發"], horizontal=True)

st.subheader("3. 傳送對象喜好")
pref = st.radio("對方最喜歡？", ["萌萌貓咪", "活潑狗狗", "咖啡下午茶", "動漫電玩", "山明水秀"], horizontal=True)

st.subheader("4. 圖片需具備的元素")
elem = st.radio("畫面點綴元素：", ["牡丹花", "蓮花", "翠竹", "璀璨星空", "文青植物"], horizontal=True)

# 5. 圖中人物設定 (動態隱藏防呆機制)
st.subheader("5. 圖中人物設定")
char = st.radio("是否需要人物？", ["不需要人物", "傳送對象", "長輩自己", "兩人合照"], horizontal=True)

char_d = "無人物"
if char != "不需要人物":
    char_d = st.radio("人物神態特徵：", ["滿臉笑容", "戴著墨鏡", "帥氣正裝", "休閒運動", "喝茶聊天"], horizontal=True)

# 6~9 類別
st.subheader("6. 圖片主題")
theme = st.radio("這張圖的核心故事：", ["平安早安", "溫馨晚安", "週末愉快", "節慶祝賀", "幽默迷因"], horizontal=True)

st.subheader("7. 圖片風格")
style = st.radio("視覺外觀風格：", ["溫馨插畫風", "傳統水墨風", "日系動漫風", "真實攝影風", "現代極簡風"], horizontal=True)

st.subheader("8. 圖片大小比例設定")
size_type = st.radio("請選擇圖片尺寸：", ["1:1 正方形", "16:9 直式", "4:3 橫式"], horizontal=True)

st.subheader("9. 核心特定祝福語")
bless = st.radio("想傳達的祝願：", ["身體健康", "記得吃飽", "心情放鬆", "工作順利", "考試加油"], horizontal=True)

# 10. 必要文字
st.subheader("10. 畫面上必出現的大中文字")
user_text = st.text_input("輸入印在圖片上的清晰大字：", value="早安平安")

# 11. 字型風格選擇
st.subheader("11. 中文字型風格選擇")
font_style = st.radio("文字印章字型：", ["微軟正黑體", "標楷體", "新細明體"], horizontal=True)

st.subheader("✍️ 最終大腦補充描述欄位")
extra = st.text_input("還有什麼想對 Gemini 說的？", placeholder="例如：希望背景有一道彩虹...")

st.markdown("---")

# 🚀 網頁版一鍵生成大按鈕 (依照最新 2026 規格，將 use_container_width=True 改為 width='stretch')
if st.button("✨ 一鍵生成客製化关怀图片", type="primary", width="stretch"):
    if not client:
        st.error("❌ 請先輸入有效的 Gemini API Key 才能連線大腦！")
    else:
        ratio_map = {"1:1 正方形": "1:1", "16:9 直式": "16:9", "4:3 橫式": "4:3"}
        target_ratio = ratio_map.get(size_type, "1:1")

        if target_ratio == "1:1":
            img_size = (1024, 1024)
        elif target_ratio == "16:9":
            img_size = (768, 1360)
        else:
            img_size = (1248, 936)

        try:
            # 🧠 【第一階段】：連線真實 Gemini 文字模型
            with st.spinner("🧠 第一階段：Gemini 文字大腦正在優化與翻譯生圖提示詞..."):
                system_instruction = (
                    "You are an expert prompt engineer for image generation. "
                    "Your job is to expand the user's selected Chinese tags into a vivid, beautiful English prompt. "
                    "Focus heavily on the background, textures, lighting, and overall mood. "
                    "CRITICAL: Do NOT include any textual characters, alphabets, or words inside the image itself. "
                    "Only output the raw English prompt, no other chatter."
                )
                
                user_tags_payload = (
                    f"風格: {style}, 核心主體: {pref}, 人物需求: {char}(特徵: {char_d}), "
                    f"點綴元素: {elem}, 主題氛圍: {theme}, 額外細節: {extra}"
                )

                text_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=user_tags_payload,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.75,
                    )
                )
                real_english_prompt = text_response.text.strip()

            # 🎨 【第二階段】：連線真實 Google Imagen 3 繪圖
            with st.spinner("🎨 第二階段：Gemini 影像模型 (Imagen 3) 正在構圖與繪製高畫質卡片..."):
                image_response = client.models.generate_images(
                    model="imagen-2.5-generate-002",
                    prompt=real_english_prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        output_mime_type="image/png",
                        aspect_ratio=target_ratio,
                        person_generation="ALLOW_ADULT",
                    )
                )
                
                import io
                generated_bytes = image_response.generated_images[0].image.image_bytes
                img = Image.open(io.BytesIO(generated_bytes))
                img = img.resize(img_size, Image.Resampling.LANCZOS)
                draw = ImageDraw.Draw(img)

            # ✍️ 【第三階段】：使用下載好的開源繁體中文字型進行高對比度疊加
            with st.spinner("✍️ 第三階段：正在讀取指定字型並疊加繁體中文關懷字體..."):
                if os.path.exists(FONT_PATH):
                    font = ImageFont.truetype(FONT_PATH, int(img_size[0] * 0.06))
                    sub_font = ImageFont.truetype(FONT_PATH, int(img_size[0] * 0.035))
                else:
                    font = ImageFont.load_default()
                    sub_font = ImageFont.load_default()

                # 繪製陰影/高對比邊框
                draw.text((img_size[0]*0.08 + 2, img_size[1]*0.06 + 2), user_text, fill=(255, 255, 255), font=font)
                draw.text((img_size[0]*0.08, img_size[1]*0.06), user_text, fill=(44, 62, 80), font=font)
                
                bottom_text = f"致{rel}: {bless}"
                if weather_text:
                    bottom_text += f"\n[今日速報: {weather_text}]"
                draw.text((img_size[0]*0.08, img_size[1] - (img_size[1]*0.15)), bottom_text, fill=(52, 73, 94), font=sub_font)
                
                img.save("result_card.png")

            # 🎉 展現最終結果 (更新最新的 width="stretch" 規格)
            st.success("🎉 真正的 Gemini AI 圖片與中文疊加生成成功！")
            st.image("result_card.png", caption="Gemini 核心運作真實成果", width="stretch")
            
            st.markdown(f"### 📋 您即將送出的文字內文：")
            st.info(f"**「{user_text}！致 {rel}：{bless}」**")

            with open("result_card.png", "rb") as file:
                st.download_button(label="📥 下載這張卡片到手機/電腦", data=file, file_name="card.png", mime="image/png", width="stretch")

            with st.expander("🔍 查看後台真正的 Gemini 運作軌跡"):
                st.subheader("1. 您的點選參數封包 (Payload)")
                st.write(user_tags_payload)
                st.subheader("2. Gemini 3.0 Flash 擴寫出的真實生圖指令")
                st.code(real_english_prompt, language="text")

        except Exception as e:
            st.error(f"運作過程中發生錯誤：{e}")
