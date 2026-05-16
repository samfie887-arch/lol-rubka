from rubka.asynco import Robot
from rubka.context import Message
from rubka.keypad import ChatKeypadBuilder
from rubka import filters
import asyncio
import json
import os
from datetime import datetime, timedelta
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")


def start_health_server(port):
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    server.serve_forever()


bot = Robot(
    token="BEAEBI0EPGCAIGSPCKEZYQLJAXCAVBGDQEPTLQJPTMXMLDUPNYHFBBPBJJHCJOZQ")

ADMIN_ID = "MeTube_admin"
ADMIN_USERNAMES = ["admin", "sand"]

OFFICIAL_CHANNELS = [
    {
        "id": "BAGEEBIIH0UWDUTZOGSYKCKZKCJDSGSX",
        "link": "https://rubika.ir/joinc/FAEDCCBE0ONPMHSKHJEKIYUAYIBQIDPE",
        "name": "کانال اصلی"
    },
    {
        "id": "EJJCDEGC0TAOCRHJZQGPDRBYEYKILRBA",
        "link": "https://rubika.ir/joinc/EJJCDEGC0TAOCRHJZQGPDRBYEYKILRBA",
        "name": "کانال زاپاس"
    },
    {
        "id": "BAGEEBIIH0UWDUTZOGSYKCKZKCJDSGSX",
        "link": "https://rubika.ir/joing/BAGEEBIIH0UWDUTZOGSYKCKZKCJDSGSX",
        "name": "کانال عمومی"
    }
]

user_states = {}
user_usernames = {}
admin_states = {}
register_states = {}
purchase_states = {}
request_states = {}
report_states = {}
selected_video = {}
subscription_data = {}
user_rubika_ids = {}
pending_rubika_id_request = {}
edit_rubika_states = {}

CARD_NUMBER = "6037-9981-9248-4904"
CARD_HOLDER = "درسا حیدری"
DB_FILE = "video_shop_database.json"

SUBSCRIPTION_PLANS = {
    "plan_1": {
        "id": "plan_1",
        "name": "🥉 اشتراک یک ماهه",
        "duration": "۳۰ روز",
        "price": 119000,
        "price_display": "119,000 تومان",
        "description": "▫️ دسترسی کامل به تمام ویدیوها\n▫️ مدت زمان: ۳۰ روز\n▫️ مناسب برای تست و شروع"
    },
    "plan_2": {
        "id": "plan_2",
        "name": "🥈 اشتراک دو ماهه",
        "duration": "۶۰ روز",
        "price": 220000,
        "price_display": "220,000 تومان",
        "description": "▫️ دسترسی کامل به تمام ویدیوها\n▫️ مدت زمان: ۶۰ روز\n▫️ صرفه‌جویی ۱۵٪ نسبت به ماهانه"
    },
    "plan_3": {
        "id": "plan_3",
        "name": "🥇 اشتراک سه ماهه",
        "duration": "۹۰ روز",
        "price": 438000,
        "price_display": "438,000 تومان",
        "description": "▫️ دسترسی کامل به تمام ویدیوها\n▫️ مدت زمان: ۹۰ روز\n▫️ بهترین ارزش خرید ✨"
    }
}


VIDEOS = {}


def check_subscription_active(chat_id: str) -> bool:
    """بررسی فعال بودن اشتراک کاربر"""
    chat_id = str(chat_id)

    if chat_id not in subscription_data:
        return False

    expiry = subscription_data[chat_id].get("expiry_date")
    if not expiry:
        return False

    try:
        expiry_date = datetime.strptime(expiry, "%Y/%m/%d %H:%M")
        return datetime.now() < expiry_date
    except:
        return False


def get_subscription_info(chat_id: str) -> str:
    """دریافت اطلاعات اشتراک کاربر"""
    chat_id = str(chat_id)

    if chat_id not in subscription_data:
        return "❌ اشتراک فعالی ندارید!"

    data = subscription_data[chat_id]
    expiry = data.get("expiry_date", "")
    plan_name = data.get("plan_name", "")

    if not check_subscription_active(chat_id):
        return "⏰ اشتراک شما به پایان رسیده است!"

    try:
        expiry_date = datetime.strptime(expiry, "%Y/%m/%d %H:%M")
        remaining = expiry_date - datetime.now()
        days_left = remaining.days

        return f"""🎯 **وضعیت اشتراک شما:**

📦 پلن: {plan_name}
📅 تاریخ پایان: {expiry}
⏳ روزهای باقی‌مانده: {days_left} روز

✨ با تشکر از همراهی شما!"""
    except:
        return "❌ خطا در خواندن اطلاعات اشتراک!"


def has_registered_rubika_id(chat_id: str) -> bool:
    """بررسی اینکه کاربر قبلاً ایدی روبیکا ثبت کرده یا نه"""
    return str(chat_id) in user_rubika_ids


def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for key in ["pending_payments", "transactions", "user_requests", "sent_messages", "reports"]:
                if key not in data:
                    data[key] = []
            if "videos" not in data:
                data["videos"] = VIDEOS
            if "subscriptions" not in data:
                data["subscriptions"] = {}
            if "user_rubika_ids" not in data:
                data["user_rubika_ids"] = {}
            return data
    return {"users": {"ali": "1234", "zahra": "5678", "admin": "admin123", "sand": "1122"}, "pending_payments": [], "transactions": [], "user_requests": [], "sent_messages": [], "reports": [], "videos": VIDEOS, "subscriptions": {}, "user_rubika_ids": {}}


def save_data(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


db = load_data()
subscription_data = db.get("subscriptions", {})
user_rubika_ids = db.get("user_rubika_ids", {})


def is_admin_user(username):
    return username.lower() in [a.lower() for a in ADMIN_USERNAMES]

# ===== کیبردها =====


def kilid_main():
    return ChatKeypadBuilder().row(
        ChatKeypadBuilder().button(id="register", text="✨ عضویت در بات"),
        ChatKeypadBuilder().button(id="login", text="🔐 ورود به حساب")
    ).row(
        ChatKeypadBuilder().button(id="help", text="📚 راهنمای جامع"),
        ChatKeypadBuilder().button(id="our_channels", text="📢 کانال‌های ما")
    ).build()


def kilid_user_panel():
    return ChatKeypadBuilder().row(
        ChatKeypadBuilder().button(id="user_video_list", text="🎬 لیست ویدیوها"),
        ChatKeypadBuilder().button(id="subscription_menu", text="⭐ خرید اشتراک ویژه")
    ).row(
        ChatKeypadBuilder().button(id="my_subscription", text="📊 وضعیت اشتراک"),
        ChatKeypadBuilder().button(id="our_channels", text="📢 کانال‌های ما")
    ).row(
        ChatKeypadBuilder().button(id="video_request", text="📥 درخواست ویدیو"),
        ChatKeypadBuilder().button(id="report_problem", text="⚠️ گزارش مشکل")
    ).row(
        ChatKeypadBuilder().button(id="edit_rubika_id", text="✏️ ویرایش ایدی روبیکا")
    ).row(
        ChatKeypadBuilder().button(id="logout", text="🚪 خروج")
    ).build()


def kilid_admin_panel():
    return ChatKeypadBuilder().row(
        ChatKeypadBuilder().button(id="admin_video_list", text="🎬 مدیریت ویدیوها"),
        ChatKeypadBuilder().button(id="admin_subscriptions", text="👥 اشتراک‌های فعال")
    ).row(
        ChatKeypadBuilder().button(id="admin_pending", text="💳 تأیید پرداخت‌ها"),
        ChatKeypadBuilder().button(id="admin_requests", text="📨 صندوق درخواست‌ها")
    ).row(
        ChatKeypadBuilder().button(id="admin_manage_videos", text="🎥 ویرایش ویدیوها"),
        ChatKeypadBuilder().button(id="admin_rubika_ids", text="🆔 ایدی‌های روبیکا")
    ).row(
        ChatKeypadBuilder().button(id="admin_reports", text="📋 گزارش‌ها"),
        ChatKeypadBuilder().button(id="admin_send_message", text="💬 پیام به کاربر")
    ).row(
        ChatKeypadBuilder().button(id="admin_revenue_report", text="💰 گزارش مالی")
    ).row(
        ChatKeypadBuilder().button(id="admin_expired_subscriptions",
                                   text="⏰ اشتراک‌های منقضی شده")
    ).row(
        ChatKeypadBuilder().button(id="our_channels", text="📢 کانال‌های ما"),
        ChatKeypadBuilder().button(id="logout", text="🚪 خروج")
    ).build()


def kilid_subscription_plans():
    kilid = ChatKeypadBuilder()
    for plan in SUBSCRIPTION_PLANS.values():
        kilid.row(ChatKeypadBuilder().button(
            id=f"plan_{plan['id']}", text=f"{plan['name']} - {plan['price_display']}"))
    kilid.row(ChatKeypadBuilder().button(id="back_to_panel", text="🔙 بازگشت"))
    return kilid.build()


def kilid_video_list():
    kilid = ChatKeypadBuilder()
    videos = db.get("videos", VIDEOS)
    if not videos:
        kilid.row(ChatKeypadBuilder().button(
            id="nothing", text="📭 ویدیویی موجود نیست"))
    else:
        for video in videos.values():
            kilid.row(ChatKeypadBuilder().button(
                id=f"vid_{video['id']}",
                text=f"vid_{video['id']} 🎬 {video['title']}"
            ))
    kilid.row(ChatKeypadBuilder().button(id="back_to_panel", text="🔙 بازگشت"))
    return kilid.build()


def kilid_video_selected():
    return ChatKeypadBuilder().row(
        ChatKeypadBuilder().button(id="buy_subscription", text="⭐ خرید اشتراک")
    ).row(
        ChatKeypadBuilder().button(id="back_to_video_list", text="🔙 لیست ویدیوها")
    ).build()


def kilid_after_card():
    return ChatKeypadBuilder().row(
        ChatKeypadBuilder().button(id="payment_done", text="✅ پرداخت انجام شد")
    ).row(
        ChatKeypadBuilder().button(id="cancel_purchase", text="🔙 انصراف")
    ).build()


def kilid_payment_verification():
    return ChatKeypadBuilder().row(
        ChatKeypadBuilder().button(id="admin_verify_submit", text="✅ تأیید و فعال‌سازی"),
        ChatKeypadBuilder().button(id="admin_reject_submit", text="❌ رد پرداخت")
    ).row(
        ChatKeypadBuilder().button(id="back_to_pending_list", text="🔙 لیست پرداخت‌ها")
    ).build()


def kilid_pending_users_keyboard():
    kilid = ChatKeypadBuilder()
    pending = db.get("pending_payments", [])

    unique_users = {}
    for p in pending:
        username = p.get("username", "").strip()
        if username:
            if username not in unique_users:
                unique_users[username] = 1
            else:
                unique_users[username] += 1

    if not unique_users:
        kilid.row(ChatKeypadBuilder().button(
            id="nothing", text="📭 پرداخت در انتظاری نیست"))
    else:
        for username, count in unique_users.items():
            kilid.row(ChatKeypadBuilder().button(
                id=f"pending_user_{username}", text=f"👤 {username} ({count} پرداخت)"))

    kilid.row(ChatKeypadBuilder().button(id="back_to_panel", text="🔙 بازگشت"))
    return kilid.build()


def kilid_admin_video_management():
    """ویرایش شد: حذف admvid_ از متن دکمه‌ها"""
    kilid = ChatKeypadBuilder()
    videos = db.get("videos", VIDEOS)
    if videos:
        for video in videos.values():
            # فقط عنوان ویدیو با علامت ⚙️ نمایش داده می‌شود
            kilid.row(ChatKeypadBuilder().button(
                id=f"admvid_{video['id']}",
                text=f"⚙️ {video['title']}"
            ))
    kilid.row(ChatKeypadBuilder().button(
        id="admin_add_video", text="➕ افزودن ویدیو جدید"))
    kilid.row(ChatKeypadBuilder().button(id="back_to_panel", text="🔙 بازگشت"))
    return kilid.build()


def kilid_video_edit_options(video_id):
    return ChatKeypadBuilder().row(
        ChatKeypadBuilder().button(id=f"edit_{video_id}", text="✏️ ویرایش"),
        ChatKeypadBuilder().button(id=f"delete_{video_id}", text="🗑 حذف")
    ).row(
        ChatKeypadBuilder().button(id="back_to_manage", text="🔙 بازگشت")
    ).build()


def kilid_edit_details(video_id):
    return ChatKeypadBuilder().row(
        ChatKeypadBuilder().button(
            id=f"edt_title_{video_id}", text="✏️ عنوان"),
        ChatKeypadBuilder().button(id=f"edt_desc_{video_id}", text="📝 توضیحات")
    ).row(
        ChatKeypadBuilder().button(
            id=f"edt_duration_{video_id}", text="⏱ مدت"),
        ChatKeypadBuilder().button(id=f"edt_price_{video_id}", text="💰 قیمت")
    ).row(
        ChatKeypadBuilder().button(id="back_to_manage", text="🔙 بازگشت")
    ).build()


def kilid_users_list():
    kilid = ChatKeypadBuilder()
    all_users = db.get("users", {})
    normal_users = [u for u in all_users.keys() if not is_admin_user(u)]

    if not normal_users:
        kilid.row(ChatKeypadBuilder().button(
            id="nothing", text="📭 کاربری یافت نشد"))
    else:
        for username in normal_users[:20]:
            kilid.row(ChatKeypadBuilder().button(
                id=f"msg_{username}", text=f"👤 {username}"))
    kilid.row(ChatKeypadBuilder().button(id="back_to_panel", text="🔙 بازگشت"))
    return kilid.build()


def kilid_rubika_id_request():
    return ChatKeypadBuilder().row(
        ChatKeypadBuilder().button(id="send_rubika_id", text="📱 ارسال ایدی روبیکا")
    ).row(
        ChatKeypadBuilder().button(id="back_to_panel", text="🔙 بازگشت به منو")
    ).build()


def kilid_pending_payments_for_user(username):
    kilid = ChatKeypadBuilder()
    pending = db.get("pending_payments", [])
    user_payments = [p for p in pending if p.get(
        "username", "").strip() == username.strip()]

    for p in user_payments:
        pid = p.get("payment_id", "")
        plan_name = p.get("plan_name", "")
        amount = p.get("amount", 0)
        kilid.row(ChatKeypadBuilder().button(
            id=f"select_payment_{pid}",
            text=f"payment_{pid} 🔖 {plan_name} - {amount:,} تومان"
        ))

    kilid.row(ChatKeypadBuilder().button(
        id="back_to_pending_list", text="🔙 لیست کاربران"))
    return kilid.build()


def kilid_cancel_edit_rubika():
    return ChatKeypadBuilder().row(
        ChatKeypadBuilder().button(id="cancel_edit_rubika", text="🔙 انصراف")
    ).build()


@bot.on_message(commands=["start"])
async def start_bot(bot: Robot, message: Message):
    chat_id = message.chat_id
    for d in [user_states, admin_states, register_states, purchase_states, request_states, report_states, selected_video, pending_rubika_id_request, edit_rubika_states]:
        d.pop(chat_id, None)

    current_username = user_usernames.get(chat_id)

    if chat_id == ADMIN_ID or (current_username and is_admin_user(current_username)):
        await message.reply(
            "🎩 **پنل مدیریت**\n\n"
            "درود بر مدیر گرامی! 🌟\n"
            "از این بخش می‌توانید ربات را مدیریت کنید.",
            chat_keypad=kilid_admin_panel(), chat_keypad_type="New"
        )
    elif current_username:
        if has_registered_rubika_id(chat_id):
            welcome_msg = f"👋 سلام {current_username} جان! خوشحالیم که برگشتی ☺️\n\n🎯 چطور می‌تونم کمکت کنم؟"
        else:
            welcome_msg = f"👋 سلام {current_username} جان! خوشحالیم که برگشتی ☺️\n\n⚠️ **توجه:** شما هنوز ایدی روبیکای خود را ثبت نکرده‌اید!\n📱 لطفاً برای ثبت، از دکمه زیر استفاده کنید.\n\n🎯 چطور می‌تونم کمکت کنم؟"

        await message.reply(
            welcome_msg,
            chat_keypad=kilid_user_panel(), chat_keypad_type="New"
        )
    else:
        await message.reply(
            "🌟 **به بات ویدیو یوتیوب خوش آمدید!** 🌟\n\n"
            "🎬 این بات به خاطر دوران جنگی و محدودیت‌های موجود، ویدیوهای فان و سرگرم‌کننده ✨ یوتیوب رو براتون فراهم کرده 💎\n\n"
            "📥 برای شروع یکی از گزینه‌های زیر رو انتخاب کنید (اول راهنما رو بخونید بعد شروع کنید 📚):",
            chat_keypad=kilid_main(), chat_keypad_type="New"
        )


@bot.on_message(filters=None)
async def handle_all_messages(robot: Robot, message: Message):
    chat_id = message.chat_id
    text = message.text.strip() if message.text else ""

    current_username = user_usernames.get(chat_id)
    is_admin = (chat_id == ADMIN_ID) or (
        current_username and is_admin_user(current_username))

    # ----- admin expired subscriptions -----
    if is_admin and text in ["admin_expired_subscriptions", "⏰ اشتراک‌های منقضی شده"]:
        admin_states.pop(chat_id, None)
        expired = {}
        for cid, data in subscription_data.items():
            if not check_subscription_active(cid):
                expired[cid] = data

        if not expired:
            await message.reply("✅ هیچ اشتراک منقضی‌شده‌ای وجود ندارد!")
            return

        msg = "⏰ **لیست اشتراک‌های منقضی شده:**\n\n"
        for cid, data in expired.items():
            username = data.get("username", "ناشناس")
            rubika_id = user_rubika_ids.get(str(cid), "❌ ثبت نشده")
            expiry = data.get("expiry_date", "نامشخص")
            msg += f"👤 {username}\n🆔 روبیکا: {rubika_id}\n📅 پایان: {expiry}\n▬▬▬▬▬▬▬▬▬▬\n"
        await message.reply(msg)
        return

    # ----- user edit rubika id -----
    if not is_admin and text in ["edit_rubika_id", "✏️ ویرایش ایدی روبیکا"]:
        if not current_username:
            await message.reply("🔒 ابتدا باید وارد حساب خود شوید!")
            return
        if not has_registered_rubika_id(chat_id):
            await message.reply(
                "⚠️ شما هنوز ایدی روبیکایی ثبت نکرده‌اید!\n"
                "ابتدا با استفاده از دکمه «ارسال ایدی روبیکا» ایدی خود را ثبت کنید.",
                chat_keypad=kilid_rubika_id_request(),
                chat_keypad_type="New"
            )
            return

        edit_rubika_states[chat_id] = "waiting_new_rubika_id"
        current_id = user_rubika_ids[str(chat_id)]
        await message.reply(
            f"✏️ **ویرایش ایدی روبیکا**\n\n"
            f"🆔 ایدی فعلی: `{current_id}`\n\n"
            f"⚠️ **توجه بسیار مهم:**\n"
            f"تنها **یک ایدی** از شما وارد کانال ویژه می‌شود.\n"
            f"اگر قبلاً با این ایدی (`{current_id}`) عضو کانال شده‌اید،\n"
            f"با ایدی جدید **دیگر نمی‌توانید** دوباره اد شوید!\n\n"
            f"🔹 اما در صورت بروز مشکل، ادمین می‌تواند ایدی قبلی را حذف\n"
            f"و ایدی جدید شما را جایگزین کند.\n\n"
            f"📝 لطفاً ایدی جدید خود را با @ وارد کنید\n"
            f"یا از دکمه زیر برای انصراف استفاده کنید:",
            chat_keypad=kilid_cancel_edit_rubika(),
            chat_keypad_type="New"
        )
        return

    # handling the new rubika id during edit
    if not is_admin and chat_id in edit_rubika_states and edit_rubika_states[chat_id] == "waiting_new_rubika_id":
        if text.strip() in ["/cancel", "cancel_edit_rubika", "🔙 انصراف"]:
            edit_rubika_states.pop(chat_id, None)
            await message.reply("🚫 ویرایش لغو شد.", chat_keypad=kilid_user_panel(), chat_keypad_type="New")
            return

        new_id = text.strip()
        if not new_id.startswith("@") or len(new_id) < 3:
            await message.reply(
                "❌ ایدی باید با @ شروع شود و حداقل ۳ کاراکتر باشد.\n"
                "مثال: `@username`\n"
                "📝 لطفاً دوباره وارد کنید یا از دکمه انصراف استفاده کنید:",
                chat_keypad=kilid_cancel_edit_rubika()
            )
            return

        old_id = user_rubika_ids.get(str(chat_id), "")
        user_rubika_ids[str(chat_id)] = new_id
        db["user_rubika_ids"] = user_rubika_ids
        save_data(db)
        edit_rubika_states.pop(chat_id, None)

        await message.reply(
            f"✅ **ایدی روبیکای شما با موفقیت به‌روزرسانی شد!**\n\n"
            f"🔄 قبلی: `{old_id}`\n"
            f"🆕 جدید: `{new_id}`\n\n"
            f"⚠️ به یاد داشته باشید که ادمین باید ایدی جدید را بررسی کند\n"
            f"و در صورت نیاز، ایدی قبلی را از کانال حذف و ایدی جدید را اضافه کند.",
            chat_keypad=kilid_user_panel(),
            chat_keypad_type="New"
        )
        try:
            await robot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔄 **تغییر ایدی روبیکا**\n"
                f"👤 کاربر: {current_username}\n"
                f"🆔 قبلی: `{old_id}`\n"
                f"🆕 جدید: `{new_id}`\n"
                f"📅 زمان: {datetime.now().strftime('%Y/%m/%d %H:%M')}"
            )
        except Exception as e:
            print(f"Error notifying admin about rubika ID edit: {e}")
        return

    # ===== نمایش ایدی‌های روبیکا برای ادمین =====
    if is_admin and text in ["admin_rubika_ids", "🆔 ایدی‌های روبیکا"]:
        admin_states.pop(chat_id, None)
        if not user_rubika_ids:
            await message.reply("📭 هیچ ایدی روبیکایی ثبت نشده است!")
            return

        msg = "🆔 **لیست ایدی‌های روبیکای ثبت شده:**\n\n"
        for i, (cid, rubika_id) in enumerate(user_rubika_ids.items(), 1):
            username = "ناشناس"
            for uchat, uname in user_usernames.items():
                if str(uchat) == str(cid):
                    username = uname
                    break
            for sub_cid, sub_data in subscription_data.items():
                if str(sub_cid) == str(cid):
                    username = sub_data.get("username", username)
                    break

            msg += f"{i}️⃣ 👤 کاربر: {username}\n🆔 ایدی روبیکا: {rubika_id}\n▬▬▬▬▬▬▬▬▬▬\n"

        await message.reply(msg)
        return

    # ===== کلیک روی دکمه "ارسال ایدی روبیکا" =====
    if text == "send_rubika_id" or text == "📱 ارسال ایدی روبیکا":
        if not current_username:
            await message.reply("🔒 ابتدا باید وارد حساب خود شوید!")
            return

        if has_registered_rubika_id(chat_id):
            await message.reply(
                f"✅ شما قبلاً ایدی روبیکای خود را ثبت کرده‌اید:\n"
                f"🆔 `{user_rubika_ids[str(chat_id)]}`\n\n"
                f"⚠️ هر کاربر فقط یک بار می‌تواند ایدی ثبت کند.",
                chat_keypad=kilid_user_panel() if not is_admin else kilid_admin_panel(),
                chat_keypad_type="New"
            )
            return

        pending_rubika_id_request[chat_id] = True
        await message.reply(
            "📱 **ثبت ایدی روبیکا**\n\n"
            "⚠️ **نکات بسیار مهم:**\n"
            "• ایدی باید حتماً با **@** شروع شود\n"
            "• مثال درست: `@username`\n"
            "• ادمین با همین ایدی شما را به کانال ویژه اضافه می‌کند\n"
            "• **از درستی ایدی خود مطمئن شوید!**\n"
            "• در صورت اشتباه بودن، امکان عضویت در کانال را از دست می‌دهید\n\n"
            "📝 لطفاً ایدی روبیکای خود را دقیقاً وارد کنید:"
        )
        return

    # ===== دریافت ایدی روبیکا از کاربر (فقط وقتی درخواست شده) =====
    if current_username and not is_admin and chat_id in pending_rubika_id_request:
        rubika_id = text.strip()

        if not rubika_id.startswith("@"):
            await message.reply(
                "❌ **ایدی نامعتبر!**\n\n"
                "ایدی روبیکا باید حتماً با **@** شروع شود.\n"
                "مثال درست: `@username`\n\n"
                "📝 لطفاً مجدداً تلاش کنید:"
            )
            return

        if len(rubika_id) < 3:
            await message.reply(
                "❌ **ایدی خیلی کوتاه است!**\n\n"
                "لطفاً یک ایدی معتبر وارد کنید.\n"
                "مثال: `@username`"
            )
            return

        user_rubika_ids[str(chat_id)] = rubika_id
        db["user_rubika_ids"] = user_rubika_ids
        save_data(db)

        pending_rubika_id_request.pop(chat_id, None)

        await message.reply(
            f"✅ **ایدی روبیکای شما با موفقیت ثبت شد!**\n\n"
            f"🆔 ایدی: `{rubika_id}`\n\n"
            f"🔔 ادمین به زودی شما را با این ایدی به کانال ویژه اضافه خواهد کرد.\n"
            f"🙏 از صبر شما متشکریم!",
            chat_keypad=kilid_user_panel(),
            chat_keypad_type="New"
        )

        try:
            await robot.send_message(
                chat_id=ADMIN_ID,
                text=f"🆔 **ایدی روبیکا جدید ثبت شد**\n\n"
                f"👤 کاربر: {current_username}\n"
                f"🆔 ایدی: `{rubika_id}`\n"
                f"📅 تاریخ: {datetime.now().strftime('%Y/%m/%d %H:%M')}"
            )
        except Exception as e:
            print(f"Error notifying admin about rubika ID: {e}")
        return

    # ===== کانال‌های ما =====
    if text in ["our_channels", "📢 کانال‌های ما"]:
        admin_states.pop(chat_id, None)
        channels_text = ""
        for ch in OFFICIAL_CHANNELS:
            channels_text += f"📢 {ch['name']}\n🔗 {ch['link']}\n\n"
        await message.reply(
            f"📢 **کانال‌های رسمی ما**\n\n"
            f"برای اطلاع از جدیدترین ویدیوها و اخبار، در کانال‌های ما عضو شوید:\n\n"
            f"{channels_text}"
            f"✨ با عضویت در کانال‌ها، از تمام اطلاعیه‌های مهم باخبر می‌شوید.",
            chat_keypad=kilid_main() if not current_username else (
                kilid_admin_panel() if is_admin else kilid_user_panel()),
            chat_keypad_type="New"
        )
        return

    # ===== راهنما =====
    if text in ["help", "📚 راهنمای جامع"]:
        admin_states.pop(chat_id, None)
        channels_text = ""
        for ch in OFFICIAL_CHANNELS:
            channels_text += f"📢 {ch['name']}\n🔗 {ch['link']}\n\n"
        await message.reply(
            "📚 **راهنمای استفاده از بات** 📚\n\n"
            "1️⃣ ابتدا در بات عضو شوید یا وارد حساب خود گردید\n\n"
            "2️⃣ برای دسترسی به ویدیوها، اشتراک تهیه کنید\n"
            "   • یک ماهه: 119 هزار تومان\n"
            "   • دو ماهه: 22۰ هزار تومان\n"
            "   • سه ماهه: 438 هزار تومان\n\n"
            "3️⃣ بعد از خرید، حتماً ایدی روبیکای خود را با **@** ثبت کنید\n"
            "   • ادمین شما را با همین ایدی به کانال ویژه اضافه می‌کند\n"
            "   • از درستی ایدی خود مطمئن شوید!\n\n"
            "4️⃣ حتماً کانال‌های رسمی ما رو چک کنید تا از جدیدترین ویدیوها باخبر بشید 📢\n\n"
            f"🔗 **کانال‌های رسمی:**\n{channels_text}"
            "\n❓ سوالی دارید؟ با بخش گزارش مشکل در میان بگذارید 🙏\n\n"
            f"ایدی ادمین : @{ADMIN_ID}"
        )
        return

    # ===== منوی اشتراک =====
    if text in ["subscription_menu", "⭐ خرید اشتراک ویژه", "buy_subscription", "⭐ خرید اشتراک"]:
        admin_states.pop(chat_id, None)
        if not current_username:
            await message.reply("🔒 ابتدا باید وارد حساب خود شوید!")
            return

        plans_text = "⭐ **پلن‌های اشتراک ویژه** ⭐\n\n"
        plans_text += "با خرید اشتراک، به تمام ویدیوهای فان و سرگرم‌کننده دسترسی کامل پیدا می‌کنید!\n\n"
        for plan in SUBSCRIPTION_PLANS.values():
            plans_text += f"{plan['name']}\n💰 قیمت: {plan['price_display']}\n📅 مدت: {plan['duration']}\n📝 {plan['description']}\n\n▬▬▬▬▬▬▬▬▬▬\n\n"
        plans_text += "👇 برای خرید، یکی از پلن‌های زیر را انتخاب کنید:"
        await message.reply(plans_text, chat_keypad=kilid_subscription_plans(), chat_keypad_type="New")
        return

    # ===== انتخاب پلن =====
    for plan_id, plan in SUBSCRIPTION_PLANS.items():
        if text == f"plan_{plan['id']}" or text.startswith(plan['name']):
            admin_states.pop(chat_id, None)
            if not current_username:
                await message.reply("🔒 ابتدا باید وارد حساب خود شوید!")
                return
            purchase_states[chat_id] = "waiting_card"
            purchase_states[f"{chat_id}_plan_id"] = plan["id"]
            purchase_states[f"{chat_id}_plan_name"] = plan["name"]
            purchase_states[f"{chat_id}_plan_price"] = plan["price"]
            purchase_states[f"{chat_id}_plan_duration"] = plan["duration"]

            await message.reply(
                f"🛒 **خرید اشتراک**\n\n"
                f"📦 پلن: {plan['name']}\n"
                f"💰 مبلغ: {plan['price_display']}\n"
                f"📅 مدت: {plan['duration']}\n\n"
                f"💳 **اطلاعات کارت مقصد:**\n"
                f"🔢 شماره کارت: \n`{CARD_NUMBER}`\n"
                f"👤 به نام: {CARD_HOLDER}\n\n"
                f"📱 لطفاً شماره کارت خود را جهت پیگیری وارد کنید:"
            )
            return

    # ===== وضعیت اشتراک =====
    if text in ["my_subscription", "📊 وضعیت اشتراک"]:
        admin_states.pop(chat_id, None)
        if not current_username:
            await message.reply("🔒 ابتدا باید وارد حساب خود شوید!")
            return

        sub_info = get_subscription_info(chat_id)

        if check_subscription_active(chat_id) and not has_registered_rubika_id(chat_id):
            sub_info += "\n\n⚠️ **توجه:** شما هنوز ایدی روبیکای خود را ثبت نکرده‌اید!\n📱 لطفاً با کلیک روی دکمه زیر ایدی خود را ارسال کنید."
            await message.reply(sub_info, chat_keypad=kilid_rubika_id_request(), chat_keypad_type="New")
        else:
            await message.reply(sub_info)
        return

    # ===== مدیریت اشتراک‌ها برای ادمین =====
    if is_admin and text in ["admin_subscriptions", "👥 اشتراک‌های فعال"]:
        admin_states.pop(chat_id, None)
        if not subscription_data:
            await message.reply("📭 هیچ اشتراک فعالی وجود ندارد!")
            return
        msg = "👥 **لیست اشتراک‌های فعال:**\n\n"
        for chat_id_key, sub_data in subscription_data.items():
            is_active = check_subscription_active(chat_id_key)
            status = "✅ فعال" if is_active else "⏰ منقضی شده"
            username = sub_data.get("username", "ناشناس")
            rubika_id = user_rubika_ids.get(chat_id_key, "❌ ثبت نشده")
            msg += f"👤 {username}\n🆔 ایدی روبیکا: {rubika_id}\n📦 {sub_data.get('plan_name', '')}\n📅 پایان: {sub_data.get('expiry_date', '')}\n📊 {status}\n▬▬▬▬▬▬▬▬▬▬\n"
        await message.reply(msg)
        return

    # ===== پنل ادمین - ارسال پیام به کاربر =====
    if is_admin and text in ["admin_send_message", "💬 پیام به کاربر"]:
        admin_states.pop(chat_id, None)
        admin_states[chat_id] = "waiting_for_user_selection"
        await message.reply(
            "💬 **ارسال پیام به کاربر**\n\n"
            "👤 کاربر مورد نظر را از لیست زیر انتخاب کنید:",
            chat_keypad=kilid_users_list(), chat_keypad_type="New"
        )
        return

    # ===== کلیک روی کاربر برای ارسال پیام =====
    if is_admin and text.startswith("👤 ") and admin_states.get(chat_id) == "waiting_for_user_selection":
        target_username = text.replace("👤 ", "")
        if target_username in db["users"] and not is_admin_user(target_username):
            admin_states[chat_id] = "sending_free_message_text"
            admin_states["target_username"] = target_username
            target_chat_id = next(
                (c for c, u in user_usernames.items() if u == target_username), None)
            admin_states["target_chat_id"] = target_chat_id
            await message.reply(f"💬 پیام خود را برای **{target_username}** بنویسید:")
        return

    # ===== ارسال متن پیام =====
    if is_admin and chat_id in admin_states and admin_states[chat_id] == "sending_free_message_text":
        msg_text = text
        target_chat_id = admin_states.get("target_chat_id")
        target_username = admin_states.get("target_username", "")
        db["sent_messages"].append({
            "username": target_username,
            "message": msg_text,
            "date": datetime.now().strftime("%Y/%m/%d %H:%M")
        })
        save_data(db)
        if target_chat_id:
            try:
                await robot.send_message(chat_id=target_chat_id, text=f"💬 **پیام از طرف ادمین:**\n\n{msg_text}")
            except:
                pass
        admin_states.pop(chat_id, None)
        await message.reply(
            f"✅ پیام با موفقیت به **{target_username}** ارسال شد!",
            chat_keypad=kilid_admin_panel(),
            chat_keypad_type="New"
        )
        return

    # ===== پنل تأیید پرداخت‌ها - نمایش کیبرد کاربران =====
    if is_admin and text in ["admin_pending", "💳 تأیید پرداخت‌ها", "back_to_pending_list", "🔙 لیست پرداخت‌ها"]:
        admin_states.pop(chat_id, None)
        pending = db.get("pending_payments", [])
        if not pending:
            await message.reply("✅ هیچ پرداخت در انتظار تأییدی وجود ندارد!")
            return

        unique_users = {}
        for p in pending:
            u = p.get("username", "").strip()
            if u:
                unique_users[u] = unique_users.get(u, 0) + 1

        msg = f"💳 **لیست کاربران با پرداخت در انتظار**\n\n"
        msg += f"📊 تعداد کاربران: {len(unique_users)}\n"
        msg += f"📊 تعداد کل پرداخت‌ها: {len(pending)}\n\n"
        msg += "👤 کاربر مورد نظر را از لیست زیر انتخاب کنید:"

        await message.reply(msg, chat_keypad=kilid_pending_users_keyboard(), chat_keypad_type="New")
        return

    # ===== انتخاب کاربر از لیست پرداخت‌ها =====
    if is_admin and (text.startswith("pending_user_") or (text.startswith("👤 ") and "پرداخت" in text)):
        if text.startswith("pending_user_"):
            target_username = text.replace("pending_user_", "").strip()
        else:
            target_username = text.split(" (")[0].replace("👤 ", "").strip()

        pending = db.get("pending_payments", [])
        user_payments = [p for p in pending if p.get(
            "username", "").strip() == target_username]

        if not user_payments:
            await message.reply("❌ هیچ پرداخت در انتظاری برای این کاربر یافت نشد!")
            return

        admin_states["selected_payment_username"] = target_username

        if len(user_payments) == 1:
            payment = user_payments[0]
            admin_states["selected_payment_id"] = payment["payment_id"]
            admin_states[chat_id] = "processing_payment"

            await message.reply(
                f"💳 **جزئیات پرداخت**\n\n"
                f"👤 کاربر: {payment['username']}\n"
                f"📦 پلن: {payment.get('plan_name', '')}\n"
                f"💰 مبلغ: {payment['amount']:,} تومان\n"
                f"📅 تاریخ: {payment['date']}\n"
                f"💳 کارت واریز‌کننده: \n{payment.get('card_number', '')}\n"
                f"👤 نام صاحب کارت: {payment.get('card_holder', 'نامشخص')}\n\n"
                f"⏬ یکی از گزینه‌های زیر را انتخاب کنید:",
                chat_keypad=kilid_payment_verification(),
                chat_keypad_type="New"
            )
        else:
            msg = f"💳 **{len(user_payments)} پرداخت در انتظار از {target_username}:**\n\n"
            for i, p in enumerate(user_payments, 1):
                msg += f"{i}️⃣ 📦 {p.get('plan_name', '')}\n💰 {p['amount']:,} تومان\n📅 {p['date']}\n▬▬▬▬▬▬▬▬▬▬\n"

            msg += "👇 پرداخت مورد نظر را از لیست زیر انتخاب کنید:"
            admin_states[chat_id] = "selecting_payment_from_list"
            await message.reply(msg, chat_keypad=kilid_pending_payments_for_user(target_username), chat_keypad_type="New")
        return

    # ===== انتخاب پرداخت از لیست =====
    if is_admin and admin_states.get(chat_id) == "selecting_payment_from_list":
        pid = None
        if text.startswith("payment_"):
            pid = text.split(" ")[0].replace("payment_", "")
        elif text.startswith("select_payment_"):
            pid = text.replace("select_payment_", "")

        if pid:
            pending = db.get("pending_payments", [])
            payment = next(
                (p for p in pending if p["payment_id"] == pid), None)

            if not payment:
                await message.reply("❌ پرداخت مورد نظر یافت نشد!")
                return

            admin_states["selected_payment_id"] = pid
            admin_states[chat_id] = "processing_payment"

            await message.reply(
                f"💳 **جزئیات پرداخت**\n\n"
                f"👤 کاربر: {payment['username']}\n"
                f"📦 پلن: {payment.get('plan_name', '')}\n"
                f"💰 مبلغ: {payment['amount']:,} تومان\n"
                f"📅 تاریخ: {payment['date']}\n"
                f"💳 کارت واریز‌کننده: \n{payment.get('card_number', '')}\n"
                f"👤 نام صاحب کارت: {payment.get('card_holder', 'نامشخص')}\n\n"
                f"⏬ یکی از گزینه‌های زیر را انتخاب کنید:",
                chat_keypad=kilid_payment_verification(),
                chat_keypad_type="New"
            )
        return

    # ===== تأیید پرداخت =====
    if is_admin and text in ["admin_verify_submit", "✅ تأیید و فعال‌سازی"]:
        pid = admin_states.get("selected_payment_id")
        if not pid:
            await message.reply("❌ ابتدا یک پرداخت را انتخاب کنید!")
            return

        payment = next(
            (p for p in db["pending_payments"] if p["payment_id"] == pid), None)
        if not payment:
            await message.reply("❌ پرداخت مورد نظر یافت نشد!")
            return

        db["pending_payments"].remove(payment)

        for t in db["transactions"]:
            if t.get("payment_id") == pid:
                t["status"] = "approved"
                break

        if payment.get("type") == "subscription":
            plan_duration = payment.get("duration", "")
            if "۳۰" in plan_duration:
                days = 30
            elif "۶۰" in plan_duration:
                days = 60
            elif "۹۰" in plan_duration:
                days = 90
            else:
                days = 30

            expiry = datetime.now().replace(hour=23, minute=59, second=59) + timedelta(days=days)

            user_chat_id = str(payment.get("chat_id", ""))

            subscription_data[user_chat_id] = {
                "username": payment.get("username", ""),
                "plan_name": payment.get("plan_name", ""),
                "plan_id": payment.get("plan_id", ""),
                "expiry_date": expiry.strftime("%Y/%m/%d %H:%M"),
                "payment_id": pid,
                "activated_date": datetime.now().strftime("%Y/%m/%d %H:%M")
            }
            db["subscriptions"] = subscription_data

            if str(user_chat_id) not in user_rubika_ids:
                auto_id = f"@{payment.get('username', 'unknown')}"
                user_rubika_ids[str(user_chat_id)] = auto_id
                db["user_rubika_ids"] = user_rubika_ids

            save_data(db)

        try:
            rubika_id = user_rubika_ids.get(
                str(payment['chat_id']), "ثبت نشده")

            await robot.send_message(
                chat_id=payment["chat_id"],
                text=f"🎉 **تبریک! اشتراک شما فعال شد**\n\n"
                f"📦 پلن: {payment.get('plan_name', '')}\n"
                f"📅 تاریخ پایان: {subscription_data.get(str(payment['chat_id']), {}).get('expiry_date', '')}\n\n"
                f"🆔 ایدی روبیکای شما: `{rubika_id}`\n"
                f"🔔 ادمین با این ایدی شما را به کانال ویژه اضافه خواهد کرد.\n\n"
                f"⚠️ اگر این ایدی اشتباه است، لطفاً از بخش ثبت ایدی روبیکا آن را اصلاح کنید."
            )
        except Exception as e:
            print(f"Error sending message: {e}")

        admin_states.pop(chat_id, None)

        pending = db.get("pending_payments", [])
        if pending:
            unique_users = {}
            for p in pending:
                u = p.get("username", "").strip()
                if u:
                    unique_users[u] = unique_users.get(u, 0) + 1
            msg = f"✅ پرداخت تأیید شد!\n\n💳 **لیست کاربران باقی‌مانده:**\n📊 {len(unique_users)} کاربر - {len(pending)} پرداخت\n\n👤 کاربر بعدی را انتخاب کنید:"
            await message.reply(msg, chat_keypad=kilid_pending_users_keyboard(), chat_keypad_type="New")
        else:
            await message.reply("✅ پرداخت تأیید شد!\n\n🎉 تمام پرداخت‌ها بررسی شدند.", chat_keypad=kilid_admin_panel(), chat_keypad_type="New")
        return

    # ===== رد پرداخت =====
    if is_admin and text in ["admin_reject_submit", "❌ رد پرداخت"]:
        pid = admin_states.get("selected_payment_id")
        if not pid:
            await message.reply("❌ ابتدا یک پرداخت را انتخاب کنید!")
            return

        payment = next(
            (p for p in db["pending_payments"] if p["payment_id"] == pid), None)
        if not payment:
            await message.reply("❌ پرداخت مورد نظر یافت نشد!")
            return

        db["pending_payments"].remove(payment)

        for t in db["transactions"]:
            if t.get("payment_id") == pid:
                t["status"] = "rejected"
                break

        save_data(db)

        try:
            await robot.send_message(
                chat_id=payment["chat_id"],
                text=f"❌ **پرداخت شما رد شد**\n\n"
                f"📦 پلن: {payment.get('plan_name', '')}\n"
                f"💰 مبلغ: {payment['amount']:,} تومان\n\n"
                f"⚠️ در صورت وجود مشکل، از بخش گزارش مشکل اقدام کنید."
            )
        except Exception as e:
            print(f"Error sending rejection message: {e}")

        admin_states.pop(chat_id, None)

        pending = db.get("pending_payments", [])
        if pending:
            unique_users = {}
            for p in pending:
                u = p.get("username", "").strip()
                if u:
                    unique_users[u] = unique_users.get(u, 0) + 1
            msg = f"❌ پرداخت رد شد!\n\n💳 **لیست کاربران باقی‌مانده:**\n📊 {len(unique_users)} کاربر - {len(pending)} پرداخت\n\n👤 کاربر بعدی را انتخاب کنید:"
            await message.reply(msg, chat_keypad=kilid_pending_users_keyboard(), chat_keypad_type="New")
        else:
            await message.reply("❌ پرداخت رد شد!\n\n🎉 تمام پرداخت‌ها بررسی شدند.", chat_keypad=kilid_admin_panel(), chat_keypad_type="New")
        return

    # ===== گزارش مالی =====
    if is_admin and text in ["admin_revenue_report", "💰 گزارش مالی"]:
        admin_states.pop(chat_id, None)
        approved = [t for t in db.get(
            "transactions", []) if t.get("status") == "approved"]
        if not approved:
            await message.reply("💰 درآمدی ثبت نشده است.")
            return

        total_amount = 0
        for t in approved:
            amount_str = t.get("amount", "0 تومان")
            amount_str = amount_str.replace(" تومان", "").replace(",", "")
            try:
                total_amount += int(amount_str)
            except:
                pass

        count = len(approved)
        await message.reply(
            f"💰 **گزارش مالی** 💰\n\n"
            f"🔢 تعداد فروش موفق: {count}\n"
            f"💵 مجموع درآمد: {total_amount:,} تومان"
        )
        return

    # ===== مدیریت ویدیوها توسط ادمین =====
    if is_admin and text in ["admin_manage_videos", "🎥 ویرایش ویدیوها"]:
        admin_states.pop(chat_id, None)
        await message.reply(
            "🎥 **مدیریت ویدیوها**\n\nبرای ویرایش یا حذف روی ویدیو کلیک کنید.",
            chat_keypad=kilid_admin_video_management(), chat_keypad_type="New"
        )
        return

    # ===== برگشت به پنل اصلی =====
    if text in ["back_to_panel", "🔙 بازگشت", "🔙 بازگشت به منو"]:
        for d in [purchase_states, request_states, report_states, admin_states, selected_video, pending_rubika_id_request, edit_rubika_states]:
            d.pop(chat_id, None)

        if is_admin:
            kb = kilid_admin_panel()
        elif current_username:
            kb = kilid_user_panel()
        else:
            kb = kilid_main()

        await message.reply("🔙 به منوی اصلی بازگشتید.", chat_keypad=kb, chat_keypad_type="New")
        return

    # ===== بازگشت از ادیت به لیست مدیریت ویدیوها =====
    if is_admin and text in ["back_to_manage"]:
        admin_states.pop(chat_id, None)
        await message.reply(
            "⚙️ **بخش مدیریت ویدیوها**\n\nلطفاً ویدیوی مورد نظر را انتخاب کنید:",
            chat_keypad=kilid_admin_video_management(), chat_keypad_type="New"
        )
        return

    # ===== انتخاب ویدیو از لیست مدیریت (بدون پیشوند admvid_) =====
    if is_admin and text.startswith("⚙️ "):
        # استخراج عنوان ویدیو از متن دکمه
        title_from_button = text[3:].strip()
        videos = db.get("videos", VIDEOS)
        video_id = None
        for vid_id, vid_data in videos.items():
            if vid_data['title'] == title_from_button:
                video_id = vid_id
                break
        if video_id and video_id in videos:
            v = videos[video_id]
            admin_states["edit_video_id"] = video_id
            await message.reply(
                f"⚙️ **مدیریت ویدیو:** {v['title']}\n\n"
                f"📝 توضیحات: {v['description']}\n⏱ مدت: {v['duration']}\n💰 قیمت: {v['price']}\n\n"
                f"چه تغییری می‌خواهید اعمال کنید؟",
                chat_keypad=kilid_video_edit_options(video_id), chat_keypad_type="New"
            )
            return

    # ===== ویرایش یا حذف ویدیو =====
    if is_admin and (text.startswith("edit_") or text == "✏️ ویرایش"):
        if text.startswith("edit_"):
            video_id = text.replace("edit_", "")
        else:
            video_id = admin_states.get("edit_video_id")

        if video_id and video_id in db.get("videos", VIDEOS):
            admin_states["edit_video_id"] = video_id
            await message.reply(
                "✏️ **بخش ویرایش اطلاعات**\n\nکدام بخش را می‌خواهید ویرایش کنید؟",
                chat_keypad=kilid_edit_details(video_id), chat_keypad_type="New"
            )
        return

    if is_admin and (text.startswith("delete_") or text == "🗑 حذف"):
        if text.startswith("delete_"):
            video_id = text.replace("delete_", "")
        else:
            video_id = admin_states.get("edit_video_id")

        if video_id and video_id in db.get("videos", VIDEOS):
            v = db["videos"][video_id]
            admin_states[chat_id] = "confirming_delete"
            admin_states["edit_video_id"] = video_id
            await message.reply(
                f"⚠️ **هشدار: حذف ویدیو**\n\n🎬 عنوان: {v.get('title', '')}\n\nآیا از حذف این ویدیو اطمینان دارید؟\nاین عملیات غیرقابل بازگشت است!\n\n✅ برای تأیید بنویسید: بله\n❌ برای لغو بنویسید: خیر"
            )
        return

    # ===== ویرایش جزئیات (کیبرد جدید: فقط با متن) =====
    if is_admin and (text in ["✏️ عنوان", "📝 توضیحات", "⏱ مدت", "💰 قیمت"]):
        video_id = admin_states.get("edit_video_id")
        if video_id and video_id in db.get("videos", VIDEOS):
            v = db["videos"][video_id]
            if text == "✏️ عنوان":
                admin_states[chat_id] = "editing_title"
                admin_states["edit_video_id"] = video_id
                await message.reply(f"✏️ عنوان فعلی: {v['title']}\n\n📝 عنوان جدید را وارد کنید:")
            elif text == "📝 توضیحات":
                admin_states[chat_id] = "editing_description"
                admin_states["edit_video_id"] = video_id
                await message.reply(f"📝 توضیحات فعلی: {v['description']}\n\n📝 توضیحات جدید را بنویسید:")
            elif text == "⏱ مدت":
                admin_states[chat_id] = "editing_duration"
                admin_states["edit_video_id"] = video_id
                await message.reply(f"⏱ مدت فعلی: {v['duration']}\n\n⏱ مدت جدید را وارد کنید:")
            elif text == "💰 قیمت":
                admin_states[chat_id] = "editing_price"
                admin_states["edit_video_id"] = video_id
                await message.reply(f"💰 قیمت فعلی: {v['price']}\n\n💰 قیمت جدید را وارد کنید:")
            return

    # ===== ویرایش با شناسه پیشوندی (حفظ سازگاری احتمالی) =====
    if is_admin:
        if text.startswith("edt_title_"):
            video_id = text.replace("edt_title_", "")
            if video_id in db.get("videos", VIDEOS):
                admin_states[chat_id] = "editing_title"
                admin_states["edit_video_id"] = video_id
                v = db["videos"][video_id]
                await message.reply(f"✏️ عنوان فعلی: {v['title']}\n\n📝 عنوان جدید را وارد کنید:")
            return

        if text.startswith("edt_desc_"):
            video_id = text.replace("edt_desc_", "")
            if video_id in db.get("videos", VIDEOS):
                admin_states[chat_id] = "editing_description"
                admin_states["edit_video_id"] = video_id
                v = db["videos"][video_id]
                await message.reply(f"📝 توضیحات فعلی: {v['description']}\n\n📝 توضیحات جدید را بنویسید:")
            return

        if text.startswith("edt_duration_"):
            video_id = text.replace("edt_duration_", "")
            if video_id in db.get("videos", VIDEOS):
                admin_states[chat_id] = "editing_duration"
                admin_states["edit_video_id"] = video_id
                v = db["videos"][video_id]
                await message.reply(f"⏱ مدت فعلی: {v['duration']}\n\n⏱ مدت جدید را وارد کنید:")
            return

        if text.startswith("edt_price_"):
            video_id = text.replace("edt_price_", "")
            if video_id in db.get("videos", VIDEOS):
                admin_states[chat_id] = "editing_price"
                admin_states["edit_video_id"] = video_id
                v = db["videos"][video_id]
                await message.reply(f"💰 قیمت فعلی: {v['price']}\n\n💰 قیمت جدید را وارد کنید:")
            return

        if text in ["admin_add_video", "➕ افزودن ویدیو جدید"]:
            admin_states[chat_id] = "adding_video_title"
            await message.reply("➕ **افزودن ویدیو جدید**\n\nلطفاً یک عنوان جذاب برای ویدیو انتخاب کنید ✨\n\n📝 عنوان:")
            return

    if is_admin and chat_id in admin_states:
        state = admin_states[chat_id]
        video_id = admin_states.get("edit_video_id")
        videos = db.get("videos", VIDEOS)

        if state == "confirming_delete":
            if text.strip() == "بله" and video_id in videos:
                v_title = videos[video_id].get('title', '')
                del videos[video_id]
                db["videos"] = videos
                save_data(db)
                admin_states.pop(chat_id, None)
                await message.reply(f"🗑 ویدیو '{v_title}' با موفقیت حذف شد!", chat_keypad=kilid_admin_video_management(), chat_keypad_type="New")
            else:
                admin_states.pop(chat_id, None)
                await message.reply("🚫 عملیات حذف لغو شد.", chat_keypad=kilid_admin_video_management(), chat_keypad_type="New")
            return

        if state == "editing_title" and video_id in videos:
            videos[video_id]["title"] = text.strip()
            db["videos"] = videos
            save_data(db)
            admin_states.pop(chat_id, None)
            await message.reply("✅ عنوان بروزرسانی شد!", chat_keypad=kilid_admin_video_management(), chat_keypad_type="New")
            return

        if state == "editing_description" and video_id in videos:
            videos[video_id]["description"] = text.strip()
            db["videos"] = videos
            save_data(db)
            admin_states.pop(chat_id, None)
            await message.reply("✅ توضیحات بروزرسانی شد!", chat_keypad=kilid_admin_video_management(), chat_keypad_type="New")
            return

        if state == "editing_duration" and video_id in videos:
            videos[video_id]["duration"] = text.strip()
            db["videos"] = videos
            save_data(db)
            admin_states.pop(chat_id, None)
            await message.reply("✅ مدت زمان بروزرسانی شد!", chat_keypad=kilid_admin_video_management(), chat_keypad_type="New")
            return

        if state == "editing_price" and video_id in videos:
            videos[video_id]["price"] = text.strip()
            db["videos"] = videos
            save_data(db)
            admin_states.pop(chat_id, None)
            await message.reply("✅ قیمت بروزرسانی شد!", chat_keypad=kilid_admin_video_management(), chat_keypad_type="New")
            return

        # ----- افزودن ویدیو جدید (فقط عنوان و مدت – قیمت و توضیحات پیش‌فرض) -----
        if state == "adding_video_title":
            if len(text.strip()) < 3:
                await message.reply("❌ عنوان باید حداقل ۳ کاراکتر باشد!")
                return
            admin_states["new_video_title"] = text.strip()
            admin_states["new_video_description"] = "..."   # پیش‌فرض
            # پیش‌فرض
            admin_states["new_video_price"] = "با خرید اشتراک تمام ویدیو ها موجود را دریافت میکنید"
            admin_states[chat_id] = "adding_video_duration_new"
            await message.reply(f"✨ عنوان: {text.strip()}\n\n⏱ مدت زمان ویدیو را وارد کنید (مثال: ۴۵ دقیقه):")
            return

        if state == "adding_video_duration_new":
            admin_states["new_video_duration"] = text.strip()
            # ذخیره‌ی مستقیم بدون پرسیدن قیمت
            nid = f"v{len(videos)+1}"
            videos[nid] = {
                "id": nid,
                "title": admin_states.get("new_video_title", ""),
                "description": admin_states.get("new_video_description", "..."),
                "duration": admin_states.get("new_video_duration", ""),
                "price": admin_states.get("new_video_price", "با خرید اشتراک تمام ویدیو ها موجود را دریافت میکنید")
            }
            db["videos"] = videos
            save_data(db)
            admin_states.pop(chat_id, None)
            await message.reply("🎉 ویدیو جدید با موفقیت اضافه شد!", chat_keypad=kilid_admin_video_management(), chat_keypad_type="New")
            return

    # ===== اصلی (ورود، ثبت‌نام، ویدیوها و غیره) =====
    if text in ["login", "🔐 ورود به حساب"]:
        admin_states.pop(chat_id, None)
        user_states[chat_id] = "waiting_username"
        await message.reply("🔐 **ورود به حساب کاربری**\n\nلطفاً نام کاربری خود را وارد کنید:")
        return

    if text in ["register", "✨ عضویت در بات"]:
        admin_states.pop(chat_id, None)
        if chat_id in user_usernames:
            await message.reply("❌ شما هم‌اکنون وارد حساب خود هستید!\nبرای ثبت‌نام جدید، ابتدا خارج شوید.")
            return
        register_states[chat_id] = "register_username"
        await message.reply("📝 **عضویت در بات**\n\nیک نام کاربری زیبا انتخاب کنید:\n\n• حداقل ۳ حرف\n• بدون فاصله\n• فقط حروف انگلیسی")
        return

    if text in ["user_video_list", "🎬 لیست ویدیوها"]:
        admin_states.pop(chat_id, None)
        if not current_username:
            await message.reply("🔒 ابتدا باید وارد حساب خود شوید!")
            return
        if not db.get("videos"):
            await message.reply(
                "📭 **هنوز ویدیویی اضافه نشده!**\n\n"
                "به زودی ویدیوهای جذاب فان و سرگرم‌کننده به این بخش اضافه می‌شود.\n"
                "منتظر خبرهای خوب از طرف ادمین باشید! ✨",
                chat_keypad=kilid_video_list(), chat_keypad_type="New"
            )
            return
        if check_subscription_active(chat_id):
            await message.reply(
                "🎬 **ویدیوهای فان و سرگرم‌کننده**\n\n"
                "برای مشاهده جزئیات، روی هر ویدیو کلیک کنید 👇",
                chat_keypad=kilid_video_list(), chat_keypad_type="New"
            )
        else:
            await message.reply(
                "🎬 **ویدیوها**\n\nبرای مشاهده ویدیوها نیاز به اشتراک فعال دارید.\n"
                "برای خرید اشتراک از منوی اصلی اقدام کنید. 👇\n\n"
                "⭐ برای خرید اشتراک از منوی اصلی اقدام کنید.",
                chat_keypad=kilid_video_list(), chat_keypad_type="New"
            )
        return

    if is_admin and text in ["admin_video_list", "🎬 مدیریت ویدیوها"]:
        admin_states.pop(chat_id, None)
        if not db.get("videos"):
            await message.reply(
                "📭 **هنوز ویدیویی اضافه نشده!**\n\n"
                "به زودی ویدیوهای جذاب فان و سرگرم‌کننده به این بخش اضافه می‌شود.\n"
                "منتظر خبرهای خوب از طرف ادمین باشید! ✨",
                chat_keypad=kilid_video_list(), chat_keypad_type="New"
            )
            return
        await message.reply(
            "🎬 **ویدیوهای فان و سرگرم‌کننده**\n\n"
            "برای مشاهده جزئیات، روی هر ویدیو کلیک کنید 👇",
            chat_keypad=kilid_video_list(), chat_keypad_type="New"
        )
        return

    # ===== بخش درخواست ویدیو =====
    if text in ["video_request", "📥 درخواست ویدیو"]:
        admin_states.pop(chat_id, None)
        if not current_username:
            await message.reply("🔒 ابتدا باید وارد حساب خود شوید!")
            return
        request_states[chat_id] = "writing_video_request"
        await message.reply(
            "📥 **درخواست ویدیو جدید**\n\n"
            "لطفاً ویدیویی که می‌خواهید اضافه شود را شرح دهید:\n\n"
            "• نام ویدیو یا موضوع\n"
            "• لینک (در صورت وجود)\n"
            "• هر توضیح اضافی\n\n"
            "منتظر پیشنهادهای شما هستیم! ✨"
        )
        return

    # ===== دریافت متن درخواست ویدیو =====
    if chat_id in request_states and request_states[chat_id] == "writing_video_request":
        rid = f"VIDREQ-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        db["user_requests"].append({
            "request_id": rid,
            "username": current_username,
            "chat_id": str(chat_id),
            "type": "video_request",
            "request": text,
            "date": datetime.now().strftime("%Y/%m/%d %H:%M"),
            "status": "pending"
        })
        save_data(db)
        request_states.pop(chat_id, None)
        await message.reply(
            f"✅ **درخواست شما با موفقیت ثبت شد!**\n\n"
            f"👤 کاربر: {current_username}\n"
            f"📝 شرح درخواست:\n{text}\n\n"
            f"⏳ پس از بررسی، نتیجه اعلام خواهد شد.\n"
            f"با تشکر از پیشنهاد شما 🙏",
            chat_keypad=kilid_user_panel(),
            chat_keypad_type="New"
        )
        return

    # ===== گزارش مشکل =====
    if text in ["report_problem", "⚠️ گزارش مشکل"]:
        admin_states.pop(chat_id, None)
        if not current_username:
            await message.reply("🔒 ابتدا باید وارد حساب خود شوید!")
            return
        report_states[chat_id] = "writing_report"
        await message.reply("⚠️ **گزارش مشکل**\n\nلطفاً مشکل خود را به طور کامل توضیح دهید:\n\n• چه مشکلی پیش آمده؟\n• در کدام بخش با مشکل مواجه شدید؟")
        return

    if text in ["back_to_video_list", "🔙 لیست ویدیوها", "🔙 ویدیوهای دیگر"]:
        purchase_states.pop(chat_id, None)
        selected_video.pop(chat_id, None)
        await message.reply(
            "🎬 **لیست ویدیوها**\n\nدوباره می‌توانید ویدیوی مورد نظر خود را انتخاب کنید:",
            chat_keypad=kilid_video_list(), chat_keypad_type="New"
        )
        return

    if text in ["cancel_purchase", "🔙 انصراف"]:
        purchase_states.pop(chat_id, None)
        await message.reply("🚫 عملیات خرید لغو شد.", chat_keypad=kilid_subscription_plans(), chat_keypad_type="New")
        return

    if text in ["logout", "🚪 خروج"]:
        for d in [user_usernames, user_states, admin_states, register_states, purchase_states, request_states, report_states, selected_video, pending_rubika_id_request, edit_rubika_states]:
            d.pop(chat_id, None)
        await message.reply("👋 خدانگهدار! امیدواریم به زودی برگردید.", chat_keypad=kilid_main(), chat_keypad_type="New")
        return

    # ===== کلیک روی ویدیو (با متن جدید) =====
    if text.startswith("vid_"):
        video_id = text.split(" ")[0].replace("vid_", "")
        if video_id and video_id in db.get("videos", VIDEOS):
            selected_video[chat_id] = video_id
            v = db["videos"][video_id]
            await message.reply(
                f"✨ **اطلاعات ویدیو** ✨\n\n"
                f"🎬 عنوان: {v['title']}\n📝 توضیحات: {v['description']}\n⏱ مدت: {v['duration']}\n💰 قیمت: {v['price']}\n\n"
                f"👇 برای خرید اشتراک و دسترسی کامل، روی دکمه زیر کلیک کنید:"
            )
            await message.reply("🎬 **گزینه‌های ویدیو:**", chat_keypad=kilid_video_selected(), chat_keypad_type="New")
        return

    if chat_id in purchase_states:
        state = purchase_states[chat_id]
        if state == "waiting_card":
            card = text.replace(" ", "").replace("-", "")
            if not card.isdigit() or len(card) != 16:
                await message.reply("❌ شماره کارت باید ۱۶ رقم باشد!")
                return
            purchase_states[chat_id] = "waiting_cardholder"
            purchase_states[f"{chat_id}_card"] = card
            await message.reply("💳 شماره کارت شما ثبت شد.\n\n👤 لطفاً **نام صاحب کارت** (همان نامی که روی کارت درج شده) را وارد کنید:")
            return

        elif state == "waiting_cardholder":
            cardholder = text.strip()
            if len(cardholder) < 3:
                await message.reply("❌ نام صاحب کارت باید حداقل ۳ حرف باشد!")
                return
            purchase_states[chat_id] = "waiting_payment"
            purchase_states[f"{chat_id}_cardholder"] = cardholder
            plan_price = purchase_states.get(f"{chat_id}_plan_price", 0)
            plan_name = purchase_states.get(f"{chat_id}_plan_name", "")
            plan_duration = purchase_states.get(f"{chat_id}_plan_duration", "")
            card = purchase_states.get(f"{chat_id}_card", "")
            await message.reply(
                f"💳 **اطلاعات پرداخت**\n\n"
                f"✅ شماره کارت شما: {card}\n"
                f"👤 نام صاحب کارت: {cardholder}\n"
                f"💳 کارت مقصد: `{CARD_NUMBER}`\n"
                f"👤 به نام: {CARD_HOLDER}\n"
                f"💰 مبلغ: {plan_price:,} تومان\n"
                f"📦 پلن: {plan_name}\n"
                f"📅 مدت: {plan_duration}\n\n"
                f"پس از واریز، روی دکمه زیر کلیک کنید."
            )
            await message.reply("💳 لطفاً پرداخت را انجام دهید:", chat_keypad=kilid_after_card(), chat_keypad_type="New")
            return

    if text in ["payment_done", "✅ پرداخت انجام شد"]:
        if chat_id in purchase_states and purchase_states[chat_id] == "waiting_payment":
            plan_id = purchase_states.get(f"{chat_id}_plan_id", "")
            plan_name = purchase_states.get(f"{chat_id}_plan_name", "نامشخص")
            plan_price = purchase_states.get(f"{chat_id}_plan_price", 0)
            plan_duration = purchase_states.get(f"{chat_id}_plan_duration", "")
            card = purchase_states.get(f"{chat_id}_card", "نامشخص")
            cardholder = purchase_states.get(f"{chat_id}_cardholder", "نامشخص")
            pid = f"SUB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            db["pending_payments"].append({
                "payment_id": pid, "username": current_username, "chat_id": str(chat_id),
                "plan_id": plan_id, "plan_name": plan_name, "amount": plan_price,
                "duration": plan_duration, "card_number": card,
                "card_holder": cardholder,
                "status": "pending",
                "type": "subscription", "date": datetime.now().strftime("%Y/%m/%d %H:%M")
            })
            db["transactions"].append({
                "username": current_username, "plan_name": plan_name,
                "amount": f"{plan_price:,} تومان", "status": "pending",
                "date": datetime.now().strftime("%Y/%m/%d %H:%M"),
                "payment_id": pid, "type": "subscription"
            })
            save_data(db)
            purchase_states.pop(chat_id, None)

            payment_msg = (
                f"🎉 **پرداخت شما با موفقیت ثبت شد!**\n\n"
                f"📦 پلن: {plan_name}\n💰 مبلغ: {plan_price:,} تومان\n📅 مدت: {plan_duration}\n\n"
                f"⏳ پرداخت شما در حال بررسی است.\n"
                f"پس از تأیید ادمین، اشتراک شما فعال خواهد شد.\n\n"
            )

            if has_registered_rubika_id(chat_id):
                payment_msg += f"✅ ایدی روبیکای شما قبلاً ثبت شده: `{user_rubika_ids[str(chat_id)]}`\n\n"
                payment_msg += "🙏 از صبر شما متشکریم!"
                kb = kilid_user_panel() if not is_admin else kilid_admin_panel()
            else:
                payment_msg += (
                    "📱 **لطفاً همین حالا ایدی روبیکای خود را ثبت کنید!**\n\n"
                    "⚠️ **نکات مهم:**\n"
                    "• ایدی باید حتماً با **@** شروع شود\n"
                    "• مثال: `@username`\n"
                    "• ادمین با همین ایدی شما را به کانال اضافه می‌کند\n"
                    "• **از درستی ایدی مطمئن شوید**\n\n"
                    "👇 روی دکمه زیر کلیک کنید:"
                )
                kb = kilid_rubika_id_request()

            await message.reply(payment_msg, chat_keypad=kb, chat_keypad_type="New")

            try:
                await robot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"💳 **پرداخت اشتراک جدید**\n\n👤 کاربر: {current_username}\n📦 پلن: {plan_name}\n💰 مبلغ: {plan_price:,} تومان\n📅 مدت: {plan_duration}\n💳 کارت واریز‌کننده: {card}\n👤 نام صاحب کارت: {cardholder}\n\nبرای رسیدگی به بخش «تأیید پرداخت‌ها» مراجعه کنید."
                )
            except Exception as e:
                print(f"Error notifying admin: {e}")
        return

    if chat_id in report_states and report_states[chat_id] == "writing_report":
        rid = f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        db["reports"].append({
            "report_id": rid, "username": current_username, "chat_id": str(chat_id),
            "report": text, "date": datetime.now().strftime("%Y/%m/%d %H:%M"), "status": "pending"
        })
        save_data(db)
        report_states.pop(chat_id, None)
        await message.reply(f"✅ **گزارش شما ثبت شد!**\n\nتیم پشتیبانی بررسی خواهد کرد.", chat_keypad=kilid_user_panel(), chat_keypad_type="New")
        return

    if is_admin:
        if text in ["admin_requests", "📨 صندوق درخواست‌ها"]:
            admin_states.pop(chat_id, None)
            if not db["user_requests"]:
                await message.reply("📭 هیچ درخواستی ثبت نشده است!")
                return
            for r in db["user_requests"]:
                req_type = r.get("type", "عمومی")
                if req_type == "video_request":
                    type_label = "🎬 درخواست ویدیو"
                else:
                    type_label = "📨 درخواست"
                await message.reply(
                    f"{type_label} از {r['username']}:\n"
                    f"📝 متن: {r['request']}\n"
                    f"📅 تاریخ: {r['date']}"
                )
            return
        if text in ["admin_reports", "📋 گزارش‌ها"]:
            admin_states.pop(chat_id, None)
            if not db.get("reports", []):
                await message.reply("✅ هیچ گزارشی ثبت نشده است!")
                return
            for r in db["reports"]:
                s = "⏳ در انتظار بررسی" if r.get(
                    "status") == "pending" else "✅ بررسی شده"
                await message.reply(f"{s}\n👤 کاربر: {r['username']}\n📅 تاریخ: {r['date']}\n📝 شرح: {r['report']}")
            return
        if text in ["admin_delete_user", "🗑 حذف کاربر"]:
            admin_states.pop(chat_id, None)
            admin_states[chat_id] = "deleting_user"
            ul = "\n".join(
                [f"• {u}" for u in db["users"] if not is_admin_user(u)])
            if not ul:
                await message.reply("✅ کاربری برای حذف وجود ندارد!")
                return
            await message.reply(f"🗑 **حذف کاربر**\n\nبرای حذف، نام کاربری مورد نظر را بنویسید:\n\n{ul}")
            return
        if chat_id in admin_states and admin_states[chat_id] == "deleting_user":
            u = text.lower().strip()
            if u in db["users"] and not is_admin_user(u):
                del db["users"][u]
                save_data(db)
                admin_states.pop(chat_id, None)
                await message.reply(f"🗑 کاربر '{u}' با موفقیت حذف شد!", chat_keypad=kilid_admin_panel(), chat_keypad_type="New")
            return

    if chat_id in register_states:
        state = register_states[chat_id]
        if state == "register_username":
            nu = text.lower().strip()
            if len(nu) < 3 or " " in nu or nu in db["users"]:
                await message.reply("❌ نام کاربری نامعتبر است!\n\n• حداقل ۳ حرف\n• بدون فاصله\n• تکراری نباشد")
                return
            register_states[f"{chat_id}_tu"] = nu
            register_states[chat_id] = "register_password"
            await message.reply(f"✅ نام کاربری '{nu}' تأیید شد!\n\n🔐 لطفاً رمز عبور خود را وارد کنید (حداقل ۴ کاراکتر):")
            return
        if state == "register_password":
            np = text.strip()
            if len(np) < 4:
                await message.reply("❌ رمز عبور باید حداقل ۴ کاراکتر باشد!")
                return
            nu = register_states.get(f"{chat_id}_tu")
            db["users"][nu] = np
            save_data(db)
            register_states.pop(chat_id, None)
            user_usernames[chat_id] = nu
            kb = kilid_admin_panel() if is_admin_user(nu) else kilid_user_panel()
            await message.reply(f"🎉 **عضویت با موفقیت انجام شد!**\n\n👤 نام کاربری: {nu}\n🔐 رمز عبور: {np}\n\n⚠️ اطلاعات خود را یادداشت کنید.\n✨ اکنون می‌توانید از ربات استفاده کنید!", chat_keypad=kb, chat_keypad_type="New")
            return

    if chat_id in user_states:
        state = user_states[chat_id]
        if state == "waiting_username":
            eu = text.lower().strip()
            found = next((du for du in db["users"] if du.lower() == eu), None)
            if found:
                user_usernames[chat_id] = found
                user_states[chat_id] = "waiting_password"
                await message.reply(f"✅ نام کاربری '{found}' معتبر است!\n\n🔐 لطفاً رمز عبور خود را وارد کنید:")
            else:
                await message.reply("❌ نام کاربری یافت نشد!\n\nاگر حساب ندارید، گزینه «عضویت در بات» را انتخاب کنید.")
            return
        if state == "waiting_password":
            uname = user_usernames.get(chat_id)
            if text.strip() == db["users"].get(uname):
                user_states.pop(chat_id, None)
                kb = kilid_admin_panel() if is_admin_user(uname) else kilid_user_panel()
                await message.reply(f"😊 **خوش آمدید {uname} عزیز!**\n\nورود شما با موفقیت انجام شد.\nاز امکانات ربات لذت ببرید!", chat_keypad=kb, chat_keypad_type="New")
            else:
                await message.reply("❌ رمز عبور اشتباه است!\n\nلطفاً مجدداً تلاش کنید.")
            return


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    threading.Thread(target=start_health_server,
                     args=(port,), daemon=True).start()
    asyncio.run(bot.run())
