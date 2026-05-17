import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# ===== তোমার দুটো key এখানে বসাও =====
TELEGRAM_TOKEN = "তোমার_telegram_bot_token"
OPENROUTER_API_KEY = "তোমার_openrouter_api_key"
# =========================================

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Command দেখে সবচেয়ে ভালো free model বেছে নেয়
def choose_model(text: str) -> str:
    text_lower = text.lower()

    # Coding / website / programming
    if any(w in text_lower for w in ["code", "coding", "website", "html", "python", "javascript", "program", "script", "কোড", "ওয়েবসাইট"]):
        return "qwen/qwen3-235b-a22b:free"

    # Deep research / analysis / reasoning
    if any(w in text_lower for w in ["research", "analyze", "analysis", "explain", "report", "রিসার্চ", "বিশ্লেষণ", "রিপোর্ট", "ব্যাখ্যা"]):
        return "deepseek/deepseek-r1:free"

    # Long documents / summarize / translate
    if any(w in text_lower for w in ["summarize", "translate", "document", "pdf", "সারসংক্ষেপ", "অনুবাদ", "দীর্ঘ"]):
        return "google/gemini-2.0-flash-exp:free"

    # Math / logic
    if any(w in text_lower for w in ["math", "calculate", "solve", "equation", "গণিত", "হিসাব", "সমীকরণ"]):
        return "deepseek/deepseek-r1:free"

    # Default — সব ধরনের কাজের জন্য Qwen 3
    return "qwen/qwen3-235b-a22b:free"


def call_openrouter(user_message: str) -> str:
    model = choose_model(user_message)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://t.me/myaibot",
        "X-Title": "Telegram AI Bot"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "তুমি একজন সহায়ক AI assistant। বাংলায় প্রশ্ন আসলে বাংলায় উত্তর দাও, ইংরেজিতে আসলে ইংরেজিতে। সুন্দর ও বিস্তারিত উত্তর দাও।"
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        "max_tokens": 2000
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        data = response.json()

        if "choices" in data and len(data["choices"]) > 0:
            reply = data["choices"][0]["message"]["content"]
            model_used = model.split("/")[1].split(":")[0]
            return f"{reply}\n\n─────────────\n🤖 Model: {model_used}"
        else:
            return f"❌ Error: {data.get('error', {}).get('message', 'Unknown error')}"

    except requests.exceptions.Timeout:
        return "⏱️ সময় বেশি লাগছে, আবার চেষ্টা করো।"
    except Exception as e:
        return f"❌ কিছু একটা সমস্যা হয়েছে: {str(e)}"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 আমি তোমার AI Assistant!\n\n"
        "আমাকে যা করতে বলবে:\n"
        "• যেকোনো প্রশ্নের উত্তর\n"
        "• Website / code লেখা\n"
        "• Research ও report\n"
        "• অনুবাদ ও সারসংক্ষেপ\n\n"
        "শুধু message পাঠাও! 🚀"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 কমান্ড লিস্ট:\n\n"
        "/start — শুরু করো\n"
        "/help — সাহায্য\n"
        "/models — কোন model কোন কাজে\n\n"
        "অথবা সরাসরি message করো!"
    )


async def models_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Model selection:\n\n"
        "💻 Code/Website → Qwen 3 235B\n"
        "🔬 Research/Analysis → DeepSeek R1\n"
        "📄 Long doc/Translate → Gemini Flash\n"
        "🧮 Math/Logic → DeepSeek R1\n"
        "💬 সাধারণ কথা → Qwen 3 235B\n\n"
        "সব model সম্পূর্ণ FREE!"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_name = update.message.from_user.first_name

    # "ভাবছি..." দেখাও
    thinking_msg = await update.message.reply_text("⏳ ভাবছি...")

    # AI call করো
    reply = call_openrouter(user_text)

    # Reply পাঠাও
    await thinking_msg.delete()

    # Telegram-এর 4096 character limit handle
    if len(reply) > 4000:
        chunks = [reply[i:i+4000] for i in range(0, len(reply), 4000)]
        for chunk in chunks:
            await update.message.reply_text(chunk)
    else:
        await update.message.reply_text(reply)


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("models", models_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot চালু হয়েছে!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
