import telebot
import requests
import os
import hashlib
import time
from flask import Flask
from threading import Thread
# --- تغییرات مربوط به دیتابیس ---
import psycopg2
from psycopg2 import pool

TELEGRAM_TOKEN = '7690534947:AAFf2YpBstmMoRkvlxKiSygKKssVBGwnEYo'
OPENROUTER_API_KEY = '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'
# USERS_FILE و LOCK_FILE دیگر مورد نیاز نیستند
ADMIN_ID = 5403642668  # شناسه تلگرام ادمین (این را با شناسه خودتان جایگزین کنید)

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_states = {}

# ساخت یک اپلیکیشن ساده با Flask
app = Flask(__name__)

@app.route('/')
def index():
    return "Jaguar Bot is running!"

# --- تغییرات مربوط به دیتابیس ---
# یک Connection Pool برای مدیریت بهتر اتصالات به دیتابیس
db_pool = None

def get_db_connection():
    """ایجاد یک اتصال به دیتابیس از طریق Connection Pool"""
    global db_pool
    if db_pool is None:
        try:
            # اطلاعات اتصال از متغیر محیطی DATABASE_URL خوانده می‌شود که Render به طور خودکار تنظیم می‌کند
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise Exception("متغیر محیطی DATABASE_URL تنظیم نشده است.")
            
            db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, dsn=database_url)
            print("✅ اتصال به دیتابیس با موفقیت برقرار شد.")
        except Exception as e:
            print(f"❌ خطا در اتصال به دیتابیس: {e}")
            raise
    return db_pool.getconn()

def release_db_connection(conn):
    """بازگرداندن اتصال به Pool"""
    if db_pool and conn:
        db_pool.putconn(conn)

def init_db():
    """ایجاد جدول کاربران در دیتابیس در صورت عدم وجود"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY
                );
            """)
            conn.commit()
            print("✅ جدول کاربران با موفقیت ایجاد یا تایید شد.")
    except Exception as e:
        print(f"❌ خطا در ایجاد جدول دیتابیس: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def save_user_id(user_id):
    """
    ذخیره شناسه کاربر در دیتابیس PostgreSQL
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # استفاده از دستور INSERT ... ON CONFLICT برای جلوگیری از خطا در صورت وجود کاربر
            cursor.execute(
                "INSERT INTO users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING;",
                (user_id,)
            )
            conn.commit()
            # بررسی اینکه آیا ردیف جدیدی اضافه شده است یا نه
            if cursor.rowcount > 0:
                print(f"✅ کاربر جدید ذخیره شد: {user_id}")
            else:
                print(f"ℹ️ کاربر از قبل وجود داشت: {user_id}")
    except Exception as e:
        print(f"❌ خطا در ذخیره کاربر {user_id}: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def get_all_users():
    """
    دریافت لیست تمام کاربران از دیتابیس PostgreSQL
    """
    conn = None
    users = []
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id FROM users;")
            users_data = cursor.fetchall()
            users = [user[0] for user in users_data]
    except Exception as e:
        print(f"❌ خطا در خواندن لیست کاربران: {e}")
    finally:
        if conn:
            release_db_connection(conn)
    return users

def run_bot():
    """تابعی برای اجرای ربات در یک Thread جداگانه با مدیریت خطای بهتر"""
    print("✅ ربات در حال اجراست...")
    print("⚠️  نکته: مطمئن شوید که این نمونه از ربات تنها نمونه در حال اجراست.")
    print("📡 در حال اتصال به سرورهای تلگرام...")
    
    # حلقه مدیریت خطا برای polling
    while True:
        try:
            # استفاده از timeout و long_polling_timeout برای اتصال پایدارتر
            bot.infinity_polling(timeout=60, long_polling_timeout=20, restart_on_change=False)
        except telebot.apihelper.ApiTelegramException as e:
            if e.error_code == 409:
                print("❌ خطا 409: نمونه دیگری از ربات در حال اجراست!")
                print("   لطفاً تمام نمونه‌های دیگر ربات را متوقف کنید.")
                print("   در حال تلاش مجدد پس از 30 ثانیه...")
                time.sleep(30)
            else:
                print(f"⚠️ خطای تلگرام: {e.description}")
                print("   در حال تلاش مجدد پس از 10 ثانیه...")
                time.sleep(10)
        except requests.exceptions.ConnectionError as e:
            print(f"🌐 خطای اتصال: {e}")
            print("   در حال تلاش مجدد پس از 15 ثانیه...")
            time.sleep(15)
        except Exception as e:
            print(f"💥 خطای پیش‌بینی نشده: {e}")
            print("   در حال تلاش مجدد پس از 20 ثانیه...")
            time.sleep(20)

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
        # پیام‌های جدید برای ویژگی تقسیم پیام
        "continue_button": "ادامه ▶️",
        "message_part_indicator": "(بخش {current}/{total})",
        # پیام‌های مربوط به broadcast
        "broadcast_sent": "✅ پیام با موفقیت به {count} کاربر ارسال شد.",
        "broadcast_failed": "❌ ارسال پیام به {count} کاربر ناموفق بود.",
        "no_users": "هیچ کاربری در دیتابیس یافت نشد.",
        "admin_only": "⛔ این دستور فقط برای ادمین قابل استفاده است.",
        "broadcast_usage": "استفاده صحیح: /broadcast پیام شما",
        "download_users_button": "📄 دریافت لیست کاربران",
        "users_list_sent": "✅ لیست کاربران با موفقیت ارسال شد.",
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
                "که دقیقا مشکل یا نیاز اصلی کاربر را برای یک دستیار متخصص توضیح دهد. "
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
        # New messages for splitting feature
        "continue_button": "Continue ▶️",
        "message_part_indicator": "(Part {current}/{total})",
        # Broadcast messages
        "broadcast_sent": "✅ Message successfully sent to {count} users.",
        "broadcast_failed": "❌ Failed to send message to {count} users.",
        "no_users": "No users found in the database.",
        "admin_only": "⛔ This command is only available to admins.",
        "broadcast_usage": "Usage: /broadcast your message",
        "download_users_button": "📄 Download User List",
        "users_list_sent": "✅ User list sent successfully.",
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
                    "Rewrite the input as a short 1–2 sentence prompt that clearly describes what the code assistant should generate. "
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
                "Describe the subject, style, composition, lighting, colors, and mood. "
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

def ensure_code_block(text, language=""):
    """
    تابعی برای اطمینان از اینکه متن داخل بلوک کد قرار دارد
    """
    # اگر متن قبلاً داخل بلوک کد است، آن را برگردان
    if text.startswith('```') and text.endswith('```'):
        return text
    
    # اگر متن شامل بلوک کد است، آن را استخراج کن
    if '```' in text:
        parts = text.split('```')
        if len(parts) >= 3:
            # اولین بلوک کد را برگردان
            code_content = parts[1]
            # اگر اولین خط زبان است، آن را جدا کن
            lines = code_content.split('\n')
            if len(lines) > 1:
                lang = lines[0].strip()
                code = '\n'.join(lines[1:])
                return f"```{lang}\n{code}\n```"
            else:
                return f"```\n{code_content}\n```"
    
    # در غیر این صورت، کل متن را در یک بلوک کد قرار بده
    return f"```{language}\n{text}\n```"

def safe_send_message(chat_id, text, reply_markup=None, parse_mode=None, retries=3):
    """
    ارسال امن پیام با مدیریت خطا و تلاش مجدد
    """
    for attempt in range(retries):
        try:
            return bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2)  # صبر 2 ثانیه قبل از تلاش مجدد
            else:
                print(f"Failed to send message after {retries} attempts: {e}")
                raise

def safe_send_document(chat_id, document, caption=None, retries=3):
    """
    ارسال امن سند با مدیریت خطا و تلاش مجدد
    """
    for attempt in range(retries):
        try:
            return bot.send_document(chat_id, document, caption=caption)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2)  # صبر 2 ثانیه قبل از تلاش مجدد
            else:
                print(f"Failed to send document after {retries} attempts: {e}")
                raise

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    
    # ذخیره شناسه کاربر در دیتابیس
    save_user_id(user_id)
    
    # نمایش کیبورد انتخاب زبان
    lang_keyboard = telebot.types.InlineKeyboardMarkup()
    lang_keyboard.row(
        telebot.types.InlineKeyboardButton(text="فارسی", callback_data="lang_fa"),
        telebot.types.InlineKeyboardButton(text="English", callback_data="lang_en")
    )
    
    # ارسال پیام خوشامدگویی و درخواست انتخاب زبان با استفاده از توابع امن
    try:
        safe_send_message(user_id, TEXTS["fa"]["welcome"], reply_markup=lang_keyboard)
    except Exception as e:
        print(f"Error sending welcome message: {e}")
    
    # تنظیم وضعیت کاربر به انتظار برای انتخاب زبان
    user_states[user_id] = {"step": "awaiting_language"}

@bot.message_handler(commands=['broadcast'])
def broadcast_handler(message):
    """
    ارسال پیام به تمام کاربران (فقط برای ادمین)
    """
    user_id = message.from_user.id
    
    # بررسی اینکه آیا کاربر ادمین است
    if user_id != ADMIN_ID:
        bot.send_message(user_id, TEXTS["fa"]["admin_only"])
        return
    
    # استخراج پیام از دستور
    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        bot.send_message(user_id, TEXTS["fa"]["broadcast_usage"])
        return
    
    broadcast_message = parts[1]
    users = get_all_users()
    
    if not users:
        bot.send_message(user_id, TEXTS["fa"]["no_users"])
        return
    
    success_count = 0
    failed_count = 0
    
    for user_id in users:
        try:
            safe_send_message(user_id, broadcast_message)
            success_count += 1
            time.sleep(0.1)  # کمی تأخیر برای جلوگیری از محدودیت تلگرام
        except Exception as e:
            print(f"Failed to send message to {user_id}: {e}")
            failed_count += 1
    
    # ارسال گزارش به ادمین
    report = f"{TEXTS['fa']['broadcast_sent'].format(count=success_count)}"
    if failed_count > 0:
        report += f"\n{TEXTS['fa']['broadcast_failed'].format(count=failed_count)}"
    
    bot.send_message(message.from_user.id, report)

@bot.message_handler(commands=['stats'])
def stats_handler(message):
    """
    نمایش آمار کاربران و امکان دریافت لیست کامل (فقط برای ادمین)
    """
    user_id = message.from_user.id
    
    # بررسی اینکه آیا کاربر ادمین است
    if user_id != ADMIN_ID:
        bot.send_message(user_id, TEXTS["fa"]["admin_only"])
        return
    
    users = get_all_users()
    total_users = len(users)
    
    stats_message = f"📊 آمار ربات:\n\n"
    stats_message += f"👥 تعداد کل کاربران: {total_users}\n"
    stats_message += f"💾 ذخیره‌سازی: دیتابیس PostgreSQL\n\n"
    stats_message += "برای دریافت لیست کامل کاربران، روی دکمه زیر کلیک کنید:"
    
    # ایجاد کیبورد اینلاین با دکمه دانلود
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton(
        text=TEXTS["fa"]["download_users_button"], 
        callback_data="download_users"
    ))
    
    bot.send_message(user_id, stats_message, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback_query_handler(call):
    """
    مدیریت کلیک‌ها روی دکمه‌های اینلاین (انتخاب زبان، ابزارها و ادامه پیام)
    """
    user_id = call.from_user.id
    state = user_states.get(user_id, {})
    lang = state.get("language", "fa")
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
    
    # مدیریت کلیک روی دکمه "ادامه"
    elif call.data.startswith("continue_"):
        # بازیابی اطلاعات بخش بعدی از حافظه
        next_chunk_index = state.get("next_chunk_index", 0)
        all_chunks = state.get("message_chunks", [])
        
        if next_chunk_index < len(all_chunks):
            next_chunk_text = all_chunks[next_chunk_index]
            next_chunk_index += 1
            
            # به‌روزرسانی وضعیت کاربر
            state["next_chunk_index"] = next_chunk_index
            
            # ساخت کیبورد برای بخش بعدی
            keyboard = telebot.types.InlineKeyboardMarkup()
            if next_chunk_index < len(all_chunks):
                keyboard.add(telebot.types.InlineKeyboardButton(text=texts["continue_button"], callback_data=f"continue_{next_chunk_index}"))
            
            # ارسال بخش بعدی پیام
            bot.send_message(user_id, next_chunk_text, reply_markup=keyboard)
            bot.answer_callback_query(call.id)
        else:
            bot.answer_callback_query(call.id, "خطا: بخش بعدی یافت نشد.", show_alert=True)
    
    # مدیریت کلیک روی دکمه دانلود کاربران
    elif call.data == "download_users":
        user_id = call.from_user.id
        
        # بررسی اینکه آیا کاربر ادمین است
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, TEXTS["fa"]["admin_only"], show_alert=True)
            return
        
        try:
            # ایجاد یک فایل متنی موقت از لیست کاربران
            users = get_all_users()
            user_list_str = "\n".join(map(str, users))
            
            # ارسال فایل به عنوان یک سند
            bot.send_document(
                user_id,
                user_list_str.encode('utf-8'),
                caption=f"لیست کاربران ربات Jaguar\nتعداد: {len(users)} کاربر"
            )
            bot.answer_callback_query(call.id, TEXTS["fa"]["users_list_sent"])
        except Exception as e:
            print(f"Error sending users file: {e}")
            bot.answer_callback_query(call.id, "خطا در ارسال فایل.", show_alert=True)
    
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
        response_data = chat_with_jaguar(user_input, lang)
        
        response_text = response_data["text"]
        is_code_request = response_data.get("is_code_request", False)
        
        # ساخت کیبورد بازگشت
        back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        back_button.row(texts["back_to_main"])
        
        # اگر درخواست کد است، پاسخ را داخل بلوک کد قرار می‌دهیم
        if is_code_request:
            # تشخیص زبان کد
            code_lang = ""
            
            # بررسی کلمات کلیدی برای تشخیص زبان
            if any(keyword in user_input.lower() for keyword in ["python", "پایتون"]):
                code_lang = "python"
            elif any(keyword in user_input.lower() for keyword in ["javascript", "js", "جاوااسکریپت"]):
                code_lang = "javascript"
            elif any(keyword in user_input.lower() for keyword in ["java", "جاوا"]):
                code_lang = "java"
            elif any(keyword in user_input.lower() for keyword in ["cpp", "c++", "سی‌پلاس‌پلاس"]):
                code_lang = "cpp"
            elif any(keyword in user_input.lower() for keyword in ["c#", "سی‌شارپ"]):
                code_lang = "csharp"
            elif any(keyword in user_input.lower() for keyword in ["html", "css"]):
                code_lang = "html"
            elif any(keyword in user_input.lower() for keyword in ["sql", "اس‌کیوال"]):
                code_lang = "sql"
            elif any(keyword in user_input.lower() for keyword in ["c", "سی"]):
                code_lang = "c"
            
            # اطمینان از اینکه پاسخ داخل بلوک کد است
            formatted_response = ensure_code_block(response_text, code_lang)
            
            # ارسال پاسخ با فرمت کد
            bot.send_message(
                user_id,
                formatted_response,
                reply_markup=back_button,
                parse_mode="Markdown"
            )
        else:
            # ارسال پاسخ معمولی
            bot.send_message(
                user_id,
                response_text,
                reply_markup=back_button,
                parse_mode=None
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

        # ارسال پرامپت تولید شده داخل بلوک کد
        bot.send_message(user_id, f"```\n{final_prompt}\n```", parse_mode="Markdown", reply_markup=back_button)

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
    چت با هوش مصنوعی Jaguar (با قابلیت تقسیم پیام طولانی)
    """
    texts = TEXTS[language]
    
    # دستورالعمل سیستم برای Jaguar
    if language == "fa":
        base_system_instruction = (
            "تو Jaguar هستی، یک دستیار هوش مصنوعی ساخته‌شده توسط Ehsan. "
            "باید به سوالات کاربران دقیق، کوتاه و مفید پاسخ بدهی. "
            "اگر از هویتت پرسیده شد، باید بگویی Jaguar هستی و توسط Ehsan ساخته شده‌ای. "
            "اگر کاربر درخواست کد کرد، باید مستقیماً کد نهایی را فقط داخل یک code block سه‌تایی Markdown بدهی "
            "و هیچ توضیح اضافی یا دکمه ادامه اضافه نکنی."
        )
        code_keywords = ["کد بنویس", "برام کد بنویس", "write code", "تابع بنویس", "برام تابع بنویس"]
    else:
        base_system_instruction = (
            "You are Jaguar, an AI assistant created by Ehsan. "
            "Your answers must be helpful, precise, and concise. "
            "If the user asks for code, you must provide the final code directly inside a Markdown code block "
            "with no extra explanation and no 'continue' button."
        )
        code_keywords = ["write code", "کد بنویس", "تابع بنویس"]

    is_code_request = any(keyword in user_input.lower() for keyword in code_keywords)

    if is_code_request:
        system_instruction = (
            base_system_instruction +
            " "
            "If the user requests code, you must output the exact code directly inside a Markdown code block "
            "using triple backticks (```), with no escaping and no explanations. "
            "Do NOT add buttons, do NOT describe how the code works, and do NOT generate prompts. "
            "Only return the raw code the user asked for."
        )
    else:
        system_instruction = base_system_instruction

    max_retries = 2
    retry_delay = 5  # 5 ثانیه

    for attempt in range(max_retries):
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
                "max_tokens": 1500  # افزایش توکن برای پاسخ‌های طولانی‌تر
            }

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                response_data = response.json()
                ai_response = response_data['choices'][0]['message']['content'].strip()
                
                # تقسیم پاسخ طولانی به بخش‌های کوچکتر
                max_message_length = 4000  # حداکثر طول پیام در تلگرام
                
                if len(ai_response) <= max_message_length:
                    # اگر پاسخ کوتاه بود، آن را به صورت عادی برگردان
                    return {
                        "text": ai_response,
                        "is_code_request": is_code_request
                    }
                else:
                    # اگر پاسخ طولانی بود، آن را تقسیم و در حافظه ذخیره کن
                    chunks = []
                    current_chunk = ""
                    for i, char in enumerate(ai_response):
                        current_chunk += char
                        if (i + 1) % max_message_length == 0 and len(current_chunk) >= max_message_length:
                            chunks.append(current_chunk)
                            current_chunk = ""
                    if current_chunk:  # اضافه کردن آخرین بخش
                        chunks.append(current_chunk)
                    
                    # ذخیره بخش‌ها در وضعیت کاربر
                    user_id_str = str(message.from_user.id)
                    user_states[user_id_str]["message_chunks"] = chunks
                    user_states[user_id_str]["next_chunk_index"] = 1
                    
                    # ساخت کیبورد با دکمه ادامه
                    keyboard = telebot.types.InlineKeyboardMarkup()
                    keyboard.add(telebot.types.InlineKeyboardButton(
                        text=texts["continue_button"], 
                        callback_data=f"continue_1"
                    ))
                    
                    # اضافه کردن شماره بخش به اولین پیام
                    first_chunk_text = chunks[0] + f"\n\n{texts['message_part_indicator'].format(current=1, total=len(chunks))}"
                    
                    return {
                        "text": first_chunk_text,
                        "reply_markup": keyboard,
                        "is_code_request": is_code_request
                    }
            
            elif response.status_code == 429:  # 429 Too Many Requests
                if attempt < max_retries - 1:
                    print(f"Rate limit hit. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                else:
                    return {"text": texts.get("rate_limit_error", "Rate limit exceeded. Please try again later."), "is_code_request": is_code_request}
            elif response.status_code == 401 or response.status_code == 403:
                return {"text": texts.get("invalid_api_key_error", "Invalid API key."), "is_code_request": is_code_request}
            else:
                print(f"API Error: Status Code {response.status_code}, Response: {response.text}")
                return {"text": texts.get("api_server_error", "API server error."), "is_code_request": is_code_request}

        except requests.exceptions.RequestException as e:
            print(f"Network Error: {e}")
            if attempt < max_retries - 1:
                print(f"Network error. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                continue
            else:
                return {"text": texts.get("network_error", "Network error."), "is_code_request": is_code_request}
        except Exception as e:
            print(f"An unexpected error occurred in chat_with_jaguar: {e}")
            return {"text": texts.get("unknown_error", "An unknown error occurred."), "is_code_request": is_code_request}

    return {"text": texts.get("unknown_error", "An unknown error occurred."), "is_code_request": is_code_request}

def generate_request(user_input, category, language):
    """
    تبدیل ورودی کاربر به پرامپت مناسب بر اساس دسته‌بندی و زبان انتخاب شده
    """
    texts = TEXTS[language]
    system_instruction = texts["system_instruction"]
    patterns = texts["patterns"]

    max_retries = 2
    retry_delay = 5  # 5 ثانیه

    for attempt in range(max_retries):
        try:
            if category == "👨‍💻 Code / Dev":
                pattern = patterns[category]["simple"] if is_simple_task(user_input) else patterns[category]["complex"]
                instruction = pattern.format(user_input=user_input)
            elif category in patterns:
                instruction = patterns[category].format(user_input=user_input)
            else:
                instruction = patterns["❓ Other"].format(user_input=user_input)
            
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

            if response.status_code == 200:
                response_data = response.json()
                return response_data['choices'][0]['message']['content'].strip()
            elif response.status_code == 429:
                if attempt < max_retries - 1:
                    print(f"Rate limit hit in generate_request. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    return texts.get("rate_limit_error", "Rate limit exceeded. Please try again later.")
            else:
                print(f"API Error in generate_request: Status Code {response.status_code}, Response: {response.text}")
                return texts.get("api_server_error", "API server error.")

        except requests.exceptions.RequestException as e:
            print(f"Network Error in generate_request: {e}")
            if attempt < max_retries - 1:
                print(f"Network error. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                continue
            else:
                return texts.get("network_error", "Network error.")
        except Exception as e:
            print(f"An unexpected error occurred in generate_request: {e}")
            return texts.get("unknown_error", "An unknown error occurred.")

    return texts.get("unknown_error", "An unknown error occurred.")

if __name__ == '__main__':
    # --- تغییرات مربوط به دیتابیس ---
    # ابتدا جدول دیتابیس را ایجاد یا بررسی کن
    try:
        init_db()
    except Exception as e:
        print(f"Fatal: Could not initialize database. Exiting. Error: {e}")
        exit() # اگر دیتابیس آماده نباشد، برنامه نباید اجرا شود

    # اجرای ربات در یک Thread جداگانه
    bot_thread = Thread(target=run_bot)
    bot_thread.start()
    
    # اجرای وب سرور Flask
    # Render به طور خودکار پورت را از طریق متغیرهای محیطی مشخص می‌کند
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
