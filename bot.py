import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import random
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Константы
ADMIN_ID = 1449276772
BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = 'postgresql://postgres:jUGJtRdVtAkahZBRBZMlpIICrkDfuuhq@junction.proxy.rlwy.net:19226/railway'

# Подключение к базе данных
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Модели базы данных
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    username = Column(String)
    balance = Column(Float, default=5000)
    rating = Column(Integer, default=0)
    clan = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

class GameLog(Base):
    __tablename__ = 'game_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    game_type = Column(String)
    bet = Column(Float)
    result = Column(String)
    profit = Column(Float)
    played_at = Column(DateTime, default=datetime.utcnow)

class SupportTicket(Base):
    __tablename__ = 'support_tickets'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    username = Column(String)
    message = Column(String)
    status = Column(String, default='open')  # open, answered, closed
    created_at = Column(DateTime, default=datetime.utcnow)
    answer = Column(String, nullable=True)
    answered_at = Column(DateTime, nullable=True)

# Создание таблиц
Base.metadata.create_all(engine)

# Токен бота
TOKEN = os.getenv('BOT_TOKEN')

def get_or_create_user(session, user_id, username):
    user = session.query(User).filter_by(user_id=user_id).first()
    if not user:
        user = User(user_id=user_id, username=username)
        session.add(user)
        session.commit()
    return user

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    user = get_or_create_user(session, update.effective_user.id, update.effective_user.username)
    session.close()

    keyboard = [
        ["💎 Основное", "🚀 Игры"],
        ["😎 Персонаж"],
        ["🃏 Покер", "📊 Биржа"],
        ["⚙️ Настроить", "📒 Профиль", "🔥 Донат"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"👋 Привет, {update.effective_user.first_name}!\n"
        "Я - твой новый игровой друг.\n\n"
        "🎉 Здесь тебя ждёт море веселья и множество игр, чтобы каждый твой день был ярче! 🥰\n\n"
        "🚀 Готов отправиться в увлекательное приключение? Просто выбери действие ниже и вперёд! 👇",
        reply_markup=reply_markup
    )

async def show_games_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🃏 Покер"],
        ["🎰 Лотерея", "🎰 Казино", "🎲 Рулетка"],
        ["📈 Краш", "📊 Трейд", "💰 Слоты"],
        ["🪙 Монетка", "♠️ Блэкджек", "❌ Крестики-нолики"],
        ["🔢 2048", "✏️ Викторина", "❓ Загадки"],
        ["◀️ В главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите игру:", reply_markup=reply_markup)

async def show_blackjack_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("▶️ Начать игру", callback_data="blackjack_start"),
            InlineKeyboardButton("❓ Помощь", callback_data="blackjack_help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🃏 Блэкджек\n"
        "Минимальная ставка: 10$\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )

async def show_bet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    user = get_or_create_user(session, update.callback_query.from_user.id, update.callback_query.from_user.username)
    session.close()
    
    one_third = user.balance // 3
    two_thirds = (user.balance * 2) // 3
    
    keyboard = [
        [
            InlineKeyboardButton(f"{one_third}$", callback_data=f"blackjack_bet_{one_third}"),
            InlineKeyboardButton(f"{two_thirds}$", callback_data=f"blackjack_bet_{two_thirds}")
        ],
        [
            InlineKeyboardButton("Ва-банк", callback_data=f"blackjack_bet_{user.balance}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(
        f"💰 Ваш баланс: {user.balance}$\n"
        "Выберите сумму ставки:",
        reply_markup=reply_markup
    )

async def check_blackjack(update: Update, user, game, player_score):
    if player_score == 21:
        session = Session()
        bet = user.balance
        win_amount = bet * 2  # Выигрыш х2 при 21 очке
        user.balance += win_amount
        session.commit()
        session.close()
        
        # Формируем текст для карт
        player_cards_text = "🎫 Ваши карты:\n"
        for i, (card, suit) in enumerate(game.player_cards, 1):
            player_cards_text += f"⠀{i}⃣ {suit} {card}\n"
        
        dealer_cards_text = "🎟 Карты крупье:\n"
        dealer_card, dealer_suit = game.dealer_cards[0]
        dealer_cards_text += f"⠀1⃣ {dealer_suit} {dealer_card}"
        
        game_text = (
            f"💡 Ваши очки: {player_score} ⏐ Крупье: {game.calculate_score(game.dealer_cards)}\n"
            f"{player_cards_text}\n"
            f"{dealer_cards_text}\n"
            f"🌟 Блэкджек! Вы выиграли {win_amount}$!\n"
            f"💰 Баланс: {user.balance}$"
        )
        
        keyboard = [[InlineKeyboardButton("🔄 Играть заново", callback_data="blackjack_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.message.reply_text(game_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(game_text, reply_markup=reply_markup)
            
        return True
    return False

class BlackjackGame:
    def __init__(self):
        self.deck = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Валет', 'Дама', 'Король', 'Туз'] * 4
        self.suits = ['♠️', '♣️', '♥️', '♦']
        self.card_values = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
            'Валет': 10, 'Дама': 10, 'Король': 10, 'Туз': 11
        }
        self.player_cards = []
        self.dealer_cards = []

    def get_card(self):
        card = random.choice(self.deck)
        suit = random.choice(self.suits)
        return card, suit

    def calculate_score(self, cards):
        score = 0
        aces = 0
        for card, _ in cards:
            if card == 'Туз':
                aces += 1
            else:
                score += self.card_values[card]
        
        for _ in range(aces):
            if score + 11 <= 21:
                score += 11
            else:
                score += 1
        return score

async def start_blackjack_game(update: Update, context: ContextTypes.DEFAULT_TYPE, bet: int):
    query = update.callback_query
    session = Session()
    user = get_or_create_user(session, query.from_user.id, query.from_user.username)
    session.close()
    
    if bet > user.balance:
        await query.message.reply_text("Недостаточно средств!")
        return
    
    user.balance -= bet
    session = Session()
    session.add(GameLog(user_id=user.user_id, game_type='blackjack', bet=bet, result='in_progress'))
    session.commit()
    session.close()
    
    game = BlackjackGame()
    game.player_cards = [game.get_card(), game.get_card()]
    game.dealer_cards = [game.get_card()]
    
    player_score = game.calculate_score(game.player_cards)
    dealer_score = game.calculate_score(game.dealer_cards)
    
    # Проверяем на блэкджек
    if await check_blackjack(update, user, game, player_score):
        session = Session()
        game_log = session.query(GameLog).filter_by(user_id=user.user_id, result='in_progress').first()
        game_log.result = 'win'
        game_log.profit = bet * 2
        session.commit()
        session.close()
        return
    
    # Формируем текст для карт игрока
    player_cards_text = "🎫 Ваши карты:\n"
    for i, (card, suit) in enumerate(game.player_cards, 1):
        player_cards_text += f"⠀{i}⃣ {suit} {card}\n"
    
    # Формируем текст для карт крупье
    dealer_cards_text = "🎟 Карты крупье:\n"
    dealer_card, dealer_suit = game.dealer_cards[0]
    dealer_cards_text += f"⠀1⃣ {dealer_suit} {dealer_card}"
    
    game_text = (
        f"Игрок, Ваши очки: {player_score} ⏐ Крупье: {dealer_score}\n"
        f"{player_cards_text}\n"
        f"{dealer_cards_text}\n"
        f"💰 Баланс: {user.balance}$"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("➕ Ещё", callback_data="blackjack_hit"),
            InlineKeyboardButton("❌ Стоп", callback_data="blackjack_stand")
        ],
        [
            InlineKeyboardButton("💰 Удвоить", callback_data="blackjack_double")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(game_text, reply_markup=reply_markup)

async def blackjack_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "[💋 Ебем лесю] Игрок, описание команды:\n\n"
        "♣️ Суть игры «Блэкджек» (не путайте с игрой «21 очко») заключается в том, чтобы обыграть Вашего противника (бота), заполучив бóльшее количество очков, но не более 21.\n\n"
        "➖ Доступные действия:\n"
        "⠀➕ Ещё - взять случайную карту\n"
        "⠀❌ Стоп - закончить игру и узнать результат (или перейти к следующей руке)\n"
        "⠀💰 Удвоить - удвоить ставку, взять случайную карту и закончить игру (или перейти к следующей руке)\n"
        "⠀↔️ Разделить - удвоить ставку и разделить Вашу колоду на две руки\n"
        "⠀⠀ ➖ Доступно только при наличии двух одинаковых по достоинству карт (2 и 2, король и дама и т.д)\n"
        "⠀❤️ Застраховать - внести дополнительную ставку равную половине основной и застраховать Вашу колоду\n"
        "⠀⠀ ➖ Доступно только при наличии у бота туза\n"
        "⠀⠀ ➖ Если у бота «Блэкджек», Вам возвращается Ваша ставка полностью\n\n"
        "➖ Возможные исходы:\n"
        "⠀♣️ Блэкджек - 21 очко в начале игры, приз x2.5\n"
        "⠀✅ Победа - приз x2 (при страховке - х1.5)\n"
        "⠀❌ Проигрыш - ставка аннулируется\n"
        "⠀💸 Ничья - ставка возвращается (страховка не возвращается)\n\n"
        "♠️ Количество очков за каждые карты:\n"
        "⠀ ➖ Карты от двойки до десятки: 2-10 очков соответственно\n"
        "⠀ ➖ Карты «картинки» (король, дама, валет): 10 очков\n"
        "⠀ ➖ (❗️) Туз: 11 очков, НО если сумма текущих двух карт больше 10, то цена туза — 1 очко"
    )
    if update.callback_query:
        await update.callback_query.message.reply_text(help_text)
    else:
        await update.message.reply_text(help_text)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "blackjack_help":
        await blackjack_help(update, context)
    elif query.data == "blackjack_start":
        await show_bet_menu(update, context)
    elif query.data.startswith("blackjack_bet_"):
        bet = int(query.data.split("_")[2])
        await start_blackjack_game(update, context, bet)
    elif query.data == "blackjack_hit":
        # Добавить карту игроку
        session = Session()
        user = get_or_create_user(session, query.from_user.id, query.from_user.username)
        session.close()
        
        game = BlackjackGame()
        game.player_cards = [game.get_card(), game.get_card()]
        game.dealer_cards = [game.get_card()]
        
        game.player_cards.append(game.get_card())
        player_score = game.calculate_score(game.player_cards)
        
        # Проверяем на блэкджек
        if await check_blackjack(update, user, game, player_score):
            session = Session()
            game_log = session.query(GameLog).filter_by(user_id=user.user_id, result='in_progress').first()
            game_log.result = 'win'
            game_log.profit = user.balance * 2
            session.commit()
            session.close()
            return
        
        if player_score > 21:
            # Проигрыш
            session = Session()
            game_log = session.query(GameLog).filter_by(user_id=user.user_id, result='in_progress').first()
            game_log.result = 'lose'
            session.commit()
            session.close()
            
            player_cards_text = "🎫 Ваши карты:\n"
            for i, (card, suit) in enumerate(game.player_cards, 1):
                player_cards_text += f"⠀{i}⃣ {suit} {card}\n"
            
            dealer_cards_text = "🎟 Карты крупье:\n"
            dealer_card, dealer_suit = game.dealer_cards[0]
            dealer_cards_text += f"⠀1⃣ {dealer_suit} {dealer_card}"
            
            game_text = (
                f"💡 Ваши очки: {player_score} ⏐ Крупье: {game.calculate_score(game.dealer_cards)}\n"
                f"{player_cards_text}\n"
                f"{dealer_cards_text}\n"
                f"❌ Вы проиграли!\n"
                f"💰 Баланс: {user.balance}$"
            )
            
            keyboard = [[InlineKeyboardButton("🔄 Играть заново", callback_data="blackjack_start")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(game_text, reply_markup=reply_markup)
        else:
            # Продолжаем игру
            player_cards_text = "🎫 Ваши карты:\n"
            for i, (card, suit) in enumerate(game.player_cards, 1):
                player_cards_text += f"⠀{i}⃣ {suit} {card}\n"
            
            dealer_cards_text = "🎟 Карты крупье:\n"
            dealer_card, dealer_suit = game.dealer_cards[0]
            dealer_cards_text += f"⠀1⃣ {dealer_suit} {dealer_card}"
            
            game_text = (
                f"Игрок, Ваши очки: {player_score} ⏐ Крупье: {game.calculate_score(game.dealer_cards)}\n"
                f"{player_cards_text}\n"
                f"{dealer_cards_text}\n"
                f"💰 Баланс: {user.balance}$"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("➕ Ещё", callback_data="blackjack_hit"),
                    InlineKeyboardButton("❌ Стоп", callback_data="blackjack_stand")
                ],
                [
                    InlineKeyboardButton("💰 Удвоить", callback_data="blackjack_double")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(game_text, reply_markup=reply_markup)
    
    elif query.data == "blackjack_stand":
        # Игрок останавливается, дилер показывает карты
        session = Session()
        user = get_or_create_user(session, query.from_user.id, query.from_user.username)
        session.close()
        
        game = BlackjackGame()
        game.player_cards = [game.get_card(), game.get_card()]
        game.dealer_cards = [game.get_card()]
        
        dealer_score = game.calculate_score(game.dealer_cards)
        
        # Дилер берет карты, пока у него меньше 17
        while dealer_score < 17:
            game.dealer_cards.append(game.get_card())
            dealer_score = game.calculate_score(game.dealer_cards)
        
        player_score = game.calculate_score(game.player_cards)
        
        # Формируем текст для карт
        player_cards_text = "🎫 Ваши карты:\n"
        for i, (card, suit) in enumerate(game.player_cards, 1):
            player_cards_text += f"⠀{i}⃣ {suit} {card}\n"
        
        dealer_cards_text = "🎟 Карты крупье:\n"
        for i, (card, suit) in enumerate(game.dealer_cards, 1):
            dealer_cards_text += f"⠀{i}⃣ {suit} {card}\n"
        
        # Определяем победителя
        session = Session()
        game_log = session.query(GameLog).filter_by(user_id=user.user_id, result='in_progress').first()
        if dealer_score > 21 or player_score > dealer_score:
            # Игрок выиграл
            win_amount = user.balance * 2
            user.balance += win_amount
            game_log.result = 'win'
            game_log.profit = win_amount
            session.commit()
            session.close()
            result_text = f"✅ Вы выиграли {win_amount}$!"
        elif player_score < dealer_score:
            # Игрок проиграл
            game_log.result = 'lose'
            session.commit()
            session.close()
            result_text = f"❌ Вы проиграли {user.balance}$!"
        else:
            # Ничья
            user.balance += user.balance
            game_log.result = 'draw'
            session.commit()
            session.close()
            result_text = "🤝 Ничья! Ставка возвращена."
        
        game_text = (
            f"💡 Ваши очки: {player_score} ⏐ Крупье: {dealer_score}\n"
            f"{player_cards_text}\n"
            f"{dealer_cards_text}\n"
            f"{result_text}\n"
            f"💰 Баланс: {user.balance}$"
        )
        
        keyboard = [[InlineKeyboardButton("🔄 Играть заново", callback_data="blackjack_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(game_text, reply_markup=reply_markup)
    
    elif query.data == "blackjack_double":
        # Удвоить ставку и взять одну карту
        session = Session()
        user = get_or_create_user(session, query.from_user.id, query.from_user.username)
        session.close()
        
        bet = user.balance
        if user.balance < bet:  # Проверяем, хватает ли денег на удвоение
            await query.message.reply_text("Недостаточно средств для удвоения!")
            return
        
        # Удваиваем ставку
        user.balance -= bet
        session = Session()
        game_log = session.query(GameLog).filter_by(user_id=user.user_id, result='in_progress').first()
        game_log.bet = bet * 2
        session.commit()
        session.close()
        
        # Берем одну карту
        game = BlackjackGame()
        game.player_cards = [game.get_card(), game.get_card()]
        game.dealer_cards = [game.get_card()]
        
        game.player_cards.append(game.get_card())
        player_score = game.calculate_score(game.player_cards)
        
        # Сразу показываем карты дилера и определяем победителя
        dealer_score = game.calculate_score(game.dealer_cards)
        while dealer_score < 17:
            game.dealer_cards.append(game.get_card())
            dealer_score = game.calculate_score(game.dealer_cards)
        
        # Формируем текст для карт
        player_cards_text = "🎫 Ваши карты:\n"
        for i, (card, suit) in enumerate(game.player_cards, 1):
            player_cards_text += f"⠀{i}⃣ {suit} {card}\n"
        
        dealer_cards_text = "🎟 Карты крупье:\n"
        for i, (card, suit) in enumerate(game.dealer_cards, 1):
            dealer_cards_text += f"⠀{i}⃣ {suit} {card}\n"
        
        # Определяем победителя
        doubled_bet = bet * 2
        session = Session()
        game_log = session.query(GameLog).filter_by(user_id=user.user_id, result='in_progress').first()
        if player_score > 21:
            game_log.result = 'lose'
            session.commit()
            session.close()
            result_text = f"❌ Вы проиграли {doubled_bet}$!"
        elif dealer_score > 21 or player_score > dealer_score:
            win_amount = doubled_bet * 2
            user.balance += win_amount
            game_log.result = 'win'
            game_log.profit = win_amount
            session.commit()
            session.close()
            result_text = f"✅ Вы выиграли {win_amount}$!"
        elif player_score < dealer_score:
            game_log.result = 'lose'
            session.commit()
            session.close()
            result_text = f"❌ Вы проиграли {doubled_bet}$!"
        else:
            user.balance += doubled_bet
            game_log.result = 'draw'
            session.commit()
            session.close()
            result_text = "🤝 Ничья! Ставка возвращена."
        
        game_text = (
            f"💡 Ваши очки: {player_score} ⏐ Крупье: {dealer_score}\n"
            f"{player_cards_text}\n"
            f"{dealer_cards_text}\n"
            f"{result_text}\n"
            f"💰 Баланс: {user.balance}$"
        )
        
        keyboard = [[InlineKeyboardButton("🔄 Играть заново", callback_data="blackjack_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(game_text, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    
    if text == "помощь блэкджек":
        await blackjack_help(update, context)
    elif text == "🎲 рулетка":
        await show_roulette_menu(update, context)
    elif text == "♠️ блэкджек":
        await show_blackjack_menu(update, context)
    elif text == "🚀 игры":
        await show_games_menu(update, context)
    elif text == "💎 основное":
        await show_main_menu(update, context)
    elif text == "📒 профиль":
        await show_profile(update, context)
    elif text == "◀️ в главное меню":
        await start(update, context)

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    user = get_or_create_user(session, update.effective_user.id, update.effective_user.username)
    
    # Получаем статистику игр
    games_played = session.query(func.count(GameLog.id)).filter_by(user_id=user.user_id).scalar()
    total_profit = session.query(func.sum(GameLog.profit)).filter_by(user_id=user.user_id).scalar() or 0
    
    profile_text = (
        f"👤 Профиль игрока\n\n"
        f"🆔 ID: {user.user_id}\n"
        f"👤 Имя: {update.effective_user.first_name}\n"
        f"💰 Баланс: {user.balance}$\n"
        f"🏆 Рейтинг: {user.rating}\n"
        f"🎮 Игр сыграно: {games_played}\n"
        f"💵 Общий профит: {total_profit}$\n"
        f"📅 Дата регистрации: {user.created_at.strftime('%d.%m.%Y')}"
    )
    
    session.close()
    await update.message.reply_text(profile_text)

async def test_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Создаем сессию
        session = Session()
        
        # Проверяем, существует ли пользователь
        user = session.query(User).filter_by(user_id=update.effective_user.id).first()
        
        if user:
            await update.message.reply_text(
                f"✅ База данных работает!\n\n"
                f"Найден существующий пользователь:\n"
                f"ID: {user.user_id}\n"
                f"Имя: {user.username}\n"
                f"Баланс: {user.balance}\n"
                f"Создан: {user.created_at}"
            )
        else:
            # Создаем нового пользователя
            test_user = User(
                user_id=update.effective_user.id,
                username=update.effective_user.username or "Unknown",
                balance=5000.0
            )
            session.add(test_user)
            session.commit()
            
            await update.message.reply_text(
                f"✅ База данных работает!\n\n"
                f"Создан новый пользователь:\n"
                f"ID: {test_user.user_id}\n"
                f"Имя: {test_user.username}\n"
                f"Баланс: {test_user.balance}"
            )
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при работе с базой данных: {str(e)}")
    finally:
        session.close()

async def send_to_admin(message: str):
    """Отправляет сообщение админу"""
    try:
        await application.bot.send_message(chat_id=ADMIN_ID, text=message)
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения админу: {e}")

async def admin_give_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ-команда для выдачи баланса пользователю"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды")
        return

    try:
        # Формат команды: /give_balance user_id amount
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("❌ Использование: /give_balance user_id amount")
            return

        user_id = int(args[0])
        amount = float(args[1])

        session = Session()
        user = session.query(User).filter_by(user_id=user_id).first()
        
        if not user:
            await update.message.reply_text("❌ Пользователь не найден")
            return

        user.balance += amount
        session.commit()

        await update.message.reply_text(f"✅ Баланс пользователя {user.username} обновлен: {user.balance}")
        await application.bot.send_message(
            chat_id=user_id,
            text=f"💰 Ваш баланс был изменен администратором на {amount}!\nТекущий баланс: {user.balance}"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    finally:
        session.close()

async def admin_view_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ-команда для просмотра тикетов"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды")
        return

    session = Session()
    try:
        tickets = session.query(SupportTicket).filter_by(status='open').all()
        if not tickets:
            await update.message.reply_text("📫 Нет открытых тикетов")
            return

        for ticket in tickets:
            await update.message.reply_text(
                f"🎫 Тикет #{ticket.id}\n"
                f"От: {ticket.username} (ID: {ticket.user_id})\n"
                f"Сообщение: {ticket.message}\n"
                f"Статус: {ticket.status}\n"
                f"Создан: {ticket.created_at}\n\n"
                f"Чтобы ответить используйте:\n"
                f"/answer_ticket {ticket.id} ваш_ответ"
            )
    finally:
        session.close()

async def admin_answer_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ-команда для ответа на тикет"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет прав для выполнения этой команды")
        return

    try:
        # Формат команды: /answer_ticket ticket_id answer_text
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("❌ Использование: /answer_ticket ticket_id answer_text")
            return

        ticket_id = int(args[0])
        answer = ' '.join(args[1:])

        session = Session()
        ticket = session.query(SupportTicket).filter_by(id=ticket_id).first()
        
        if not ticket:
            await update.message.reply_text("❌ Тикет не найден")
            return

        ticket.status = 'answered'
        ticket.answer = answer
        ticket.answered_at = datetime.utcnow()
        session.commit()

        await update.message.reply_text(f"✅ Ответ на тикет #{ticket_id} отправлен")
        await application.bot.send_message(
            chat_id=ticket.user_id,
            text=f"📬 Получен ответ на ваш тикет #{ticket.id}:\n\n"
                 f"Ваш вопрос: {ticket.message}\n"
                 f"Ответ: {answer}"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    finally:
        session.close()

async def create_support_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание тикета в техподдержку"""
    try:
        message = ' '.join(context.args)
        if not message:
            await update.message.reply_text(
                "❌ Пожалуйста, добавьте ваше сообщение после команды\n"
                "Пример: /support У меня проблема с игрой"
            )
            return

        session = Session()
        ticket = SupportTicket(
            user_id=update.effective_user.id,
            username=update.effective_user.username,
            message=message
        )
        session.add(ticket)
        session.commit()

        await update.message.reply_text(
            f"✅ Ваш тикет #{ticket.id} создан!\n"
            f"Мы ответим вам как можно скорее."
        )

        # Уведомляем админа
        await send_to_admin(
            f"📬 Новый тикет #{ticket.id}\n"
            f"От: {ticket.username} (ID: {ticket.user_id})\n"
            f"Сообщение: {message}"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при создании тикета: {str(e)}")
    finally:
        session.close()

def main():
    global application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("games", show_games_menu))
    application.add_handler(CommandHandler("profile", show_profile))
    application.add_handler(CommandHandler("help", blackjack_help))
    application.add_handler(CommandHandler("test_db", test_db))
    
    # Админ команды
    application.add_handler(CommandHandler("give_balance", admin_give_balance))
    application.add_handler(CommandHandler("tickets", admin_view_tickets))
    application.add_handler(CommandHandler("answer_ticket", admin_answer_ticket))
    
    # Команды техподдержки
    application.add_handler(CommandHandler("support", create_support_ticket))
    
    # Добавляем обработчик кнопок
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Добавляем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling()

if __name__ == '__main__':
    main()
