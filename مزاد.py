import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import sqlite3
from datetime import datetime

TOKEN = "8567704129:AAGcwJOUB5E-0Ws3CXKszrSbAD78IvryB04"
OWNER_ID = 7804017901

def init_db():
    conn = sqlite3.connect('auction_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, 
                  accepted_terms INTEGER DEFAULT 0, blocked INTEGER DEFAULT 0, join_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS admins
                 (user_id INTEGER PRIMARY KEY, username TEXT, added_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS pending_gifts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, 
                  first_name TEXT, gift_link TEXT, status TEXT, created_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS pending_usernames
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, 
                  first_name TEXT, username_offer TEXT, status TEXT, created_date TEXT)''')
    
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('channel_id', '')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('channel_link', '')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('group_id', '')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('start_text', 'مرحبا {name} في بوت المزاد\n\nاختر نوع المزاد الذي ترغب في نشره')")
    c.execute("INSERT OR IGNORE INTO admins (user_id, username, added_date) VALUES (?, 'Owner', ?)", 
              (OWNER_ID, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()

def get_setting(key):
    conn = sqlite3.connect('auction_bot.db')
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def set_setting(key, value):
    conn = sqlite3.connect('auction_bot.db')
    c = conn.cursor()
    c.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
    conn.commit()
    conn.close()

def add_user(user_id, username, first_name):
    conn = sqlite3.connect('auction_bot.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, first_name, join_date) VALUES (?, ?, ?, ?)",
              (user_id, username, first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def accept_terms(user_id):
    conn = sqlite3.connect('auction_bot.db')
    c = conn.cursor()
    c.execute("UPDATE users SET accepted_terms = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def has_accepted_terms(user_id):
    conn = sqlite3.connect('auction_bot.db')
    c = conn.cursor()
    c.execute("SELECT accepted_terms FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == 1

def is_admin(user_id):
    conn = sqlite3.connect('auction_bot.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_all_admins():
    conn = sqlite3.connect('auction_bot.db')
    c = conn.cursor()
    c.execute("SELECT user_id, username FROM admins")
    admins = c.fetchall()
    conn.close()
    return admins

def add_admin(user_id, username):
    conn = sqlite3.connect('auction_bot.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO admins (user_id, username, added_date) VALUES (?, ?, ?)",
              (user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def remove_admin(user_id):
    conn = sqlite3.connect('auction_bot.db')
    c = conn.cursor()
    c.execute("DELETE FROM admins WHERE user_id = ? AND user_id != ?", (user_id, OWNER_ID))
    conn.commit()
    conn.close()

def get_users_count():
    conn = sqlite3.connect('auction_bot.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE blocked = 1")
    blocked = c.fetchone()[0]
    conn.close()
    return total, blocked

def get_all_users():
    conn = sqlite3.connect('auction_bot.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE blocked = 0")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def add_pending_gift(user_id, username, first_name, gift_link):
    conn = sqlite3.connect('auction_bot.db')
    c = conn.cursor()
    c.execute("INSERT INTO pending_gifts (user_id, username, first_name, gift_link, status, created_date) VALUES (?, ?, ?, ?, 'pending', ?)",
              (user_id, username, first_name, gift_link, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    gift_id = c.lastrowid
    conn.commit()
    conn.close()
    return gift_id

def add_pending_username(user_id, username, first_name, username_offer):
    conn = sqlite3.connect('auction_bot.db')
    c = conn.cursor()
    c.execute("INSERT INTO pending_usernames (user_id, username, first_name, username_offer, status, created_date) VALUES (?, ?, ?, ?, 'pending', ?)",
              (user_id, username, first_name, username_offer, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    username_id = c.lastrowid
    conn.commit()
    conn.close()
    return username_id

def get_pending_gift(gift_id):
    conn = sqlite3.connect('auction_bot.db')
    c = conn.cursor()
    c.execute("SELECT user_id, username, first_name, gift_link FROM pending_gifts WHERE id = ?", (gift_id,))
    result = c.fetchone()
    conn.close()
    return result

def get_pending_username_data(username_id):
    conn = sqlite3.connect('auction_bot.db')
    c = conn.cursor()
    c.execute("SELECT user_id, username, first_name, username_offer FROM pending_usernames WHERE id = ?", (username_id,))
    result = c.fetchone()
    conn.close()
    return result

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username, user.first_name)
    
    if user.id == OWNER_ID:
        keyboard = [
            [InlineKeyboardButton("قسم الادمنيه", callback_data="admin_section"),
             InlineKeyboardButton("قسم الاعدادات", callback_data="settings_section")],
            [InlineKeyboardButton("قسم التعيين", callback_data="assignment_section")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("<b>اهلا بك في قسم التحكم</b>", reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    if not has_accepted_terms(user.id):
        terms_text = """<blockquote><b>شروط استخدام بوت المزاد

يجب عليك الموافقة على الشروط التالية:
- عدم استخدام حسابات وهمية
- عدم نشر محتوى مخالف
- الالتزام بقوانين البوت
- تحمل المسؤولية الكاملة عن المزادات المنشورة</b></blockquote>"""
        
        keyboard = [[InlineKeyboardButton("الموافقة على شروط الاستخدام", callback_data="accept_terms")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(terms_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await show_main_menu(update.message, user)

async def show_main_menu(message, user):
    start_text = get_setting('start_text')
    if start_text:
        text = start_text.replace('{name}', user.first_name)
    else:
        text = f"مرحبا {user.first_name} في بوت المزاد\n\nاختر نوع المزاد الذي ترغب في نشره"
    
    text = f"<blockquote><b>{text}</b></blockquote>"
    
    channel_link = get_setting('channel_link')
    
    keyboard = [
        [InlineKeyboardButton("نشر هدية", callback_data="post_gift"),
         InlineKeyboardButton("نشر معرف", callback_data="post_username")]
    ]
    
    if channel_link and channel_link.strip():
        keyboard.append([InlineKeyboardButton("قناة المزاد", url=channel_link)])
    else:
        keyboard.append([InlineKeyboardButton("قناة المزاد", callback_data="auction_channel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    if query.data == "accept_terms":
        accept_terms(user.id)
        await query.message.edit_text("<b>تم قبول الشروط بنجاح</b>", parse_mode=ParseMode.HTML)
        await show_main_menu(query.message, user)
    
    elif query.data == "post_gift":
        context.user_data['waiting_for'] = 'gift_link'
        keyboard = [[InlineKeyboardButton("رجوع الى القائمة الرئيسية", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "<blockquote><b>حسنا الان ارسل لي رابط الهدية فقط مثل\nt.me/nft/GiftName-1234</b></blockquote>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    elif query.data == "post_username":
        context.user_data['waiting_for'] = 'username_offer'
        keyboard = [[InlineKeyboardButton("رجوع الى القائمة الرئيسية", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "<blockquote><b>حسنا الان ارسل المعرف الذي تريد عرضه</b></blockquote>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    elif query.data == "auction_channel":
        channel_id = get_setting('channel_id')
        channel_link = get_setting('channel_link')
        if channel_id and channel_id.strip():
            try:
                chat = await context.bot.get_chat(channel_id)
                text = f"<b>قناة المزاد:</b> {chat.title}\n<code>{channel_id}</code>"
                if channel_link and channel_link.strip():
                    text += f"\n<b>الرابط:</b> {channel_link}"
                await query.message.edit_text(text, parse_mode=ParseMode.HTML)
            except:
                await query.message.edit_text("<b>لم يتم تعيين قناة المزاد بعد</b>", parse_mode=ParseMode.HTML)
        else:
            await query.message.edit_text("<b>لم يتم تعيين قناة المزاد بعد</b>", parse_mode=ParseMode.HTML)
    
    elif query.data == "back_to_main":
        context.user_data.clear()
        await query.message.delete()
        await show_main_menu(query.message, user)
    
    elif query.data == "admin_section" and user.id == OWNER_ID:
        keyboard = [
            [InlineKeyboardButton("رفع ادمن", callback_data="promote_admin"),
             InlineKeyboardButton("تنزيل ادمن", callback_data="demote_admin")],
            [InlineKeyboardButton("عرض الادمنيه", callback_data="show_admins")],
            [InlineKeyboardButton("رجوع", callback_data="back_to_control")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("<b>قسم الادمنيه</b>", reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    elif query.data == "settings_section" and user.id == OWNER_ID:
        keyboard = [
            [InlineKeyboardButton("اذاعة في البوت", callback_data="broadcast"),
             InlineKeyboardButton("اذاعة بالتوجيه", callback_data="forward_broadcast")],
            [InlineKeyboardButton("الاحصائيات", callback_data="statistics")],
            [InlineKeyboardButton("رجوع", callback_data="back_to_control")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("<b>قسم الاعدادات</b>", reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    elif query.data == "assignment_section" and user.id == OWNER_ID:
        channel_id = get_setting('channel_id') or "غير معين"
        channel_link = get_setting('channel_link') or "غير معين"
        group_id = get_setting('group_id') or "غير معين"
        start_text = get_setting('start_text') or "غير معين"
        
        text = f"""<b>المجموعة الحالية:</b> <code>{group_id}</code>
<b>القناة الحالية:</b> <code>{channel_id}</code>
<b>رابط القناة الحالي:</b> <code>{channel_link}</code>
<b>نص الستارت الحالي:</b> <code>{start_text}</code>"""
        
        keyboard = [
            [InlineKeyboardButton("تعيين القناة", callback_data="set_channel"),
             InlineKeyboardButton("تعيين المجموعة", callback_data="set_group")],
            [InlineKeyboardButton("تعيين الستارت", callback_data="set_start_text")],
            [InlineKeyboardButton("رجوع", callback_data="back_to_control")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    elif query.data == "back_to_control" and user.id == OWNER_ID:
        keyboard = [
            [InlineKeyboardButton("قسم الادمنيه", callback_data="admin_section"),
             InlineKeyboardButton("قسم الاعدادات", callback_data="settings_section")],
            [InlineKeyboardButton("قسم التعيين", callback_data="assignment_section")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("<b>اهلا بك في قسم التحكم</b>", reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    elif query.data == "promote_admin" and user.id == OWNER_ID:
        context.user_data['waiting_for'] = 'promote_admin_id'
        await query.message.edit_text("<b>ارسل ايدي المستخدم لرفعه ادمن</b>", parse_mode=ParseMode.HTML)
    
    elif query.data == "demote_admin" and user.id == OWNER_ID:
        context.user_data['waiting_for'] = 'demote_admin_id'
        await query.message.edit_text("<b>ارسل ايدي الادمن لتنزيله</b>", parse_mode=ParseMode.HTML)
    
    elif query.data == "show_admins" and user.id == OWNER_ID:
        admins = get_all_admins()
        if admins:
            text = "<b>قائمة الادمنية:</b>\n\n"
            for admin_id, username in admins:
                text += f"<b>الايدي:</b> <code>{admin_id}</code>\n<b>اليوزر:</b> @{username if username else 'بدون يوزر'}\n\n"
        else:
            text = "<b>لا يوجد ادمنية</b>"
        await query.message.edit_text(text, parse_mode=ParseMode.HTML)
    
    elif query.data == "broadcast" and user.id == OWNER_ID:
        context.user_data['waiting_for'] = 'broadcast_message'
        await query.message.edit_text("<b>ارسل الرسالة التي تريد اذاعتها</b>", parse_mode=ParseMode.HTML)
    
    elif query.data == "forward_broadcast" and user.id == OWNER_ID:
        context.user_data['waiting_for'] = 'forward_broadcast_message'
        await query.message.edit_text("<b>ارسل الرسالة التي تريد اذاعتها بالتوجيه</b>", parse_mode=ParseMode.HTML)
    
    elif query.data == "statistics" and user.id == OWNER_ID:
        total, blocked = get_users_count()
        text = f"""<blockquote><b>احصائيات البوت

عدد المستخدمين: {total}
عدد الذين حظروا البوت: {blocked}
عدد المستخدمين النشطين: {total - blocked}</b></blockquote>"""
        await query.message.edit_text(text, parse_mode=ParseMode.HTML)
    
    elif query.data == "set_channel" and user.id == OWNER_ID:
        context.user_data['waiting_for'] = 'set_channel_id'
        await query.message.edit_text("<b>قم برفع البوت مشرف في القناة ثم ارسل ايدي القناة ورابطها بهذا الشكل:</b>\n\n<i>-1001234567890 https://t.me/channelname</i>", parse_mode=ParseMode.HTML)
    
    elif query.data == "set_group" and user.id == OWNER_ID:
        context.user_data['waiting_for'] = 'set_group_id'
        await query.message.edit_text("<b>قم برفع البوت مشرف في المجموعة ثم ارسل ايدي المجموعة</b>\n\n<i>مثال: -1001234567890</i>", parse_mode=ParseMode.HTML)
    
    elif query.data == "set_start_text" and user.id == OWNER_ID:
        context.user_data['waiting_for'] = 'set_start_text'
        await query.message.edit_text("<b>ارسل نص الرسالة الترحيبية الجديد</b>\n\n<i>يمكنك استخدام {name} لاضافة اسم المستخدم</i>", parse_mode=ParseMode.HTML)
    
    elif query.data.startswith("publish_gift_"):
        if not is_admin(user.id):
            await query.answer("ليس لديك صلاحية", show_alert=True)
            return
        
        gift_id = int(query.data.split("_")[2])
        gift_data = get_pending_gift(gift_id)
        
        if not gift_data:
            await query.answer("لم يتم العثور على الهدية", show_alert=True)
            return
        
        user_id, username, first_name, gift_link = gift_data
        
        channel_id = get_setting('channel_id')
        group_id = get_setting('group_id')
        target = channel_id if channel_id and channel_id.strip() else (group_id if group_id and group_id.strip() else None)
        
        if target:
            post_text = f"""<blockquote><b>مزاد توكيو - TokYo Auction

<a href="{gift_link}">Click</a>

حط سعرك فقط مثل 1as / 1ton</b></blockquote>"""
            
            try:
                sent_message = await context.bot.send_message(
                    chat_id=target,
                    text=post_text,
                    parse_mode=ParseMode.HTML
                )
                
                await query.message.edit_text("<b>تم نشر الهدية بنجاح</b>", parse_mode=ParseMode.HTML)
                
                message_link = f"https://t.me/c/{str(target).replace('-100', '')}/{sent_message.message_id}"
                if target.startswith('@'):
                    message_link = f"https://t.me/{target.replace('@', '')}/{sent_message.message_id}"
                
                keyboard = [
                    [InlineKeyboardButton("رؤية المزاد", url=message_link)],
                    [InlineKeyboardButton("رجوع", callback_data="back_to_main")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await context.bot.send_message(
                    chat_id=user_id,
                    text="<blockquote><b>تم نشر هديتك في قناة المزاد\n\nيمكنك الان مشاهدة مزادك</b></blockquote>",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                await query.message.edit_text(f"<b>حدث خطأ اثناء النشر:</b>\n<code>{str(e)}</code>\n\n<i>تأكد من رفع البوت مشرف في القناة وان الايدي صحيح</i>", parse_mode=ParseMode.HTML)
        else:
            await query.message.edit_text("<b>لم يتم تعيين قناة او مجموعة للنشر</b>", parse_mode=ParseMode.HTML)
    
    elif query.data.startswith("publish_username_"):
        if not is_admin(user.id):
            await query.answer("ليس لديك صلاحية", show_alert=True)
            return
        
        username_id = int(query.data.split("_")[2])
        username_data = get_pending_username_data(username_id)
        
        if not username_data:
            await query.answer("لم يتم العثور على المعرف", show_alert=True)
            return
        
        user_id, username, first_name, username_offer = username_data
        
        channel_id = get_setting('channel_id')
        group_id = get_setting('group_id')
        target = channel_id if channel_id and channel_id.strip() else (group_id if group_id and group_id.strip() else None)
        
        if target:
            post_text = f"""<blockquote><b>مزاد توكيو - TokYo Auction

المعرف: @{username_offer}

حط سعرك فقط مثل 1as / 1ton</b></blockquote>"""
            
            try:
                sent_message = await context.bot.send_message(
                    chat_id=target,
                    text=post_text,
                    parse_mode=ParseMode.HTML
                )
                
                await query.message.edit_text("<b>تم نشر المعرف بنجاح</b>", parse_mode=ParseMode.HTML)
                
                message_link = f"https://t.me/c/{str(target).replace('-100', '')}/{sent_message.message_id}"
                if target.startswith('@'):
                    message_link = f"https://t.me/{target.replace('@', '')}/{sent_message.message_id}"
                
                keyboard = [
                    [InlineKeyboardButton("رؤية المزاد", url=message_link)],
                    [InlineKeyboardButton("رجوع", callback_data="back_to_main")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await context.bot.send_message(
                    chat_id=user_id,
                    text="<blockquote><b>تم نشر معرفك في قناة المزاد\n\نيمكنك الان مشاهدة مزادك</b></blockquote>",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                await query.message.edit_text(f"<b>حدث خطأ اثناء النشر:</b>\n<code>{str(e)}</code>\n\n<i>تأكد من رفع البوت مشرف في القناة وان الايدي صحيح</i>", parse_mode=ParseMode.HTML)
        else:
            await query.message.edit_text("<b>لم يتم تعيين قناة او مجموعة للنشر</b>", parse_mode=ParseMode.HTML)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    
    if 'waiting_for' not in context.user_data:
        return
    
    waiting_for = context.user_data['waiting_for']
    
    if waiting_for == 'gift_link':
        if 't.me/' in text or 'telegram.me/' in text:
            gift_id = add_pending_gift(user.id, user.username, user.first_name, text)
            await update.message.reply_text("<blockquote><b>تم ارسال طلبك الى الادارة وعند نشر هديتك سوف يتم ابلاغك. شكرا لاستخدامك البوت</b></blockquote>", parse_mode=ParseMode.HTML)
            
            admins = get_all_admins()
            admin_text = f"""<blockquote><b>هنالك شخص عرض هديته

اسمه: {user.first_name}
يوزره: @{user.username if user.username else 'بدون يوزر'}
ايديه: <code>{user.id}</code>
هديته: {text}</b></blockquote>"""
            
            keyboard = [[InlineKeyboardButton("نشر الهدية", callback_data=f"publish_gift_{gift_id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            for admin_id, _ in admins:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=admin_text,
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML
                    )
                except:
                    pass
            
            context.user_data.clear()
        else:
            await update.message.reply_text("<b>الرجاء ارسال رابط صحيح للهدية</b>", parse_mode=ParseMode.HTML)
    
    elif waiting_for == 'username_offer':
        username_id = add_pending_username(user.id, user.username, user.first_name, text.replace('@', ''))
        await update.message.reply_text("<blockquote><b>تم ارسال طلبك الى الادارة وعند نشر معرفك سوف يتم ابلاغك. شكرا لاستخدامك البوت</b></blockquote>", parse_mode=ParseMode.HTML)
        
        admins = get_all_admins()
        admin_text = f"""<blockquote><b>هنالك شخص عرض معرفه

اسمه: {user.first_name}
يوزره: @{user.username if user.username else 'بدون يوزر'}
ايديه: <code>{user.id}</code>
المعرف: @{text.replace('@', '')}</b></blockquote>"""
        
        keyboard = [[InlineKeyboardButton("نشر المعرف", callback_data=f"publish_username_{username_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        for admin_id, _ in admins:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            except:
                pass
        
        context.user_data.clear()
    
    elif waiting_for == 'promote_admin_id' and user.id == OWNER_ID:
        try:
            admin_id = int(text)
            add_admin(admin_id, "admin")
            await update.message.reply_text(f"<b>تم رفع المستخدم <code>{admin_id}</code> الى ادمن</b>", parse_mode=ParseMode.HTML)
            
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text="<blockquote><b>تم رفعك الى ادمن في البوت</b></blockquote>",
                    parse_mode=ParseMode.HTML
                )
            except:
                pass
            
            context.user_data.clear()
        except:
            await update.message.reply_text("<b>الرجاء ارسال ايدي صحيح</b>", parse_mode=ParseMode.HTML)
    
    elif waiting_for == 'demote_admin_id' and user.id == OWNER_ID:
        try:
            admin_id = int(text)
            if admin_id == OWNER_ID:
                await update.message.reply_text("<b>لا يمكن تنزيل المالك</b>", parse_mode=ParseMode.HTML)
            else:
                remove_admin(admin_id)
                await update.message.reply_text(f"<b>تم تنزيل الادمن <code>{admin_id}</code></b>", parse_mode=ParseMode.HTML)
            context.user_data.clear()
        except:
            await update.message.reply_text("<b>الرجاء ارسال ايدي صحيح</b>", parse_mode=ParseMode.HTML)
    
    elif waiting_for == 'broadcast_message' and user.id == OWNER_ID:
        users = get_all_users()
        success = 0
        failed = 0
        
        for user_id in users:
            try:
                await context.bot.send_message(chat_id=user_id, text=text, parse_mode=ParseMode.HTML)
                success += 1
                await asyncio.sleep(0.05)
            except:
                failed += 1
        
        await update.message.reply_text(f"<b>تم ارسال الاذاعة\n\nنجح: {success}\nفشل: {failed}</b>", parse_mode=ParseMode.HTML)
        context.user_data.clear()
    
    elif waiting_for == 'forward_broadcast_message' and user.id == OWNER_ID:
        users = get_all_users()
        success = 0
        failed = 0
        
        for user_id in users:
            try:
                await update.message.forward(chat_id=user_id)
                success += 1
                await asyncio.sleep(0.05)
            except:
                failed += 1
        
        await update.message.reply_text(f"<b>تم ارسال الاذاعة بالتوجيه\n\nنجح: {success}\nفشل: {failed}</b>", parse_mode=ParseMode.HTML)
        context.user_data.clear()
    
    elif waiting_for == 'set_channel_id' and user.id == OWNER_ID:
        try:
            parts = text.strip().split()
            if len(parts) >= 2:
                channel_id = parts[0]
                channel_link = parts[1]
                
                set_setting('channel_id', channel_id)
                set_setting('channel_link', channel_link)
                
                try:
                    chat = await context.bot.get_chat(channel_id)
                    await update.message.reply_text(f"<b>تم تعيين القناة:</b> {chat.title}\n<code>{channel_id}</code>\n<b>الرابط:</b> {channel_link}", parse_mode=ParseMode.HTML)
                except:
                    await update.message.reply_text(f"<b>تم تعيين القناة:</b>\n<code>{channel_id}</code>\n<b>الرابط:</b> {channel_link}\n\n<i>تأكد من رفع البوت مشرف في القناة</i>", parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text("<b>الرجاء ارسال البيانات بالشكل الصحيح:\n-1001234567890 https://t.me/channelname</b>", parse_mode=ParseMode.HTML)
            
            context.user_data.clear()
        except:
            await update.message.reply_text("<b>حدث خطأ، الرجاء المحاولة مرة اخرى</b>", parse_mode=ParseMode.HTML)
    
    elif waiting_for == 'set_group_id' and user.id == OWNER_ID:
        set_setting('group_id', text.strip())
        try:
            chat = await context.bot.get_chat(text.strip())
            await update.message.reply_text(f"<b>تم تعيين المجموعة:</b> {chat.title}\n<code>{text.strip()}</code>", parse_mode=ParseMode.HTML)
        except:
            await update.message.reply_text(f"<b>تم تعيين المجموعة:</b>\n<code>{text.strip()}</code>\n\n<i>تأكد من رفع البوت مشرف في المجموعة</i>", parse_mode=ParseMode.HTML)
        context.user_data.clear()
    
    elif waiting_for == 'set_start_text' and user.id == OWNER_ID:
        set_setting('start_text', text)
        await update.message.reply_text("<b>تم تعيين نص الستارت الجديد</b>", parse_mode=ParseMode.HTML)
        context.user_data.clear()

def main():
    init_db()
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()