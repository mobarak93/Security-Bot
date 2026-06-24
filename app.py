import os
import streamlit as strl
import re
from google import genai
from google.genai import types


strl.set_page_config(page_title="Digital Security AI Bot", page_icon="🛡️", layout="centered")
strl.markdown(
    "<h1 style='text-align: left; font-size: calc(1.8rem + 1vw); word-break: keep-all; white-space: nowrap;'>🛡️ Security Assistant</h1>", 
    unsafe_allow_html=True
)
#strl.subheader("ফ্রি ও নিরাপদ ডিজিটাল সিকিউরিটি গাইড")

# ২. API Key হ্যান্ডেল করা (Secrets এবং সাইডবার উভয় সাপোর্ট)
if "GOOGLE_API_KEY" in strl.secrets:
    strl.session_state.api_key = strl.secrets["GOOGLE_API_KEY"]
elif "api_key" not in strl.session_state:
    strl.session_state.api_key = ""

if "messages" not in strl.session_state:
    strl.session_state.messages = [
        {"role": "assistant", "content": "হ্যালো! আমি আপনার ডিজিটাল সিকিউরিটি অ্যাসিস্ট্যান্ট। ফেসবুক, ইনস্টাগ্রাম, ইউটিউব বা টিকটকের নিরাপত্তা নিয়ে যেকোনো প্রশ্ন করতে পারেন।"}
    ]


def search_local_context(query):
    if not os.path.exists("security_data.txt"):
        return ""
    
    with open("security_data.txt", "r", encoding="utf-8") as f:
        content = f.read()
    
    keywords = [word.lower() for word in query.split() if len(word) > 2]
    paragraphs = content.split("\n\n")
    relevant_chunks = []
    
    for para in paragraphs:
        for kw in keywords:
            if kw in para.lower():
                relevant_chunks.append(para)
                break
                
    return "\n\n".join(relevant_chunks[:3]) if relevant_chunks else ""


for message in strl.session_state.messages:
    with strl.chat_message(message["role"]):
        strl.markdown(message["content"])


if not strl.session_state.api_key:
    strl.warning("⚠️ Google API Key খুঁজে পাওয়া যায়নি। অনুগ্রহ করে সাইডবারে আপনার API Key দিন।")
else:
    if user_input := strl.chat_input("এখানে আপনার সিকিউরিটি প্রশ্নটি লিখুন..."):
        with strl.chat_message("user"):
            strl.markdown(user_input)
        strl.session_state.messages.append({"role": "user", "content": user_input})
        
        try:
            client = genai.Client(api_key=strl.session_state.api_key)
            context = search_local_context(user_input)
            
            system_instruction = (
                "You are an expert Social Media Security Assistant. Help users secure their platforms.\n"
                "CRITICAL INSTRUCTION:\n"
                f"1. First, check this Local Context from the user's database: [{context}]. If this context contains the specific answer or links, prioritize it over everything else.\n"
                "2. If the answer is NOT found in the local context, use the enabled Google Search tool to find official, trusted, and up-to-date documentation (e.g., Meta Help Center, Google Support) to answer accurately.\n"
                "3. Always double-check security advice and prioritize official platforms' official URLs.\n"
                "4. Always try to reply in the language (Bangla/English) the user asks."
            )
            
            with strl.chat_message("assistant"):
                with strl.spinner("তথ্য খোঁজা ও যাচাই করা হচ্ছে..."):

                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=user_input,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.3,
                            tools=[{"google_search": {}}]  # এই লাইনটি লাইভ গুগল সার্চ একটিভেট করবে
                        )
                    )
                    bot_reply = response.text
                    
                   
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
# (Copyright & Branding)
strl.markdown("---")
strl.markdown(
    "<div style='text-align: center; color: #888888; font-size: 14px;'>"
    "© 2026 <b>Md. Hosne Mobarak</b> | All Rights Reserved"
    "</div>", 
    unsafe_allow_html=True
)
