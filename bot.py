import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import random

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Токен бота
TOKEN = "7819477296:AAGsHv9V8vfCAAw1aWrc_goeLzSdr3yW0Jg"

# Временное хранилище данных пользователей
users = {}

class User:
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username
        self.balance = 5000
        self.rating = 0
        self.clan = None
        self.current_game = None
        self.game_data = {}

class BlackjackGame:
    def __init__(self):
        self.deck = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Валет', 'Дама', 'Король', 'Туз'] * 4
        self.suits = ['♠️', '♣️', '♥️', '♦']
        self.card_values = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
            'Валет': 10, 'Дама': 10, 'Король': 10, 'Туз': 11
        }

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in users:
        users[user.id] = User(user.id, user.username)

    keyboard = [
        ["💎 Основное", "🚀 Игры"],
        ["😎 Персонаж"],
        ["🃏 Покер", "📊 Биржа"],
        ["⚙️ Настроить", "📒 Профиль", "🔥 Донат"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n"
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
    user = users.get(update.callback_query.from_user.id)
    if not user:
        return
    
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
        bet = user.game_data['blackjack']['bet']
        win_amount = bet * 2  # Выигрыш х2 при 21 очке
        user.balance += win_amount
        
        # Формируем текст для карт
        player_cards_text = "🎫 Ваши карты:\n"
        for i, (card, suit) in enumerate(user.game_data['blackjack']['player_cards'], 1):
            player_cards_text += f"⠀{i}⃣ {suit} {card}\n"
        
        dealer_cards_text = "🎟 Карты крупье:\n"
        dealer_card, dealer_suit = user.game_data['blackjack']['dealer_cards'][0]
        dealer_cards_text += f"⠀1⃣ {dealer_suit} {dealer_card}"
        
        game_text = (
            f"💡 Ваши очки: {player_score} ⏐ Крупье: {game.calculate_score(user.game_data['blackjack']['dealer_cards'])}\n"
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
            
        user.game_data.pop('blackjack')
        return True
    return False

async def start_blackjack_game(update: Update, context: ContextTypes.DEFAULT_TYPE, bet: int):
    query = update.callback_query
    user = users.get(query.from_user.id)
    if not user:
        return
    
    if bet > user.balance:
        await query.message.reply_text("Недостаточно средств!")
        return
    
    user.balance -= bet
    game = BlackjackGame()
    user.game_data['blackjack'] = {
        'game': game,
        'bet': bet,
        'player_cards': [game.get_card(), game.get_card()],
        'dealer_cards': [game.get_card()]
    }
    
    player_score = game.calculate_score(user.game_data['blackjack']['player_cards'])
    dealer_score = game.calculate_score(user.game_data['blackjack']['dealer_cards'])
    
    # Проверяем на блэкджек
    if await check_blackjack(update, user, game, player_score):
        return
    
    # Формируем текст для карт игрока
    player_cards_text = "🎫 Ваши карты:\n"
    for i, (card, suit) in enumerate(user.game_data['blackjack']['player_cards'], 1):
        player_cards_text += f"⠀{i}⃣ {suit} {card}\n"
    
    # Формируем текст для карт крупье
    dealer_cards_text = "🎟 Карты крупье:\n"
    dealer_card, dealer_suit = user.game_data['blackjack']['dealer_cards'][0]
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
        user = users.get(query.from_user.id)
        if not user or 'blackjack' not in user.game_data:
            return
        
        game = user.game_data['blackjack']['game']
        user.game_data['blackjack']['player_cards'].append(game.get_card())
        player_score = game.calculate_score(user.game_data['blackjack']['player_cards'])
        
        # Проверяем на блэкджек
        if await check_blackjack(update, user, game, player_score):
            return
        
        if player_score > 21:
            # Проигрыш
            player_cards_text = "🎫 Ваши карты:\n"
            for i, (card, suit) in enumerate(user.game_data['blackjack']['player_cards'], 1):
                player_cards_text += f"⠀{i}⃣ {suit} {card}\n"
            
            dealer_cards_text = "🎟 Карты крупье:\n"
            dealer_card, dealer_suit = user.game_data['blackjack']['dealer_cards'][0]
            dealer_cards_text += f"⠀1⃣ {dealer_suit} {dealer_card}"
            
            game_text = (
                f"💡 Ваши очки: {player_score} ⏐ Крупье: {game.calculate_score(user.game_data['blackjack']['dealer_cards'])}\n"
                f"{player_cards_text}\n"
                f"{dealer_cards_text}\n"
                f"❌ Вы проиграли!\n"
                f"💰 Баланс: {user.balance}$"
            )
            
            keyboard = [[InlineKeyboardButton("🔄 Играть заново", callback_data="blackjack_start")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(game_text, reply_markup=reply_markup)
            user.game_data.pop('blackjack')
        else:
            # Продолжаем игру
            player_cards_text = "🎫 Ваши карты:\n"
            for i, (card, suit) in enumerate(user.game_data['blackjack']['player_cards'], 1):
                player_cards_text += f"⠀{i}⃣ {suit} {card}\n"
            
            dealer_cards_text = "🎟 Карты крупье:\n"
            dealer_card, dealer_suit = user.game_data['blackjack']['dealer_cards'][0]
            dealer_cards_text += f"⠀1⃣ {dealer_suit} {dealer_card}"
            
            game_text = (
                f"Игрок, Ваши очки: {player_score} ⏐ Крупье: {game.calculate_score(user.game_data['blackjack']['dealer_cards'])}\n"
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
        user = users.get(query.from_user.id)
        if not user or 'blackjack' not in user.game_data:
            return
        
        game = user.game_data['blackjack']['game']
        dealer_score = game.calculate_score(user.game_data['blackjack']['dealer_cards'])
        
        # Дилер берет карты, пока у него меньше 17
        while dealer_score < 17:
            user.game_data['blackjack']['dealer_cards'].append(game.get_card())
            dealer_score = game.calculate_score(user.game_data['blackjack']['dealer_cards'])
        
        player_score = game.calculate_score(user.game_data['blackjack']['player_cards'])
        bet = user.game_data['blackjack']['bet']
        
        # Формируем текст для карт
        player_cards_text = "🎫 Ваши карты:\n"
        for i, (card, suit) in enumerate(user.game_data['blackjack']['player_cards'], 1):
            player_cards_text += f"⠀{i}⃣ {suit} {card}\n"
        
        dealer_cards_text = "🎟 Карты крупье:\n"
        for i, (card, suit) in enumerate(user.game_data['blackjack']['dealer_cards'], 1):
            dealer_cards_text += f"⠀{i}⃣ {suit} {card}\n"
        
        # Определяем победителя
        if dealer_score > 21 or player_score > dealer_score:
            # Игрок выиграл
            win_amount = bet * 2
            user.balance += win_amount
            result_text = f"✅ Вы выиграли {win_amount}$!"
        elif player_score < dealer_score:
            # Игрок проиграл
            result_text = f"❌ Вы проиграли {bet}$!"
        else:
            # Ничья
            user.balance += bet
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
        user.game_data.pop('blackjack')
    
    elif query.data == "blackjack_double":
        # Удвоить ставку и взять одну карту
        user = users.get(query.from_user.id)
        if not user or 'blackjack' not in user.game_data:
            return
        
        bet = user.game_data['blackjack']['bet']
        if user.balance < bet:  # Проверяем, хватает ли денег на удвоение
            await query.message.reply_text("Недостаточно средств для удвоения!")
            return
        
        # Удваиваем ставку
        user.balance -= bet
        user.game_data['blackjack']['bet'] = bet * 2
        
        # Берем одну карту
        game = user.game_data['blackjack']['game']
        user.game_data['blackjack']['player_cards'].append(game.get_card())
        player_score = game.calculate_score(user.game_data['blackjack']['player_cards'])
        
        # Сразу показываем карты дилера и определяем победителя
        dealer_score = game.calculate_score(user.game_data['blackjack']['dealer_cards'])
        while dealer_score < 17:
            user.game_data['blackjack']['dealer_cards'].append(game.get_card())
            dealer_score = game.calculate_score(user.game_data['blackjack']['dealer_cards'])
        
        # Формируем текст для карт
        player_cards_text = "🎫 Ваши карты:\n"
        for i, (card, suit) in enumerate(user.game_data['blackjack']['player_cards'], 1):
            player_cards_text += f"⠀{i}⃣ {suit} {card}\n"
        
        dealer_cards_text = "🎟 Карты крупье:\n"
        for i, (card, suit) in enumerate(user.game_data['blackjack']['dealer_cards'], 1):
            dealer_cards_text += f"⠀{i}⃣ {suit} {card}\n"
        
        # Определяем победителя
        doubled_bet = bet * 2
        if player_score > 21:
            result_text = f"❌ Вы проиграли {doubled_bet}$!"
        elif dealer_score > 21 or player_score > dealer_score:
            win_amount = doubled_bet * 2
            user.balance += win_amount
            result_text = f"✅ Вы выиграли {win_amount}$!"
        elif player_score < dealer_score:
            result_text = f"❌ Вы проиграли {doubled_bet}$!"
        else:
            user.balance += doubled_bet
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
        user.game_data.pop('blackjack')

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

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))

    # Запускаем бота
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()