// ======================================
// Cloudflare Workers Telegram AI Bot
// OpenRouter দিয়ে free AI models ব্যবহার করে
// ======================================

const TELEGRAM_API = "https://api.telegram.org";

// Command দেখে সেরা free model বেছে নেয়
function chooseModel(text) {
  const t = text.toLowerCase();
  if (/code|coding|website|html|python|javascript|program|কোড|ওয়েবসাইট/.test(t))
    return "qwen/qwen3-235b-a22b:free";
  if (/research|analyze|analysis|report|রিসার্চ|বিশ্লেষণ|রিপোর্ট/.test(t))
    return "deepseek/deepseek-r1:free";
  if (/summarize|translate|summary|সারসংক্ষেপ|অনুবাদ/.test(t))
    return "google/gemini-2.0-flash-exp:free";
  if (/math|calculate|solve|গণিত|হিসাব/.test(t))
    return "deepseek/deepseek-r1:free";
  return "qwen/qwen3-235b-a22b:free";
}

async function callOpenRouter(userMessage, apiKey) {
  const model = chooseModel(userMessage);

  const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json",
      "HTTP-Referer": "https://t.me/myaibot",
      "X-Title": "Telegram AI Bot"
    },
    body: JSON.stringify({
      model: model,
      messages: [
        {
          role: "system",
          content: "তুমি একজন সহায়ক AI assistant। বাংলায় প্রশ্ন আসলে বাংলায় উত্তর দাও, ইংরেজিতে আসলে ইংরেজিতে। সুন্দর ও বিস্তারিত উত্তর দাও।"
        },
        {
          role: "user",
          content: userMessage
        }
      ],
      max_tokens: 2000
    })
  });

  const data = await response.json();

  if (data.choices && data.choices.length > 0) {
    const modelName = model.split("/")[1].split(":")[0];
    return `${data.choices[0].message.content}\n\n─────────────\n🤖 Model: ${modelName}`;
  }

  if (data.error) {
    return `❌ Error: ${data.error.message}`;
  }

  return "❌ কিছু একটা সমস্যা হয়েছে, আবার চেষ্টা করো।";
}

async function sendMessage(chatId, text, botToken) {
  // Telegram 4096 character limit
  const chunks = [];
  for (let i = 0; i < text.length; i += 4000) {
    chunks.push(text.slice(i, i + 4000));
  }

  for (const chunk of chunks) {
    await fetch(`${TELEGRAM_API}/bot${botToken}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: chatId,
        text: chunk,
        parse_mode: "Markdown"
      })
    });
  }
}

async function handleUpdate(update, botToken, openrouterKey) {
  if (!update.message || !update.message.text) return;

  const chatId = update.message.chat.id;
  const text = update.message.text;

  // Commands handle করো
  if (text === "/start") {
    await sendMessage(chatId,
      "👋 *আমি তোমার AI Assistant!*\n\nআমাকে যা করতে বলতে পারো:\n• যেকোনো প্রশ্নের উত্তর\n• Website / code লেখা\n• Research ও report\n• অনুবাদ ও সারসংক্ষেপ\n\nশুধু message পাঠাও! 🚀",
      botToken
    );
    return;
  }

  if (text === "/help") {
    await sendMessage(chatId,
      "📚 *Commands:*\n\n/start — শুরু করো\n/help — সাহায্য\n/models — কোন model কোন কাজে\n\nঅথবা সরাসরি message করো!",
      botToken
    );
    return;
  }

  if (text === "/models") {
    await sendMessage(chatId,
      "🤖 *Model selection:*\n\n💻 Code/Website → Qwen 3 235B\n🔬 Research/Analysis → DeepSeek R1\n📄 Translate/Summary → Gemini Flash\n🧮 Math/Logic → DeepSeek R1\n💬 সাধারণ কথা → Qwen 3 235B\n\nসব model সম্পূর্ণ FREE!",
      botToken
    );
    return;
  }

  // "ভাবছি..." পাঠাও
  await sendMessage(chatId, "⏳ ভাবছি...", botToken);

  // AI call করো
  const reply = await callOpenRouter(text, openrouterKey);
  await sendMessage(chatId, reply, botToken);
}

// Cloudflare Workers এর main handler
export default {
  async fetch(request, env) {
    // Webhook থেকে Telegram-এর POST request আসে
    if (request.method === "POST") {
      try {
        const update = await request.json();
        await handleUpdate(update, env.TELEGRAM_TOKEN, env.OPENROUTER_API_KEY);
        return new Response("OK", { status: 200 });
      } catch (err) {
        return new Response("Error: " + err.message, { status: 500 });
      }
    }

    // GET request — bot জীবিত আছে কিনা check করতে
    return new Response("✅ Bot is running!", { status: 200 });
  }
};
