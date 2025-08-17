import logging
import sqlite3
import re
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError
import asyncio

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إعدادات البوت
BOT_TOKEN = "7617675795:AAHm7Mi4KDvFCPDktFq8H7JtC0A3G7Ha0Ac"  # ضع توكن البوت هنا
CHANNEL_USERNAME = "@For3ABD"  # ضع اسم القناة هنا
ADMIN_IDS = [7657811161]  # ضع معرف المطور هنا

# النصوص متعددة اللغات
TEXTS = {
    'ar': {
        'choose_language': "🌍 اختر لغتك من فضلك:\n\nPlease choose your language:",
        'language_set': "✅ تم تعيين اللغة العربية بنجاح!",
        'subscribe_channel': "للاستفادة من البوت، يجب عليك الاشتراك في القناة أولاً:\n{channel}\n\nبعد الاشتراك، اضغط على 'تحقق من الاشتراك'",
        'subscription_verified': "✅ شكراً لك {name}!\n\nتم التحقق من اشتراكك بنجاح 🎉\n\nالآن أرسل تاريخ ميلادك لحساب عمرك!\nمثال: 2000/1/15",
        'not_subscribed': "❌ لم تقم بالاشتراك في القناة بعد!",
        'subscribe_button': "🔗 اشترك في القناة",
        'check_subscription': "✅ تحقق من الاشتراك",
        'welcome_message': """🎉 مرحباً {name}! 

🎂 **بوت حاسبة العمر المطور**

✨ **المميزات:**
🔸 حساب العمر بدقة متناهية
🔸 معرفة يوم الميلاد
🔸 حساب موعد عيد الميلاد القادم
🔸 إحصائيات مفصلة عن عمرك

📝 **طريقة الاستخدام:**
أرسل تاريخ ميلادك بأي من هذه الصيغ:
• 2000/5/15
• 2000-5-15  
• 15/5/2000
• 15-5-2000

🚀 ابدأ الآن بإرسال تاريخ ميلادك!""",
        'invalid_date': "❌ **صيغة التاريخ غير صحيحة!**\n\n📝 الصيغ المدعومة:\n• 2000/5/15\n• 2000-5-15\n• 15/5/2000\n• 15-5-2000\n\nجرب مرة أخرى!",
        'future_date': "❌ التاريخ في المستقبل! أدخل تاريخ ميلاد صحيح.",
        'old_date': "❌ التاريخ قديم جداً! أدخل تاريخ ميلاد واقعي.",
        'age_result': """🎂 **تم حساب عمرك بنجاح!**

📅 **تاريخ الميلاد:** {birth_date}
🌟 **يوم الميلاد:** {birth_day}

⏰ **العمر الحالي:**
🔸 {years} سنة و {months} شهر و {days} يوم

🎉 **موعد عيد الميلاد القادم:**
🔸 خلال {next_months} شهر و {next_days} يوم
🔸 {next_hours} ساعة و {next_minutes} دقيقة

📊 **إحصائيات مفصلة:**
📆 إجمالي: {total_months:,} شهر
📆 إجمالي: {total_weeks:,} أسبوع  
📆 إجمالي: {total_days:,} يوم
⏰ إجمالي: {total_hours:,} ساعة
⌚ إجمالي: {total_minutes:,} دقيقة

✨ **شكراً لاستخدام البوت!**

🌍 لتغيير اللغة ارسل: /lg""",
        'banned': "❌ أنت محظور من استخدام البوت!",
        'must_subscribe': "❌ يجب عليك الاشتراك في القناة أولاً للاستفادة من البوت!",
        'weekdays': {
            'Monday': 'الإثنين', 'Tuesday': 'الثلاثاء', 'Wednesday': 'الأربعاء',
            'Thursday': 'الخميس', 'Friday': 'الجمعة', 'Saturday': 'السبت', 'Sunday': 'الأحد'
        },
        'admin_panel': "🛠 **لوحة التحكم**\n\nاختر العملية المطلوبة:",
        'last_users_button': "📊 آخر 50 مستخدم",
        'broadcast_button': "📢 إذاعة للجميع",
        'ban_button': "🚫 حظر مستخدم",
        'unban_button': "✅ إلغاء حظر"
    },
    'en': {
        'choose_language': "🌍 Please choose your language:\n\nاختر لغتك من فضلك:",
        'language_set': "✅ English language has been set successfully!",
        'subscribe_channel': "To use the bot, you must subscribe to the channel first:\n{channel}\n\nAfter subscribing, click 'Check Subscription'",
        'subscription_verified': "✅ Thank you {name}!\n\nYour subscription has been verified successfully 🎉\n\nNow send your birth date to calculate your age!\nExample: 2000/1/15",
        'not_subscribed': "❌ You haven't subscribed to the channel yet!",
        'subscribe_button': "🔗 Subscribe to Channel",
        'check_subscription': "✅ Check Subscription",
        'welcome_message': """🎉 Welcome {name}! 

🎂 **Advanced Age Calculator Bot**

✨ **Features:**
🔸 Precise age calculation
🔸 Birth day identification
🔸 Next birthday countdown
🔸 Detailed age statistics

📝 **How to use:**
Send your birth date in any of these formats:
• 2000/5/15
• 2000-5-15  
• 15/5/2000
• 15-5-2000

🚀 Start now by sending your birth date!""",
        'invalid_date': "❌ **Invalid date format!**\n\n📝 Supported formats:\n• 2000/5/15\n• 2000-5-15\n• 15/5/2000\n• 15-5-2000\n\nTry again!",
        'future_date': "❌ Date is in the future! Enter a valid birth date.",
        'old_date': "❌ Date is too old! Enter a realistic birth date.",
        'age_result': """🎂 **Your age has been calculated successfully!**

📅 **Birth Date:** {birth_date}
🌟 **Birth Day:** {birth_day}

⏰ **Current Age:**
🔸 {years} years, {months} months and {days} days

🎉 **Next Birthday:**
🔸 In {next_months} months and {next_days} days
🔸 {next_hours} hours and {next_minutes} minutes

📊 **Detailed Statistics:**
📆 Total: {total_months:,} months
📆 Total: {total_weeks:,} weeks  
📆 Total: {total_days:,} days
⏰ Total: {total_hours:,} hours
⌚ Total: {total_minutes:,} minutes

✨ **Thank you for using the bot!**

🌍 To change language send: /lg""",
        'banned': "❌ You are banned from using the bot!",
        'must_subscribe': "❌ You must subscribe to the channel first to use the bot!",
        'weekdays': {
            'Monday': 'Monday', 'Tuesday': 'Tuesday', 'Wednesday': 'Wednesday',
            'Thursday': 'Thursday', 'Friday': 'Friday', 'Saturday': 'Saturday', 'Sunday': 'Sunday'
        },
        'admin_panel': "🛠 **Admin Panel**\n\nChoose the required operation:",
        'last_users_button': "📊 Last 50 Users",
        'broadcast_button': "📢 Broadcast to All",
        'ban_button': "🚫 Ban User",
        'unban_button': "✅ Unban User"
    }
}

class AgeCalculatorBot:
    def __init__(self):
        self.init_database()
        
    def init_database(self):
        """إنشاء قاعدة البيانات والجداول"""
        self.conn = sqlite3.connect('bot_data.db', check_same_thread=False)
        cursor = self.conn.cursor()
        
        # جدول المستخدمين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                language TEXT DEFAULT 'ar',
                join_date TEXT,
                is_banned INTEGER DEFAULT 0
            )
        ''')
        
        # جدول الدخول الأخير
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS last_activity (
                user_id INTEGER,
                username TEXT,
                first_name TEXT,
                activity_time TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        self.conn.commit()

    def add_user(self, user_id, username, first_name, language='ar'):
        """إضافة مستخدم جديد"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, language, join_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, language, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            self.conn.commit()
    
    def set_user_language(self, user_id, language):
        """تعيين لغة المستخدم"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (language, user_id))
        if cursor.rowcount == 0:
            cursor.execute('''
                INSERT INTO users (user_id, language, join_date)
                VALUES (?, ?, ?)
            ''', (user_id, language, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        self.conn.commit()
    
    def get_user_language(self, user_id):
        """الحصول على لغة المستخدم"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 'ar'
    
    def update_last_activity(self, user_id, username, first_name):
        """تحديث آخر نشاط للمستخدم"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM last_activity WHERE user_id = ?', (user_id,))
        cursor.execute('''
            INSERT INTO last_activity (user_id, username, first_name, activity_time)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        self.conn.commit()
    
    def is_user_banned(self, user_id):
        """التحقق من حظر المستخدم"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] == 1 if result else False
    
    def ban_user(self, user_id):
        """حظر مستخدم"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (user_id,))
        self.conn.commit()
    
    def unban_user(self, user_id):
        """إلغاء حظر مستخدم"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_banned = 0 WHERE user_id = ?', (user_id,))
        self.conn.commit()
    
    def get_last_50_users(self):
        """الحصول على آخر 50 مستخدم"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT user_id, username, first_name, activity_time 
            FROM last_activity 
            ORDER BY activity_time DESC 
            LIMIT 50
        ''')
        return cursor.fetchall()
    
    def get_all_users(self):
        """الحصول على جميع المستخدمين للإذاعة"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE is_banned = 0')
        return [row[0] for row in cursor.fetchall()]

# إنشاء كائن البوت
bot = AgeCalculatorBot()

def get_text(user_id, key):
    """الحصول على النص بلغة المستخدم"""
    language = bot.get_user_language(user_id)
    return TEXTS[language].get(key, TEXTS['ar'].get(key, key))

async def check_channel_subscription(update: Update, user_id: int):
    """التحقق من الاشتراك في القناة"""
    try:
        member = await update.get_bot().get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except:
        return False

def parse_date(date_string):
    """تحليل التاريخ من النص"""
    # إزالة المسافات
    date_string = date_string.strip()
    
    # أنماط التاريخ المدعومة
    patterns = [
        r'^(\d{4})[/-_](\d{1,2})[/-_](\d{1,2})$',  # YYYY/MM/DD أو YYYY-MM-DD
        r'^(\d{1,2})[/-_](\d{1,2})[/-_](\d{4})$',  # DD/MM/YYYY أو DD-MM-YYYY
    ]
    
    for pattern in patterns:
        match = re.match(pattern, date_string)
        if match:
            groups = match.groups()
            if len(groups[0]) == 4:  # السنة أولاً
                year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
            else:  # اليوم أولاً
                day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
            
            try:
                return datetime(year, month, day)
            except ValueError:
                return None
    
    return None

def calculate_age(birth_date):
    """حساب العمر بدقة"""
    now = datetime.now()
    
    # حساب العمر بالسنوات والشهور والأيام
    years = now.year - birth_date.year
    months = now.month - birth_date.month
    days = now.day - birth_date.day
    
    if days < 0:
        months -= 1
        # الحصول على عدد أيام الشهر السابق
        if now.month == 1:
            prev_month = 12
            year_for_prev_month = now.year - 1
        else:
            prev_month = now.month - 1
            year_for_prev_month = now.year
        
        days_in_prev_month = (datetime(year_for_prev_month, prev_month + 1, 1) - timedelta(days=1)).day if prev_month != 12 else 31
        days += days_in_prev_month
    
    if months < 0:
        years -= 1
        months += 12
    
    # حساب إجمالي الأشهر والأسابيع والأيام والساعات والدقائق
    total_days = (now - birth_date).days
    total_months = years * 12 + months
    total_weeks = total_days // 7
    total_hours = total_days * 24 + now.hour - birth_date.hour
    total_minutes = total_hours * 60 + now.minute - birth_date.minute
    
    # يوم الأسبوع الذي ولد فيه
    birth_weekday = birth_date.strftime('%A')
    
    # حساب موعد عيد الميلاد القادم
    next_birthday = datetime(now.year, birth_date.month, birth_date.day)
    if next_birthday <= now:
        next_birthday = datetime(now.year + 1, birth_date.month, birth_date.day)
    
    time_to_birthday = next_birthday - now
    birthday_months = 0
    birthday_days = time_to_birthday.days
    birthday_hours = time_to_birthday.seconds // 3600
    birthday_minutes = (time_to_birthday.seconds % 3600) // 60
    
    # تحويل الأيام إلى شهور وأيام
    temp_date = now
    while temp_date.replace(month=temp_date.month + 1 if temp_date.month < 12 else 1, 
                          year=temp_date.year + (1 if temp_date.month == 12 else 0)) <= next_birthday:
        birthday_months += 1
        if temp_date.month == 12:
            temp_date = temp_date.replace(year=temp_date.year + 1, month=1)
        else:
            temp_date = temp_date.replace(month=temp_date.month + 1)
    
    birthday_days = (next_birthday - temp_date).days
    
    return {
        'years': years,
        'months': months,
        'days': days,
        'total_months': total_months,
        'total_weeks': total_weeks,
        'total_days': total_days,
        'total_hours': total_hours,
        'total_minutes': total_minutes,
        'birth_weekday': birth_weekday,
        'next_birthday_months': birthday_months,
        'next_birthday_days': birthday_days,
        'next_birthday_hours': birthday_hours,
        'next_birthday_minutes': birthday_minutes
    }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البداية مع اختيار اللغة"""
    user = update.effective_user
    
    # التحقق من الحظر
    if bot.is_user_banned(user.id):
        await update.message.reply_text(get_text(user.id, 'banned'))
        return
    
    # إضافة المستخدم (بدون لغة محددة أولاً)
    bot.add_user(user.id, user.username, user.first_name)
    
    # التحقق إذا كان المستخدم اختار لغة من قبل ولديه اشتراك
    cursor = bot.conn.cursor()
    cursor.execute('SELECT language FROM users WHERE user_id = ?', (user.id,))
    user_data = cursor.fetchone()
    
    if user_data and user_data[0]:  # إذا كان لديه لغة محفوظة
        # التحقق من الاشتراك مباشرة
        if await check_channel_subscription(update, user.id):
            bot.update_last_activity(user.id, user.username, user.first_name)
            welcome_text = get_text(user.id, 'welcome_message').format(name=user.first_name)
            await update.message.reply_text(welcome_text, parse_mode='Markdown')
            return
        else:
            # إظهار رسالة الاشتراك
            keyboard = [
                [InlineKeyboardButton(get_text(user.id, 'subscribe_button'), 
                                    url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
                [InlineKeyboardButton(get_text(user.id, 'check_subscription'), 
                                    callback_data="check_subscription")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            message_text = get_text(user.id, 'subscribe_channel').format(channel=CHANNEL_USERNAME)
            await update.message.reply_text(message_text, reply_markup=reply_markup)
            return
    
    # عرض خيارات اللغة للمستخدمين الجدد فقط
    keyboard = [
        [InlineKeyboardButton("العربية 🇸🇦", callback_data="lang_ar")],
        [InlineKeyboardButton("English 🇺🇸", callback_data="lang_en")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        TEXTS['ar']['choose_language'],
        reply_markup=reply_markup
    )

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج اختيار اللغة"""
    query = update.callback_query
    user = query.from_user
    
    if query.data.startswith("lang_"):
        language = query.data.split("_")[1]
        bot.set_user_language(user.id, language)
        
        # إشعار بتعيين اللغة
        await query.edit_message_text(get_text(user.id, 'language_set'))
        
        # انتظار قصير ثم التحقق من الاشتراك
        await asyncio.sleep(1)
        
        # التحقق من الاشتراك في القناة
        if not await check_channel_subscription(update, user.id):
            keyboard = [
                [InlineKeyboardButton(get_text(user.id, 'subscribe_button'), 
                                    url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
                [InlineKeyboardButton(get_text(user.id, 'check_subscription'), 
                                    callback_data="check_subscription")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            message_text = get_text(user.id, 'subscribe_channel').format(channel=CHANNEL_USERNAME)
            await query.message.reply_text(message_text, reply_markup=reply_markup)
            return
        
        # إذا كان مشترك، عرض الترحيب
        bot.update_last_activity(user.id, user.username, user.first_name)
        welcome_text = get_text(user.id, 'welcome_message').format(name=user.first_name)
        await query.message.reply_text(welcome_text, parse_mode='Markdown')

async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر تغيير اللغة"""
    user = update.effective_user
    
    # التحقق من الحظر
    if bot.is_user_banned(user.id):
        await update.message.reply_text(get_text(user.id, 'banned'))
        return
    
    # عرض خيارات اللغة
    keyboard = [
        [InlineKeyboardButton("العربية 🇸🇦", callback_data="lang_ar")],
        [InlineKeyboardButton("English 🇺🇸", callback_data="lang_en")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    current_lang = bot.get_user_language(user.id)
    if current_lang == 'ar':
        text = "🌍 اختر لغتك الجديدة:"
    else:
        text = "🌍 Choose your new language:"
    
    await update.message.reply_text(text, reply_markup=reply_markup)

async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التحقق من الاشتراك عبر الزر"""
    query = update.callback_query
    user = query.from_user
    
    if await check_channel_subscription(update, user.id):
        # تحديث النشاط
        bot.update_last_activity(user.id, user.username, user.first_name)
        
        # رسالة التأكيد
        confirmation_text = get_text(user.id, 'subscription_verified').format(name=user.first_name)
        await query.edit_message_text(confirmation_text)
    else:
        await query.answer(get_text(user.id, 'not_subscribed'), show_alert=True)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لوحة تحكم الأدمن"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ غير مصرح لك بالوصول!")
        return
    
    user_id = update.effective_user.id
    
    keyboard = [
        [InlineKeyboardButton(get_text(user_id, 'last_users_button'), callback_data="last_users")],
        [InlineKeyboardButton(get_text(user_id, 'broadcast_button'), callback_data="broadcast")],
        [InlineKeyboardButton(get_text(user_id, 'ban_button'), callback_data="ban_user")],
        [InlineKeyboardButton(get_text(user_id, 'unban_button'), callback_data="unban_user")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        get_text(user_id, 'admin_panel'),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أزرار لوحة التحكم"""
    query = update.callback_query
    
    if query.from_user.id not in ADMIN_IDS:
        await query.answer("❌ غير مصرح لك!", show_alert=True)
        return
    
    if query.data == "last_users":
        users = bot.get_last_50_users()
        if not users:
            await query.edit_message_text("📊 لا يوجد مستخدمون حتى الآن")
            return
        
        message = "📊 **آخر 50 مستخدم:**\n\n"
        for i, (user_id, username, first_name, activity_time) in enumerate(users[:50], 1):
            username_text = f"@{username}" if username else "بدون معرف"
            message += f"{i}. {first_name} ({username_text})\n   🆔 {user_id}\n   🕐 {activity_time}\n\n"
        
        if len(message) > 4000:
            # تقسيم الرسالة إذا كانت طويلة
            messages = [message[i:i+4000] for i in range(0, len(message), 4000)]
            await query.edit_message_text(messages[0], parse_mode='Markdown')
            for msg in messages[1:]:
                await context.bot.send_message(query.message.chat_id, msg, parse_mode='Markdown')
        else:
            await query.edit_message_text(message, parse_mode='Markdown')
    
    elif query.data == "broadcast":
        await query.edit_message_text("📢 أرسل الرسالة التي تريد إذاعتها للجميع:")
        context.user_data['waiting_broadcast'] = True
    
    elif query.data == "ban_user":
        await query.edit_message_text("🚫 أرسل معرف المستخدم الذي تريد حظره:")
        context.user_data['waiting_ban'] = True
    
    elif query.data == "unban_user":
        await query.edit_message_text("✅ أرسل معرف المستخدم الذي تريد إلغاء حظره:")
        context.user_data['waiting_unban'] = True

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الرسائل النصية"""
    user = update.effective_user
    text = update.message.text
    
    # التحقق من الحظر
    if bot.is_user_banned(user.id):
        await update.message.reply_text(get_text(user.id, 'banned'))
        return
    
    # معالجة أوامر الأدمن
    if user.id in ADMIN_IDS:
        if context.user_data.get('waiting_broadcast'):
            users = bot.get_all_users()
            success_count = 0
            failed_count = 0
            
            await update.message.reply_text(f"📢 بدء الإذاعة لـ {len(users)} مستخدم...")
            
            for user_id in users:
                try:
                    await context.bot.send_message(user_id, f"📢 **رسالة من الإدارة:**\n\n{text}", parse_mode='Markdown')
                    success_count += 1
                    await asyncio.sleep(0.05)  # تجنب حدود التلغرام
                except:
                    failed_count += 1
            
            await update.message.reply_text(
                f"✅ **تم إكمال الإذاعة!**\n\n"
                f"📊 الإحصائيات:\n"
                f"✅ نجح: {success_count}\n"
                f"❌ فشل: {failed_count}"
            )
            context.user_data['waiting_broadcast'] = False
            return
        
        elif context.user_data.get('waiting_ban'):
            try:
                user_id = int(text)
                bot.ban_user(user_id)
                await update.message.reply_text(f"🚫 تم حظر المستخدم {user_id} بنجاح!")
            except ValueError:
                await update.message.reply_text("❌ معرف المستخدم غير صحيح!")
            context.user_data['waiting_ban'] = False
            return
        
        elif context.user_data.get('waiting_unban'):
            try:
                user_id = int(text)
                bot.unban_user(user_id)
                await update.message.reply_text(f"✅ تم إلغاء حظر المستخدم {user_id} بنجاح!")
            except ValueError:
                await update.message.reply_text("❌ معرف المستخدم غير صحيح!")
            context.user_data['waiting_unban'] = False
            return
    
    # التحقق من الاشتراك في القناة
    if not await check_channel_subscription(update, user.id):
        keyboard = [[InlineKeyboardButton(get_text(user.id, 'subscribe_button'), 
                                        url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
                   [InlineKeyboardButton(get_text(user.id, 'check_subscription'), 
                                       callback_data="check_subscription")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            get_text(user.id, 'must_subscribe'),
            reply_markup=reply_markup
        )
        return
    
    # تحديث نشاط المستخدم
    bot.update_last_activity(user.id, user.username, user.first_name)
    
    # تحليل التاريخ
    birth_date = parse_date(text)
    
    if not birth_date:
        await update.message.reply_text(
            get_text(user.id, 'invalid_date'),
            parse_mode='Markdown'
        )
        return
    
    # التحقق من صحة التاريخ
    now = datetime.now()
    if birth_date > now:
        await update.message.reply_text(get_text(user.id, 'future_date'))
        return
    
    if birth_date.year < 1900:
        await update.message.reply_text(get_text(user.id, 'old_date'))
        return
    
    # حساب العمر
    age_data = calculate_age(birth_date)
    
    # تنسيق الرسالة
    birth_date_formatted = birth_date.strftime('%Y/%m/%d')
    
    # الحصول على يوم الميلاد بلغة المستخدم
    weekdays = get_text(user.id, 'weekdays')
    birth_weekday = weekdays.get(age_data['birth_weekday'], age_data['birth_weekday'])
    
    # تنسيق رسالة النتيجة
    result_text = get_text(user.id, 'age_result').format(
        birth_date=birth_date_formatted,
        birth_day=birth_weekday,
        years=age_data['years'],
        months=age_data['months'],
        days=age_data['days'],
        next_months=age_data['next_birthday_months'],
        next_days=age_data['next_birthday_days'],
        next_hours=age_data['next_birthday_hours'],
        next_minutes=age_data['next_birthday_minutes'],
        total_months=age_data['total_months'],
        total_weeks=age_data['total_weeks'],
        total_days=age_data['total_days'],
        total_hours=age_data['total_hours'],
        total_minutes=age_data['total_minutes']
    )
    
    await update.message.reply_text(result_text, parse_mode='Markdown')

def main():
    """تشغيل البوت"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("lg", change_language))
    application.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    application.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="check_subscription"))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern="^(last_users|broadcast|ban_user|unban_user)$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 تم تشغيل البوت بنجاح!")
    print("⚙️ لوحة التحكم: /admin")
    print("🌍 دعم اللغات: العربية والإنجليزية")
    application.run_polling()

if __name__ == '__main__':
    main()