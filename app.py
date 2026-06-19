import os
import re
import streamlit as strl
from google import genai
from google.genai import types

# ১. স্ট্রিমলিট পেজ সেটআপ
strl.set_page_config(page_title="Digital Security AI Bot", page_icon="🛡️", layout="centered")
strl.title("🛡️ Social Media Security Assistant")
strl.subheader("ফ্রি ও নিরাপদ ডিজিটাল সিকিউরিটি গাইড")

# ২. API Key হ্যান্ডেল করা (Secrets এবং সাইডবার উভয় সাপোর্ট)
if "GOOGLE_API_KEY" in strl.secrets:
    strl.session_state.api_key = strl.secrets["GOOGLE_API_KEY"]
elif "api_key" not in strl.session_state:
    strl.session_state.api_key = ""

if "messages" not in strl.session_state:
    strl.session_state.messages = [
        {"role": "assistant", "content": "হ্যালো! আমি আপনার ডিজিটাল সিকিউরিটি অ্যাসিস্ট্যান্ট। ফেসবুক, ইনস্টাগ্রাম, ইউটিউব বা টিকটকের নিরাপত্তা নিয়ে যেকোনো প্রশ্ন করতে পারেন।"}
    ]

with strl.sidebar:
    user_key = strl.text_input("আপনার Gemini API Key দিন:", type="password", value=strl.session_state.api_key)
    if user_key and user_key != strl.session_state.api_key:
        strl.session_state.api_key = user_key
        strl.rerun()

# ৩. লোকাল টেক্সট ফাইল থেকে প্রাসঙ্গিক তথ্য খোঁজার ফাংশন (RAG এর বিকল্প সহজ লজিক)
def search_local_context(query):
    if not os.path.exists("security_data.txt"):
        return ""
    
    with open("security_data.txt", "r", encoding="utf-8") as f:
        content = f.read()
    
    # প্রশ্নটির প্রধান কিওয়ার্ডগুলো দিয়ে টেক্সট ফাইল থেকে প্রাসঙ্গিক প্যারাগ্রাফ খুঁজে নেওয়া
    keywords = [word.lower() for word in query.split() if len(word) > 2]
    paragraphs = content.split("\n\n")
    relevant_chunks = []
    
    for para in paragraphs:
        for kw in keywords:
            if kw in para.lower():
                relevant_chunks.append(para)
                break
                
    return "\n\n".join(relevant_chunks[:3]) if relevant_chunks else content

# আগের চ্যাট হিস্ট্রি স্ক্রিনে দেখানো
for message in strl.session_state.messages:
    with strl.chat_message(message["role"]):
        strl.markdown(message["content"])

# ৪. অ্যাকশন এবং রেসপন্স লজিক
if not strl.session_state.api_key:
    strl.warning("⚠️ Google API Key খুঁজে পাওয়া যায়নি। অনুগ্রহ করে সাইডবারে আপনার API Key দিন।")
else:
    if user_input := strl.chat_input("এখানে আপনার সিকিউরিটি প্রশ্নটি লিখুন..."):
        with strl.chat_message("user"):
            strl.markdown(user_input)
        strl.session_state.messages.append({"role": "user", "content": user_input})
        
        try:
            # গুগলের একদম নতুন প্রোডাকশন ক্লায়েন্ট ব্যবহার
            client = genai.Client(api_key=strl.session_state.api_key)
            
            # লোকাল ফাইল থেকে তথ্য নেওয়া
            context = search_local_context(user_input)
            
            system_instruction = (
                "You are an expert Social Media Security Assistant. Help users secure their "
                "platforms (Facebook, X, Instagram, YouTube, TikTok) based ONLY on the provided context.\n\n"
                f"Context from database:\n{context}\n\n"
                "If the query is not related to the context, answer: 'দুঃখিত, এই প্ল্যাটফর্ম বা সিকিউরিটি সেটিংসের সঠিক তথ্য আমার ডেটাবেজে নেই।'\n"
                "Always try to reply in the language (Bangla/English) the user asks."
            )
            
            with strl.chat_message("assistant"):
                with strl.spinner("তথ্য খোঁজা হচ্ছে..."):
                    # ২০২৬ সালের লেটেস্ট জেমিনি মডেল দিয়ে রেসপন্স জেনারেট করা
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=user_input,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.2
                        )
                    )
                    bot_reply = response.text
                    
                    # লেখার ভেতরের যেকোনো সাধারণ লিঙ্ককে স্বয়ংক্রিয়ভাবে ক্লিকেবল লিঙ্কে রূপান্তর করার লজিক
                    url_pattern = r'(https?://[^\s]+|(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}(?:/[^\s]*)?)'
                    def make_clickable(match):
                        url = match.group(0)
                        clean_url = url if url.startswith(('http://', 'https://')) else f'https://{url}'
                        return f'[{url}]({clean_url})'
                    
                    bot_reply = re.sub(url_pattern, make_clickable, bot_reply)
                    strl.markdown(bot_reply)
                    
            strl.session_state.messages.append({"role": "assistant", "content": bot_reply})
            strl.rerun()
            
        except Exception as e:
            strl.error(f"API থেকে উত্তর তৈরিতে সমস্যা হয়েছে: {str(e)}")
