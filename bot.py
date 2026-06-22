# bot.py
import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# КОНФИГУРАЦИЯ
BOT_TOKEN = "8433976122:AAHTt7QNuJ1RBa7pSl5fR5xTBvVtSzylegg"  # Замени на свой токен
ADMIN_ID = 6800035717  # Твой Telegram ID (замени)

# Канал для подписки (BR Bost)
REQUIRED_CHANNELS = [
    {"id": -1004435342974, "name": "BR Bost", "link": "https://t.me/+iOo3EPgF4Mc4NmQy"}  # Замени на свои
]

# Бот для перехода (Star Blink) - просто ссылка
STAR_BLINK_BOT = "https://t.me/starblinkrobot?start=ref_6800035717"

# Ссылка на DonationAlerts
DONATION_URL = "https://www.donationalerts.com/r/nnmmnnwnnnnnn"

# Цена софта
PRICE = 200

# Хранилище подписанных пользователей
subscribed_users = set()

# Хранилище тикетов
tickets = {}
ticket_counter = 1

# Инициализация
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ============================================
# СОСТОЯНИЯ FSM
# ============================================

class PaymentStates(StatesGroup):
    waiting_for_payment = State()

class SupportStates(StatesGroup):
    waiting_for_question = State()

# ============================================
# КЛАВИАТУРЫ
# ============================================

def get_subscribe_keyboard():
    """Клавиатура для подписки (показывается сразу после /start)"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📌 Подписаться на BR Bost", 
            url=REQUIRED_CHANNELS[0]['link']
        )],
        [InlineKeyboardButton(
            text="⭐ Перейти в Star Blink", 
            url=STAR_BLINK_BOT
        )],
        [InlineKeyboardButton(
            text="✅ Я подписался и перешел", 
            callback_data="check_subscription"
        )]
    ])
    return keyboard

def get_main_keyboard():
    """Главная клавиатура (доступна только после подписки)"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить софт BR Bost", callback_data="buy_soft")],
        [InlineKeyboardButton(text="💬 Поддержка", callback_data="support")],
        [InlineKeyboardButton(text="ℹ️ О боте", callback_data="about")]
    ])
    return keyboard

def get_payment_keyboard():
    """Клавиатура оплаты"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить 200₽", url=DONATION_URL)],
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data="check_payment")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_payment")]
    ])
    return keyboard

def get_support_keyboard():
    """Клавиатура поддержки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❓ Задать вопрос", callback_data="ask_question")],
        [InlineKeyboardButton(text="📋 Мои тикеты", callback_data="my_tickets")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    return keyboard

def get_admin_keyboard():
    """Клавиатура для админа"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Все тикеты", callback_data="admin_all_tickets")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data="admin_confirm_payment")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    return keyboard

def get_admin_confirm_keyboard(user_id: int):
    """Клавиатура подтверждения оплаты для админа"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Подтвердить оплату", 
            callback_data=f"confirm_payment_{user_id}"
        )],
        [InlineKeyboardButton(
            text="❌ Отклонить", 
            callback_data=f"reject_payment_{user_id}"
        )],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
    ])
    return keyboard

def get_check_subscription_keyboard():
    """Клавиатура для повторной проверки подписки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📌 Подписаться на BR Bost", 
            url=REQUIRED_CHANNELS[0]['link']
        )],
        [InlineKeyboardButton(
            text="⭐ Перейти в Star Blink", 
            url=STAR_BLINK_BOT
        )],
        [InlineKeyboardButton(
            text="🔄 Проверить подписку", 
            callback_data="check_subscription"
        )]
    ])
    return keyboard

# ============================================
# ОБРАБОТЧИКИ КОМАНД
# ============================================

@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # Проверяем подписку
    if user_id in subscribed_users:
        # Уже подписан - показываем главное меню
        await show_main_menu(message)
    else:
        # Не подписан - показываем кнопку подписки
        await show_subscribe_required(message)

async def show_subscribe_required(message: types.Message):
    """Показать требование подписки"""
    text = f"""
👋 Привет, {message.from_user.first_name}!

🚫 ДОСТУП ЗАКРЫТ

Для использования бота необходимо:
1️⃣ Подписаться на канал BR Bost
2️⃣ Перейти в бота Star Blink

📌 После выполнения нажми кнопку "✅ Я подписался и перешел в бота по покупке/продаже Telegram Stars"

⚠️ Без подписки доступ к боту невозможен!
"""
    await message.answer(text, reply_markup=get_subscribe_keyboard())

async def show_main_menu(message: types.Message):
    """Показать главное меню (после подписки)"""
    text = f"""
👋 Привет, {message.from_user.first_name}!

✅ Подписка подтверждена!

Добро пожаловать в бот по покупке АПК софта BR Bost!

💰 Цена: {PRICE}₽

Используй кнопки ниже 👇
"""
    await message.answer(text, reply_markup=get_main_keyboard())

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    """Админ панель"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У тебя нет доступа к админ панели!")
        return
    
    await message.answer(
        "👑 Админ панель\n\nВыбери действие:",
        reply_markup=get_admin_keyboard()
    )

@dp.message(Command("cancel"))
async def cancel_command(message: types.Message, state: FSMContext):
    """Отмена текущего действия"""
    await state.clear()
    await message.answer(
        "❌ Действие отменено",
        reply_markup=get_main_keyboard()
    )

# ============================================
# ПРОВЕРКА ПОДПИСКИ
# ============================================

@dp.callback_query(F.data == "check_subscription")
async def check_subscription(callback: types.CallbackQuery):
    """Проверить подписку пользователя"""
    user_id = callback.from_user.id
    
    # Проверяем подписку на канал
    is_subscribed = await check_channel_subscription(user_id)
    
    if is_subscribed:
        # Добавляем в список подписанных
        subscribed_users.add(user_id)
        
        # Показываем главное меню
        text = f"""
✅ Подписка подтверждена!

👋 Привет, {callback.from_user.first_name}!

Добро пожаловать в бот по покупке АПК софта BR Bost!

💰 Цена: {PRICE}₽

Используй кнопки ниже 👇
"""
        await callback.message.edit_text(text, reply_markup=get_main_keyboard())
        await callback.answer("✅ Подписка подтверждена!")
    else:
        # Не подписан
        text = """
❌ ПОДПИСКА НЕ ПОДТВЕРЖДЕНА

Вы не подписаны на канал BR Bost!

📌 Выполните действия:
1️⃣ Подпишитесь на канал BR Bost
2️⃣ Перейдите в Star Blink
3️⃣ Нажмите "🔄 Проверить подписку"

⚠️ Без подписки доступ к боту невозможен!
"""
        await callback.message.edit_text(text, reply_markup=get_check_subscription_keyboard())
        await callback.answer("❌ Подписка не найдена")

# ============================================
# CALLBACK ОБРАБОТЧИКИ (ГЛАВНОЕ МЕНЮ)
# ============================================

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    user_id = callback.from_user.id
    
    # Проверяем подписку
    if user_id not in subscribed_users:
        await callback.message.edit_text(
            "🚫 Доступ закрыт. Требуется подписка!",
            reply_markup=get_subscribe_keyboard()
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "🏠 Главное меню",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "about")
async def about_bot(callback: types.CallbackQuery):
    """О боте"""
    user_id = callback.from_user.id
    
    # Проверяем подписку
    if user_id not in subscribed_users:
        await callback.message.edit_text(
            "🚫 Доступ закрыт. Требуется подписка!",
            reply_markup=get_subscribe_keyboard()
        )
        await callback.answer()
        return
    
    text = f"""
ℹ️ О БОТЕ

🤖 Бот для покупки АПК софта
💰 Цена: {PRICE}₽
📅 Создан: 2025


📌 Требования:
• Подписка на канал BR Bost
• Оплата {PRICE}₽

👤 Разработчик: @venesen
💬 Поддержка: нажми кнопку "Поддержка"
"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

# ============================================
# ПОКУПКА СОФТА
# ============================================

@dp.callback_query(F.data == "buy_soft")
async def start_buy_process(callback: types.CallbackQuery, state: FSMContext):
    """Начать процесс покупки"""
    user_id = callback.from_user.id
    
    # Проверяем подписку
    if user_id not in subscribed_users:
        await callback.message.edit_text(
            "🚫 Доступ закрыт. Требуется подписка!",
            reply_markup=get_subscribe_keyboard()
        )
        await callback.answer()
        return
    
    await state.set_state(PaymentStates.waiting_for_payment)
    await state.update_data(user_id=user_id)
    
    payment_text = f"""
💳 ОПЛАТА СОФТА

💰 Сумма: {PRICE}₽

✅ Подписка подтверждена!

📌 Для оплаты:
1. Нажми кнопку "💳 Оплатить {PRICE}₽"
2. В комментарии укажи свой ID: <code>{user_id}</code>
3. После оплаты нажми "✅ Я оплатил"

⚠️ Чек проверяется до 3 часов (обычно днём до 1 часа)
"""
    await callback.message.edit_text(
        payment_text,
        reply_markup=get_payment_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data == "check_payment")
async def check_payment(callback: types.CallbackQuery, state: FSMContext):
    """Проверка оплаты"""
    user_id = callback.from_user.id
    
    # Проверяем подписку
    if user_id not in subscribed_users:
        await callback.message.edit_text(
            "🚫 Доступ закрыт. Требуется подписка!",
            reply_markup=get_subscribe_keyboard()
        )
        await callback.answer()
        return
    
    # Отправляем уведомление админу
    await bot.send_message(
        ADMIN_ID,
        f"💳 НОВАЯ ОПЛАТА\n\n"
        f"👤 Пользователь: @{callback.from_user.username or 'Не указан'}\n"
        f"🆔 ID: {user_id}\n"
        f"💰 Сумма: {PRICE}₽\n"
        f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"Нажми кнопку для подтверждения:",
        reply_markup=get_admin_confirm_keyboard(user_id)
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ Ожидание подтверждения", callback_data="waiting")],
        [InlineKeyboardButton(text="💬 Поддержка", callback_data="support")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(
        f"""
⏳ ОПЛАТА ОТПРАВЛЕНА НА ПРОВЕРКУ

💰 Сумма: {PRICE}₽
🆔 Ваш ID: <code>{user_id}</code>

⏰ Ожидайте подтверждения до 24 часов
📩 Уведомление придет в этот чат

Если возникли проблемы - напишите в поддержку
""",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: types.CallbackQuery, state: FSMContext):
    """Отмена оплаты"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Оплата отменена. Возврат в главное меню.",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

# ============================================
# АДМИН ПОДТВЕРЖДЕНИЕ ОПЛАТЫ
# ============================================

@dp.callback_query(lambda c: c.data and c.data.startswith('confirm_payment_'))
async def admin_confirm_payment(callback: types.CallbackQuery):
    """Админ подтверждает оплату"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа!")
        return
    
    user_id = int(callback.data.split('_')[2])
    
    # Отправляем пользователю ссылку на софт
    await bot.send_message(
        user_id,
        f"""
✅ ОПЛАТА ПОДТВЕРЖДЕНА!

🎉 Ссылка на скачивание софта:
https://t.me/venesen

📌 Инструкция:
1. Скачай АПК файл
2. Установи на устройство
3. Запусти и наслаждайся!

⚠️ Софт привязан к вашему устройству
Не передавайте файл другим!
"""
    )
    
    await callback.message.edit_text(
        f"✅ Оплата для пользователя {user_id} подтверждена!\n\nСофт отправлен.",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data and c.data.startswith('reject_payment_'))
async def admin_reject_payment(callback: types.CallbackQuery):
    """Админ отклоняет оплату"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа!")
        return
    
    user_id = int(callback.data.split('_')[2])
    
    await bot.send_message(
        user_id,
        f"❌ ОПЛАТА ОТКЛОНЕНА\n\n"
        f"Пожалуйста, проверьте правильность оплаты и попробуйте снова.\n"
        f"Если у вас возникли вопросы - напишите в поддержку."
    )
    
    await callback.message.edit_text(
        f"❌ Оплата для пользователя {user_id} отклонена.",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()

# ============================================
# ПОДДЕРЖКА (ТИКЕТЫ)
# ============================================

@dp.callback_query(F.data == "support")
async def support_menu(callback: types.CallbackQuery):
    """Меню поддержки"""
    user_id = callback.from_user.id
    
    # Проверяем подписку
    if user_id not in subscribed_users:
        await callback.message.edit_text(
            "🚫 Доступ закрыт. Требуется подписка!",
            reply_markup=get_subscribe_keyboard()
        )
        await callback.answer()
        return
    
    if callback.from_user.id == ADMIN_ID:
        await callback.message.edit_text(
            "👑 Админ панель поддержки",
            reply_markup=get_admin_keyboard()
        )
    else:
        await callback.message.edit_text(
            "💬 СЛУЖБА ПОДДЕРЖКИ\n\n"
            "Выбери действие:",
            reply_markup=get_support_keyboard()
        )
    await callback.answer()

@dp.callback_query(F.data == "ask_question")
async def ask_question(callback: types.CallbackQuery, state: FSMContext):
    """Начать создание тикета"""
    user_id = callback.from_user.id
    
    # Проверяем подписку
    if user_id not in subscribed_users:
        await callback.message.edit_text(
            "🚫 Доступ закрыт. Требуется подписка!",
            reply_markup=get_subscribe_keyboard()
        )
        await callback.answer()
        return
    
    await state.set_state(SupportStates.waiting_for_question)
    await callback.message.edit_text(
        "✍️ Напиши свой вопрос.\n\n"
        "Опиши проблему подробно.\n\n"
        "📌 Для отмены нажми /cancel"
    )
    await callback.answer()

@dp.message(SupportStates.waiting_for_question)
async def process_question(message: types.Message, state: FSMContext):
    """Обработка вопроса пользователя"""
    global ticket_counter
    
    user_id = message.from_user.id
    
    # Проверяем подписку
    if user_id not in subscribed_users:
        await message.answer(
            "🚫 Доступ закрыт. Требуется подписка!",
            reply_markup=get_subscribe_keyboard()
        )
        await state.clear()
        return
    
    question = message.text
    
    ticket_num = ticket_counter
    ticket_counter += 1
    
    tickets[ticket_num] = {
        "user_id": user_id,
        "username": message.from_user.username or "Не указан",
        "question": question,
        "status": "open",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "messages": []
    }
    
    await message.answer(
        f"✅ Тикет #{ticket_num} создан!\n\n"
        f"Твой вопрос:\n{question}\n\n"
        f"⏳ Ожидай ответа в этом чате."
    )
    
    await bot.send_message(
        ADMIN_ID,
        f"🆕 НОВЫЙ ТИКЕТ #{ticket_num}\n\n"
        f"👤 @{tickets[ticket_num]['username']}\n"
        f"🆔 {user_id}\n"
        f"📅 {tickets[ticket_num]['created']}\n\n"
        f"❓ {question}\n\n"
        f"📌 Используй /answer_{ticket_num} текст"
    )
    
    await state.clear()

@dp.callback_query(F.data == "my_tickets")
async def my_tickets(callback: types.CallbackQuery):
    """Показать тикеты пользователя"""
    user_id = callback.from_user.id
    
    # Проверяем подписку
    if user_id not in subscribed_users:
        await callback.message.edit_text(
            "🚫 Доступ закрыт. Требуется подписка!",
            reply_markup=get_subscribe_keyboard()
        )
        await callback.answer()
        return
    
    user_tickets = []
    for num, ticket in tickets.items():
        if ticket["user_id"] == user_id:
            user_tickets.append(num)
    
    if not user_tickets:
        await callback.message.edit_text(
            "📋 У тебя нет тикетов.",
            reply_markup=get_support_keyboard()
        )
        await callback.answer()
        return
    
    text = "📋 ТВОИ ТИКЕТЫ:\n\n"
    for num in user_tickets:
        ticket = tickets[num]
        status_emoji = "🟢" if ticket["status"] == "open" else "🔴"
        text += f"{status_emoji} #{num} - {ticket['status']}\n"
        text += f"   📅 {ticket['created']}\n"
        text += f"   ❓ {ticket['question'][:40]}...\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="support")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

# ============================================
# АДМИН КОМАНДЫ
# ============================================

@dp.message(lambda msg: msg.text and msg.text.startswith('/answer_'))
async def admin_answer(message: types.Message):
    """Ответ админа на тикет"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Нет доступа!")
        return
    
    try:
        parts = message.text.split(' ', 1)
        ticket_num = int(parts[0].replace('/answer_', ''))
        answer_text = parts[1] if len(parts) > 1 else "Ответ не указан"
    except:
        await message.answer("❌ Неверный формат!\nИспользуй: /answer_123 текст ответа")
        return
    
    if ticket_num not in tickets:
        await message.answer(f"❌ Тикет #{ticket_num} не найден!")
        return
    
    ticket = tickets[ticket_num]
    user_id = ticket["user_id"]
    
    try:
        await bot.send_message(
            user_id,
            f"📩 ОТВЕТ НА ТИКЕТ #{ticket_num}\n\n"
            f"{answer_text}\n\n"
            f"📌 Если остались вопросы - просто напиши в этот чат."
        )
      