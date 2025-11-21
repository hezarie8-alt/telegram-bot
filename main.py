import telebot
import requests

TELEGRAM_TOKEN = '7690534947:AAFf2YpBstmMoRkvlxKiSygKKssVBGwnEYo'
OPENROUTER_API_KEY = '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'
USERS_FILE = 'users.txt'

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_states = {}

# دیکشنری برای نگهداری آدرس وب‌سایت ابزارهای هوش مصنوعی
AI_TOOL_URLS = {
    # LLM Models
    "GPT": "https://chat.openai.com",
    "Claude": "https://claude.ai",
    "Gemini": "https://gemini.google.com",
    "Llama": "https://llama.meta.com",
    "Mistral Large": "https://chat.mistral.ai/chat",
    "Grok": "https://grok.x.ai",
    "Command R+": "https://cohere.com/command",
    "Cohere": "https://cohere.com",

    # Code/Dev Tools
    "GitHub Copilot": "https://github.com/features/copilot",
    "CodeLlama": "https://llama.meta.com/docs/model-cards-and-releases/code-llama",
    "Amazon CodeWhisperer": "https://aws.amazon.com/codewhisperer",
    "Tabnine": "https://www.tabnine.com",
    "Replit Ghostwriter": "https://replit.com/site/ai",
    "Z": "https://z.dev",

    # Image/Art Tools
    "Midjourney": "https://www.midjourney.com",
    "DALL-E": "https://openai.com/dall-e-3",
    "Stable Diffusion": "https://stability.ai",
    "Adobe Firefly": "https://firefly.adobe.com",
    "Ideogram": "https://ideogram.ai",

    # Audio/Music Tools
    "Suno": "https://suno.com",
    "Udio": "https://www.udio.com",
    "ElevenLabs": "https://elevenlabs.io",
    "Murf": "https://murf.ai",
    "AIVA": "https://www.aiva.ai",

    # Video Tools
    "Sora": "https://openai.com/sora",
    "Gemini": "https://gemini.google.com", # This is a duplicate, but it's also a video tool
    "Pika Labs": "https://pika.art",
    "Runway Gen": "https://runwayml.com",
    "HeyGen": "https://www.heygen.com",
    "Synthesia": "https://www.synthesia.io",

    # Business Tools
    "Perplexity": "https://www.perplexity.ai",
    "kimi": "https://kimi.moonshot.cn",
    "Jasper": "https://www.jasper.ai",
    "Z": "https://z.dev", # Duplicate, but also a business tool
    "Gamma": "https://gamma.app",
    "Zapier Central": "https://zapier.com/central",
}

# دیکشنری برای نگهداری تمام متن‌ها در دو زبان
TEXTS = {
    "fa": {
        "jaguar_button": "🤖 Jaguar AI",
        "jaguar_welcome": "به Jaguar AI خوش آمدید! از من هر سوالی دارید بپرسید.",
        "jaguar_typing": "Jaguar در حال پاسخ دادن است...",
        "jaguar_empty_response_error": "متأسفانه، Jaguar نمی‌تواند در حال حاضر به این سوال پاسخ دهد.",
        "welcome": "سلام! به ربات ما خوش آمدید.\n\nلطفاً زبان مورد نظر خود را انتخاب کنید:",
        "lang_button_fa": "فارسی",
        "lang_button_en": "English",
        "category_select": "دسته‌بندی مورد نظرت رو انتخاب کن:",
        "category_descriptions": """
*🤖 best ai:* بهترین مدل های هوش مصنوعی در زمینه های مختلف را به شما معرفی می‌کند.

*📚 Writing:* ایده‌ها را به پرامپت‌های نوشتاری مشخص (مثل پست وبلاگ، ایمیل) تبدیل می‌کند.

*🎨 Image:* ایده‌ها را به پرامپت‌های دقیق برای تولید تصویر تبدیل می‌کند.

*👨‍💻 Code:* درخواست‌ها را به پرامپت‌های فنی برای نوشتن کد تبدیل می‌کند.

*📈 Business:* ایده‌ها را به پرامپت‌های حرفه‌ای برای مسائل کسب‌وکار تبدیل می‌کند.

*🧠 Brainstorm:* ایده‌ها را به پرامپت‌های باز برای تولید راه‌حل‌های خلاقانه تبدیل می‌کند.

*❓ Other:* مشکلات کلی را به پرامپت‌های واضح و مختصر تبدیل می‌کند.
        """,
        "best_ai_category_select": "دسته‌بندی Best AI را انتخاب کن:",
        "best_ai_category_descriptions": """
*🔝 Best AI:* بهترین ابزارهای هوش مصنوعی در دسته‌بندی‌های مختلف
        """,
        "back_to_main": "🔙 بازگشت به صفحه اصلی",
        "change_category": "🔙 تغییر دسته‌بندی",
        "category_selected": " ✅ ",
        "awaiting_input_message": "حالا ایده یا درخواست خود را بنویسید تا به یک پرامپت مناسب تبدیل شود:",
        "llm_models_title": "مدل‌های زبان بزرگ و گفتگو:",
        "code_dev_tools_title": "ابزارهای کدنویسی و توسعه نرم‌افزار:",
        "image_art_tools_title": "ابزارهای تولید تصویر و هنر دیجیتال:",
        "audio_music_tools_title": "ابزارهای تولید صدا و موسیقی:",
        "video_tools_title": "ابزارهای تولید ویدیو:",
        "business_tools_title": "ابزارهای تخصصی و کسب‌وکار:",
        # دسته‌بندی‌ها
        "best_ai_button": "Best AI",
        "writing_button": "📚 Writing",
        "art_image_button": "🎨 Image",
        "code_dev_button": "👨‍💻 Code",
        "business_button": "📈 Business",
        "brainstorm_button": "🧠 Brainstorm",
        "other_button": "❓ Other",
        # زیرمجموعه‌های Best AI
        "chat_models_button": "گفت و گو",
        "code_dev_ai_button": "کدنویسی و توسعه",
        "image_art_ai_button": "تصویر و هنر",
        "audio_music_ai_button": "صدا و موسیقی",
        "video_ai_button": "تولید ویدیو",
        "business_ai_button": "ابزارهای تخصصی و کسب‌وکار",
        # پیام‌های خطا
        "processing_error": "❌ خطا در پردازش درخواست",
        "ai_communication_error": "❌ خطا در ارتباط با هوش مصنوعی",
        # پیام‌های جدید برای باز کردن لینک
        "visit_website_message": "برای باز کردن وب‌سایت {tool_name} روی دکمه زیر کلیک کنید:",
        "visit_website_button": "باز کردن وب‌سایت",
        "tool_not_found": "متأسفانه، لینکی برای این ابزار پیدا نشد.",
        # دستورالعمل و الگوهای تولید پرامپت
        "system_instruction": (
            "شما یک فرمت‌دهنده حرفه‌ای پرامپت هستید. "
            "وظیفه شما بازنویسی ورودی کاربر به یک دستور واضح، دقیق و مختصر برای یک دستیار هوش مصنوعی تخصصی است. "
            "فقط دستور نهایی را برگردانید. عناوین، لیست‌ها، توضیحات یا متای اضافی را شامل نشوید. "
            "زبان دستور نهایی باید همان زبان ورودی کاربر (فارسی یا انگلیسی) باشد."
        ),
        "patterns": {
            "👨‍💻 Code / Dev": {
                "simple": (
                    "ورودی کاربر:\n{user_input}\n\n"
                    "دستور:\n"
                    "این ورودی را به یک پرامپت بسیار مختصر و شفاف (حداکثر ۲ جمله) تبدیل کن "
                    "که دقیقا توضیح دهد چه کدی باید نوشته شود. "
                    "نوع خروجی مورد انتظار (تابع/اسکریپت/کد) را مشخص کن. "
                    "هیچ تحلیل یا توضیح اضافی نده و فقط پرامپت نهایی را برگردان."
                ),
                "complex": (
                    "ورودی کاربر:\n{user_input}\n\n"
                    "دستور:\n"
                    "این ورودی را به یک پرامپت بسیار دقیق و فنی برای یک توسعه‌دهنده تبدیل کن. "
                    "پرامپت باید شامل موارد زیر باشد:\n"
                    "- زبان برنامه‌نویسی\n"
                    "- ساختار و ماژول‌ها\n"
                    "- ورودی‌ها و خروجی‌های مورد انتظار\n"
                    "- هر محدودیت، شرط، یا ویژگی ضروری\n"
                    "پرامپت را کاملاً واضح، قابل اجرا و بدون هیچ متن اضافی تولید کن. "
                    "فقط پرامپت نهایی را برگردان."
                )
            },

            "📚 Writing": (
                "ورودی کاربر:\n{user_input}\n\n"
                "دستور:\n"
                "این ورودی را به یک پرامپت حرفه‌ای برای تولید محتوا تبدیل کن. "
                "در پرامپت موارد زیر باید مشخص شوند:\n"
                "- نوع محتوا (مثل پست وبلاگ، ایمیل، کپشن، متن فروش)\n"
                "- مخاطب هدف\n"
                "- لحن (رسمی، دوستانه، الهام‌بخش، فروش محور...)\n"
                "- هدف اصلی محتوا (مثلاً افزایش تعامل، آموزش، فروش)\n"
                "پرامپت را شفاف، کامل و فقط به صورت خروجی نهایی برگردان."
            ),

            "🎨 Art / Image": (
                "ورودی کاربر:\n{user_input}\n\n"
                "دستور:\n"
                "این ورودی را به یک پرامپت حرفه‌ای تولید تصویر تبدیل کن. "
                "پرامپت باید شامل موارد زیر باشد:\n"
                "- موضوع اصلی تصویر\n"
                "- سبک هنری (مثلاً رئالیسم، سینمایی، انیمه، ایلوستریشن...)\n"
                "- ترکیب‌بندی (زاویه دوربین، فاصله، فریم)\n"
                "- نورپردازی (قوی، ملایم، طلوع خورشید، استودیو...)\n"
                "- حال‌وهوا و فضای کلی\n"
                "- رنگ‌ها یا پالت رنگی پیشنهادی\n"
                "از توصیف هنری، دقیق و الهام‌بخش استفاده کن. فقط پرامپت نهایی را برگردان."
            ),

            "📈 Business": (
                "ورودی کاربر:\n{user_input}\n\n"
                "دستور:\n"
                "این ورودی را به یک پرامپت حرفه‌ای کسب‌وکارمحور تبدیل کن. "
                "پرامپت باید شامل موارد زیر باشد:\n"
                "- هدف دقیق کسب‌وکار\n"
                "- حوزه (بازاریابی، استراتژی، مالی، مدیریت، فروش...)\n"
                "- نوع خروجی مورد انتظار (مثل برنامه، تحلیل، استراتژی، ساختار، لیست اقدامات)\n"
                "- هر محدودیت یا KPI مهم\n"
                "پرامپت را واضح، دقیق و آماده درک توسط یک متخصص تولید کن. فقط پرامپت نهایی را بده."
            ),

            "🧠 Brainstorm": (
                "ورودی کاربر:\n{user_input}\n\n"
                "دستور:\n"
                "این ورودی را به یک پرامپت باز و خلاقانه تبدیل کن که بتواند طیف زیادی از ایده‌ها، "
                "راه‌حل‌ها یا پیشنهادهای نوآورانه تولید کند. "
                "تمرکز بر گسترش دامنه‌ی فکر و امکان‌پذیری انواع سناریوها باشد. "
                "فقط پرامپت خالص و نهایی را برگردان."
            ),

            "❓ Other": (
                "ورودی کاربر:\n{user_input}\n\n"
                "دستور:\n"
                "این ورودی را به یک پرامپت کوتاه و بسیار شفاف (۱–۲ جمله) تبدیل کن "
                "که دقیقاً مشکل یا نیاز اصلی کاربر را برای یک دستیار متخصص توضیح دهد. "
                "هیچ توضیح یا حاشیه اضافی نده. فقط پرامپت نهایی را برگردان."
            )
        }
    },
    "en": {
        "jaguar_button": "🤖 Jaguar AI",
        "jaguar_welcome": "Welcome to Jaguar AI! Ask me anything.",
        "jaguar_typing": "Jaguar is typing...",
        "jaguar_empty_response_error": "Sorry, Jaguar could not provide an answer to this question at the moment.",
        "welcome": "Hello! Welcome to our bot.\n\nPlease select your preferred language:",
        "lang_button_fa": "فارسی",
        "lang_button_en": "English",
        "category_select": "Please select a category:",
        "category_descriptions": """
*🤖 best ai:* Introduces you to the best AI models in various fields.

*📚 Writing:* Turns ideas into specific writing prompts (like a blog post, email).

*🎨 Image:* Turns ideas into detailed prompts for image generation.

*👨‍💻 Code:* Turns requests into technical prompts for writing code.

*📈 Business:* Turns ideas into professional prompts for business issues.

*🧠 Brainstorm:* Turns ideas into open prompts for generating creative solutions.

*❓ Other:* Turns general problems into clear and concise prompts.
        """,
        "best_ai_category_select": "Select a Best AI category:",
        "best_ai_category_descriptions": """
*🔝 Best AI:* The best AI tools in various categories
        """,
        "back_to_main": "🔙 Back to Main Menu",
        "change_category": "🔙 Change Category",
        "category_selected": "✅",
        "awaiting_input_message": "Now, write your idea or request to have it converted into a suitable prompt:",
        "llm_models_title": "Large Language Models & Chat:",
        "code_dev_tools_title": "Coding & Software Development Tools:",
        "image_art_tools_title": "Image Generation & Digital Art Tools:",
        "audio_music_tools_title": "Audio & Music Generation Tools:",
        "video_tools_title": "Video Generation Tools:",
        "business_tools_title": "Specialized & Business Tools:",
        # Categories
        "best_ai_button": "Best AI",
        "writing_button": "📚 Writing",
        "art_image_button": "🎨 Image",
        "code_dev_button": "👨‍💻 Code",
        "business_button": "📈 Business",
        "brainstorm_button": "🧠 Brainstorm",
        "other_button": "❓ Other",
        # Best AI Subcategories
        "chat_models_button": "Chat Models",
        "code_dev_ai_button": "Code & Dev",
        "image_art_ai_button": "Image & Art",
        "audio_music_ai_button": "Audio & Music",
        "video_ai_button": "Video",
        "business_ai_button": "Business & Specialized",
        # Error messages
        "processing_error": "❌ Error processing request",
        "ai_communication_error": "❌ Error communicating with AI",
        # New messages for opening links
        "visit_website_message": "Click the button below to visit the {tool_name} website:",
        "visit_website_button": "Open Website",
        "tool_not_found": "Sorry, a link for this tool could not be found.",
        # System instruction and prompt generation patterns
        "system_instruction": (
            "You are a professional prompt formatter. "
            "Your task is to rewrite the user's input into a clear, precise, and concise command for a specialized AI assistant. "
            "Return only the final command. Do not include titles, lists, explanations, or extra metadata. "
            "The language of the final command must be the same as the user's input language (Persian or English)."
        ),
        "patterns": {
            "👨‍💻 Code / Dev": {
                "simple": (
                    "User input:\n{user_input}\n\n"
                    "Instruction:\n"
                    "Rewrite the input as a short 1–2 sentence prompt that clearly describes what code the assistant should generate. "
                    "Do NOT write any code. Do NOT solve the problem. Only create the prompt that tells another AI what code to write. "
                    "Return only the final prompt."
                ),
                "complex": (
                    "User input:\n{user_input}\n\n"
                    "Instruction:\n"
                    "Convert this request into a detailed technical prompt for generating code. "
                    "Specify the programming language, requirements, constraints, expected behavior, inputs, and outputs. "
                    "Do NOT provide or write any code yourself. Only produce the prompt that instructs an AI to generate the code. "
                    "Return only the final prompt."
                )
            },

            "📚 Writing": (
                "User input:\n{user_input}\n\n"
                "Instruction:\n"
                "Turn this into a complete writing prompt. "
                "Specify content type, target audience, tone, and purpose. "
                "Do NOT write the actual content—return only the final prompt."
            ),

            "🎨 Art / Image": (
                "User input:\n{user_input}\n\n"
                "Instruction:\n"
                "Turn this input into a detailed visual prompt for image generation. "
                "Describe subject, style, composition, lighting, colors, and mood. "
                "Do NOT generate or describe an actual image result—return only the final prompt."
            ),

            "📈 Business": (
                "User input:\n{user_input}\n\n"
                "Instruction:\n"
                "Create a business-oriented prompt that defines the business goal, context, and desired output format. "
                "Do NOT generate the business solution—return only the prompt."
            ),

            "🧠 Brainstorm": (
                "User input:\n{user_input}\n\n"
                "Instruction:\n"
                "Rewrite this as an open-ended creative prompt for generating ideas. "
                "Do NOT produce the ideas yourself—only return the final prompt."
            ),

            "❓ Other": (
                "User input:\n{user_input}\n\n"
                "Instruction:\n"
                "Convert this into a short, clear 1–2 sentence prompt that explains the problem or request. "
                "Do NOT solve the problem—return only the final prompt."
            )
        }
    }
}

# لیست مدل‌های زبان بزرگ و گفتگو
LLM_MODELS = [
    "GPT", "Claude", "Gemini", "Llama", 
    "Mistral Large", "Grok", "Command R+", "Cohere"
]

# لیست ابزارهای کدنویسی و توسعه
CODE_DEV_TOOLS = [
    "GitHub Copilot", "CodeLlama", "Amazon CodeWhisperer", 
    "Tabnine", "Replit Ghostwriter", "Z"
]

# لیست ابزارهای تولید تصویر و هنر دیجیتال
IMAGE_ART_TOOLS = [
    "Midjourney", "DALL-E", "Stable Diffusion", 
    "Adobe Firefly", "Ideogram"
]

# لیست ابزارهای تولید صدا و موسیقی
AUDIO_MUSIC_TOOLS = [
    "Suno", "Udio", "ElevenLabs", 
    "Murf", "AIVA"
]

# لیست ابزارهای تولید ویدیو
VIDEO_TOOLS = [
    "Sora", "Gemini", "Pika Labs", 
    "Runway Gen", "HeyGen", "Synthesia"
]

# لیست ابزارهای تخصصی و کسب‌وکار
BUSINESS_TOOLS = [
    "Perplexity", "kimi", "Jasper", 
    "Z", "Gamma", "Zapier Central"
]

def escape_markdown(text):
    escape_chars = r'\\_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + c if c in escape_chars else c for c in text])

def create_inline_keyboard(tools_list):
    """
    ایجاد یک کیبورد اینلاین با حداکثر 2 دکمه در هر ردیف برای جلوگیری از کوتاه شدن نام‌ها.
    """
    keyboard = telebot.types.InlineKeyboardMarkup()
    
    # تقسیم ابزارها به ردیف‌های 2 تایی
    rows = [tools_list[i:i+2] for i in range(0, len(tools_list), 2)]
    
    for row in rows:
        buttons = [telebot.types.InlineKeyboardButton(text=tool, callback_data=f"tool_{tool}") for tool in row]
        keyboard.row(*buttons)
    
    return keyboard

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    
    # ذخیره شناسه کاربر
    save_user_id(user_id)
    
    # نمایش کیبورد انتخاب زبان
    lang_keyboard = telebot.types.InlineKeyboardMarkup()
    lang_keyboard.row(
        telebot.types.InlineKeyboardButton(text="فارسی", callback_data="lang_fa"),
        telebot.types.InlineKeyboardButton(text="English", callback_data="lang_en")
    )
    
    # ارسال پیام خوشامدگویی و درخواست انتخاب زبان
    bot.send_message(user_id, TEXTS["fa"]["welcome"], reply_markup=lang_keyboard)
    
    # تنظیم وضعیت کاربر به انتظار برای انتخاب زبان
    user_states[user_id] = {"step": "awaiting_language"}

@bot.callback_query_handler(func=lambda call: True)
def callback_query_handler(call):
    """
    مدیریت کلیک‌ها روی دکمه‌های اینلاین (انتخاب زبان و ابزارها)
    """
    user_id = call.from_user.id
    state = user_states.get(user_id, {})
    lang = state.get("language", "fa") # Get language, default to fa
    texts = TEXTS[lang]
    
    # مدیریت انتخاب زبان
    if call.data.startswith("lang_"):
        selected_lang = call.data.split("_")[1]
        
        # به‌روزرسانی وضعیت کاربر با زبان انتخاب شده
        user_states[user_id] = {"step": "category", "language": selected_lang}
        
        # ارسال پاسخ به callback_query برای اینکه دکمه لودینگ متوقف شود
        bot.answer_callback_query(callback_query_id=call.id)
        
        # ارسال منوی دسته‌بندی‌ها با زبان انتخاب شده
        send_category_menu(user_id, selected_lang)
    
    # مدیریت کلیک روی ابزارها
    elif call.data.startswith("tool_"):
        tool_name = call.data.split('_', 1)[1]
        
        # ارسال پاسخ به callback_query برای اینکه دکمه لودینگ متوقف شود
        bot.answer_callback_query(call.id)
        
        # پیدا کردن آدرس وب‌سایت ابزار
        url = AI_TOOL_URLS.get(tool_name)
        
        if url:
            # ایجاد کیبورد با دکمه لینک
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.add(telebot.types.InlineKeyboardButton(text=texts["visit_website_button"], url=url))
            
            # ارسال پیام به کاربر
            bot.send_message(
                user_id,
                texts["visit_website_message"].format(tool_name=tool_name),
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            # اگر ابزار پیدا نشد
            bot.send_message(user_id, texts["tool_not_found"])

def send_category_menu(user_id, lang):
    """
    ارسال منوی دسته‌بندی‌ها بر اساس زبان انتخاب شده
    """
    texts = TEXTS[lang]
    
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(texts["jaguar_button"])
    markup.row(texts["best_ai_button"])
    markup.row(texts["writing_button"], texts["art_image_button"], texts["code_dev_button"])
    markup.row(texts["business_button"], texts["brainstorm_button"], texts["other_button"])
    
    bot.send_message(
        user_id, 
        f"{texts['category_select']}\n{texts['category_descriptions']}", 
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: True)
def message_handler(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    
    # اگر کاربر هنوز زبان خود را انتخاب نکرده است، کاری نکن
    if not state or "language" not in state:
        return
    
    lang = state["language"]
    texts = TEXTS[lang]
    current_step = state.get("step")

    # مدیریت دکمه‌های بازگشت و تغییر دسته‌بندی
    if message.text == texts["back_to_main"] or message.text == texts["change_category"]:
        state["step"] = "category"
        send_category_menu(user_id, lang)
        return

    # مدیریت کلیک روی دکمه Jaguar
    if message.text == texts["jaguar_button"]:
        state["step"] = "jaguar_chat"
        
        back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        back_button.row(texts["back_to_main"])
        
        bot.send_message(
            user_id,
            texts["jaguar_welcome"],
            reply_markup=back_button
        )
        return

    # مدیریت دسته‌بندی Best AI
    if message.text == texts["best_ai_button"]:
        state["step"] = "best_ai_category"
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(texts["chat_models_button"], texts["code_dev_ai_button"])
        markup.row(texts["image_art_ai_button"], texts["audio_music_ai_button"])
        markup.row(texts["video_ai_button"], texts["business_ai_button"])
        markup.row(texts["back_to_main"])
        
        bot.send_message(
            user_id, 
            f"{texts['best_ai_category_select']}\n{texts['best_ai_category_descriptions']}", 
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return

    # مدیریت دسته‌بندی‌های Best AI
    if current_step == "best_ai_category":
        if message.text == texts["chat_models_button"]:
            bot.send_message(
                user_id, 
                texts["llm_models_title"], 
                reply_markup=create_inline_keyboard(LLM_MODELS),
                parse_mode="Markdown"
            )
        elif message.text == texts["code_dev_ai_button"]:
            bot.send_message(
                user_id, 
                texts["code_dev_tools_title"], 
                reply_markup=create_inline_keyboard(CODE_DEV_TOOLS),
                parse_mode="Markdown"
            )
        elif message.text == texts["image_art_ai_button"]:
            bot.send_message(
                user_id, 
                texts["image_art_tools_title"], 
                reply_markup=create_inline_keyboard(IMAGE_ART_TOOLS),
                parse_mode="Markdown"
            )
        elif message.text == texts["audio_music_ai_button"]:
            bot.send_message(
                user_id, 
                texts["audio_music_tools_title"], 
                reply_markup=create_inline_keyboard(AUDIO_MUSIC_TOOLS),
                parse_mode="Markdown"
            )
        elif message.text == texts["video_ai_button"]:
            bot.send_message(
                user_id, 
                texts["video_tools_title"], 
                reply_markup=create_inline_keyboard(VIDEO_TOOLS),
                parse_mode="Markdown"
            )
        elif message.text == texts["business_ai_button"]:
            bot.send_message(
                user_id, 
                texts["business_tools_title"], 
                reply_markup=create_inline_keyboard(BUSINESS_TOOLS),
                parse_mode="Markdown"
            )
        return

    # مدیریت چت با Jaguar
    if current_step == "jaguar_chat":
        user_input = message.text.strip()
        
        # نمایش پیام در حال تایپ
        bot.send_chat_action(user_id, 'typing')
        
        # دریافت پاسخ از Jaguar
        response = chat_with_jaguar(user_input, lang)
        
        # بررسی اینکه آیا پاسخ خالی است یا خیر
        if not response or not response.strip():
            # اگر پاسخ خالی بود، یک پیام خطای مناسب به کاربر نمایش بده
            response = texts["jaguar_empty_response_error"]

        back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        back_button.row(texts["back_to_main"])
        
        bot.send_message(
            user_id,
            response,
            reply_markup=back_button
        )
        return

    # مدیریت دسته‌بندی‌های اصلی
    if current_step == "category":
        state["category"] = message.text
        state["step"] = "awaiting_input"

        back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        back_button.row(texts["change_category"])

        bot.send_message(
            user_id,
            f"{texts['category_selected']} *{message.text}*",
            parse_mode="Markdown",
            reply_markup=back_button
        )

    elif current_step == "awaiting_input":
        user_input = message.text.strip()
        final_prompt = generate_request(user_input, state.get("category"), lang)
        state["last_prompt"] = final_prompt

        escaped_prompt = escape_markdown(final_prompt)

        back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        back_button.row(texts["change_category"])

        bot.send_message(user_id, f"`{escaped_prompt}`", parse_mode="MarkdownV2", reply_markup=back_button)

def is_simple_task(text):
    import re
    text = text.lower()

    simple_patterns = [
        r"(تابع|فانکشن)\s*(بنویس|بساز|تعریف کن)",
        r"(لیست|آرایه).*(بگیره|ورودی)",
        r"(اعداد|رشته|کاراکتر).*جدا کن",
        r"(برگردونه|برگردان|بازگرداندن).*"
    ]

    is_short = len(text) < 300

    for pattern in simple_patterns:
        if re.search(pattern, text):
            return is_short

    return False

def chat_with_jaguar(user_input, language):
    """
    چت با هوش مصنوعی Jaguar
    """
    # دستورالعمل سیستم برای Jaguar
    if language == "fa":
        system_instruction = (
            "شما Jaguar هستید، یک دستیار هوش مصنوعی که توسط Ehsan ساخته شده است. "
            "شما باید به سوالات کاربران پاسخ دهید و اطلاعات مفید ارائه دهید. "
            "اگر از شما در مورد هویت یا سازنده‌تان پرسیده شد، باید بگویید که Jaguar هستید و توسط Ehsan ساخته شده‌اید. "
            "پاسخ‌های شما باید مفید، دقیق و دوستانه باشد."
        )
    else:
        system_instruction = (
            "You are Jaguar, an AI assistant created by Ehsan. "
            "You should answer users' questions and provide helpful information. "
            "If asked about your identity or creator, you should say that you are Jaguar and were created by Ehsan. "
            "Your responses should be helpful, accurate, and friendly."
        )
    
    # ارسال درخواست به API هوش مصنوعی
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://jaguar.bot",
            "X-Title": "Jaguar AI Assistant"
        }

        payload = {
            "model": "google/gemma-2-9b-it",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_input}
            ],
            "max_tokens": 1000
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )

        response_data = response.json()
        return response_data['choices'][0]['message']['content'].strip()

    except Exception as e:
        if language == "fa":
            return f"❌ خطا در ارتباط با هوش مصنوعی: {str(e)}"
        else:
            return f"❌ Error communicating with AI: {str(e)}"

def generate_request(user_input, category, language):
    """
    تبدیل ورودی کاربر به پرامپت مناسب بر اساس دسته‌بندی و زبان انتخاب شده
    """
    texts = TEXTS[language]
    system_instruction = texts["system_instruction"]
    patterns = texts["patterns"]

    # بررسی دسته‌بندی و ایجاد پرامپت مناسب
    try:
        if category == "👨‍💻 Code / Dev":
            # برای دسته‌بندی کد، بررسی می‌کنیم که آیا وظیفه ساده است یا پیچیده
            pattern = patterns[category]["simple"] if is_simple_task(user_input) else patterns[category]["complex"]
            instruction = pattern.format(user_input=user_input)
        elif category in patterns:
            # برای سایر دسته‌بندی‌ها، از الگوی مربوطه استفاده می‌کنیم
            instruction = patterns[category].format(user_input=user_input)
        else:
            # اگر دسته‌بندی نامشخص بود، از الگوی پیش‌فرض استفاده می‌کنیم
            instruction = patterns["❓ Other"].format(user_input=user_input)
    except Exception as e:
        # در صورت بروز خطا، یک پیام خطای مناسب برمی‌گردانیم
        return f"{texts['processing_error']}: {str(e)}"

    # ارسال درخواست به API هوش مصنوعی
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://jaguar.bot",
            "X-Title": "Jaguar Request Formatter"
        }

        payload = {
            "model": "google/gemma-2-9b-it",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": instruction}
            ],
            "max_tokens": 500
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )

        response_data = response.json()
        return response_data['choices'][0]['message']['content'].strip()

    except Exception as e:
        return f"{texts['ai_communication_error']}: {str(e)}"

def save_user_id(user_id):
    """ذخیره شناسه کاربر در فایل برای جلوگیری از تکرار"""
    try:
        # خواندن لیست کاربران موجود
        with open(USERS_FILE, 'r') as f:
            existing_users = set(line.strip() for line in f)
    except FileNotFoundError:
        # اگر فایل وجود نداشت، لیست خالی در نظر بگیر
        existing_users = set()

    # اگر کاربر جدید بود، اضافه‌اش کن
    if str(user_id) not in existing_users:
        with open(USERS_FILE, 'a') as f:
            f.write(f"{user_id}\n")
        print(f"✅ New user saved: {user_id}")

if __name__ == '__main__':
    print("✅ ربات در حال اجراست.")
    bot.infinity_polling()