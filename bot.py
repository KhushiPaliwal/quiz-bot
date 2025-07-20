from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler
import threading
import asyncio
from flask import request
from telegram import Update



#import sqlite3
#import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from datetime import datetime
from collections import defaultdict

#switched to in-memory storage for stats instead of a database
user_stats_memory = {}

# Track processed updates to prevent duplicates
processed_updates = set()

app = Flask(__name__)

# Webhook configuration
WEBHOOK_URL = "https://quiz-bot-971097042152.asia-south1.run.app/webhook"  # Your actual GCP domain
BOT_TOKEN = "7435409239:AAG1T0IEHY2m7ie-1lMg9La4PmuSecP25qM"

# Create application globally so it can be accessed by Flask routes
application = None

# Database setup
# def init_database():
#     conn = sqlite3.connect('physics_quiz.db')
#     cursor = conn.cursor()
    
#     # Create tables
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS questions (
#             id INTEGER PRIMARY KEY,
#             topic TEXT,
#             question TEXT,
#             option_a TEXT,
#             option_b TEXT,
#             option_c TEXT,
#             option_d TEXT,
#             correct_option TEXT,
#             explanation TEXT
#         )
#     ''')
    
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS user_stats (
#             user_id INTEGER,
#             topic TEXT,
#             score INTEGER,
#             total_questions INTEGER,
#             date TEXT,
#             PRIMARY KEY (user_id, topic, date)
#         )
#     ''')
    
#     conn.commit()
#     conn.close()



# Static Questions for Class 11 CBSE Physics

# used a python dictionary wheere each key is the topic, value is a list of questions
#each question is again a dictionary with keys as "question", "options", "correct" and "explanation"

PHYSICS_QUESTIONS = {
    "Motion in a Straight Line": [
        {
            "question": "A car accelerates from rest at 2 m/s² for 5 seconds. What is its final velocity?",
            "options": ["5 m/s", "10 m/s", "15 m/s", "20 m/s"],
            "correct": "B",
            "explanation": "Using v = u + at, v = 0 + 2×5 = 10 m/s"
        },
        {
            "question": "The area under velocity-time graph gives:",
            "options": ["Acceleration", "Displacement", "Speed", "Force"],
            "correct": "B",
            "explanation": "Area under v-t graph represents displacement"
        },
        {
            "question": "For uniformly accelerated motion, which equation is correct?",
            "options": ["v = u + at²", "s = ut + ½at²", "v² = u² + 2as²", "s = vt"],
            "correct": "B",
            "explanation": "s = ut + ½at² is the correct kinematic equation"
        },
        {
            "question": "A ball is thrown upward with velocity 20 m/s. After how much time will it reach maximum height? (g = 10 m/s²)",
            "options": ["1 s", "2 s", "3 s", "4 s"],
            "correct": "B",
            "explanation": "At max height, v = 0. Using v = u - gt, 0 = 20 - 10t, t = 2s"
        },
        {
            "question": "Distance covered in nth second of uniformly accelerated motion is given by:",
            "options": ["u + a(n-1)", "u + ½a(2n-1)", "u + an", "½a(2n-1)"],
            "correct": "B",
            "explanation": "Distance in nth second = u + ½a(2n-1)"
        },
        {
            "question": "If displacement is zero, then distance traveled is:",
            "options": ["Always zero", "May or may not be zero", "Always positive", "Negative"],
            "correct": "B",
            "explanation": "Displacement can be zero even if distance is non-zero (circular path)"
        },
        {
            "question": "Average velocity over a time interval is:",
            "options": ["Total distance/Total time", "Total displacement/Total time", "Final velocity/2", "Initial + Final velocity/2"],
            "correct": "B",
            "explanation": "Average velocity = Total displacement/Total time"
        },
        {
            "question": "A particle moves with constant velocity. Its acceleration is:",
            "options": ["Constant", "Variable", "Zero", "Infinite"],
            "correct": "C",
            "explanation": "For constant velocity, acceleration = 0"
        },
        {
            "question": "Free fall motion has acceleration equal to:",
            "options": ["Zero", "g (downward)", "g (upward)", "Variable"],
            "correct": "B",
            "explanation": "Free fall has constant acceleration g in downward direction"
        },
        {
            "question": "The slope of position-time graph gives:",
            "options": ["Acceleration", "Velocity", "Displacement", "Distance"],
            "correct": "B",
            "explanation": "Slope of s-t graph = ds/dt = velocity"
        }
    ],
    
    "Laws of Motion": [
        {
            "question": "Newton's first law is also known as:",
            "options": ["Law of momentum", "Law of inertia", "Law of acceleration", "Law of action-reaction"],
            "correct": "B",
            "explanation": "Newton's first law defines inertia"
        },
        {
            "question": "Force required to move a 5 kg object with acceleration 2 m/s² is:",
            "options": ["2.5 N", "7 N", "10 N", "3 N"],
            "correct": "C",
            "explanation": "F = ma = 5 × 2 = 10 N"
        },
        {
            "question": "According to Newton's third law, action and reaction forces:",
            "options": ["Act on same body", "Act on different bodies", "Are unequal", "Cancel each other"],
            "correct": "B",
            "explanation": "Action-reaction pairs act on different bodies"
        },
        {
            "question": "Momentum is conserved when:",
            "options": ["External force is zero", "Internal force is zero", "Velocity is constant", "Mass is constant"],
            "correct": "A",
            "explanation": "Momentum conservation requires zero external force"
        },
        {
            "question": "A 2 kg object moving at 5 m/s collides with 3 kg object at rest. If they stick together, final velocity is:",
            "options": ["1 m/s", "2 m/s", "3 m/s", "5 m/s"],
            "correct": "B",
            "explanation": "Using momentum conservation: 2×5 = (2+3)×v, v = 2 m/s"
        },
        {
            "question": "Inertia depends on:",
            "options": ["Velocity", "Acceleration", "Mass", "Force"],
            "correct": "C",
            "explanation": "Inertia is the property of mass"
        },
        {
            "question": "Force is a:",
            "options": ["Scalar quantity", "Vector quantity", "Dimensionless quantity", "Fundamental quantity"],
            "correct": "B",
            "explanation": "Force has both magnitude and direction"
        },
        {
            "question": "Unit of momentum is:",
            "options": ["kg⋅m/s", "kg⋅m/s²", "N⋅s", "Both A and C"],
            "correct": "D",
            "explanation": "Momentum unit is kg⋅m/s which equals N⋅s"
        },
        {
            "question": "If net force on a body is zero, the body:",
            "options": ["Must be at rest", "Must move with constant velocity", "May be at rest or moving with constant velocity", "Must be accelerating"],
            "correct": "C",
            "explanation": "Zero net force means zero acceleration, so constant velocity or rest"
        },
        {
            "question": "Impulse equals:",
            "options": ["Force × distance", "Force × time", "Mass × velocity", "Both B and C"],
            "correct": "D",
            "explanation": "Impulse = F×t = change in momentum = m×Δv"
        }
    ],
    
    "Work, Energy and Power": [
        {
            "question": "Work done by a force is maximum when angle between force and displacement is:",
            "options": ["0°", "30°", "60°", "90°"],
            "correct": "A",
            "explanation": "Work = F⋅s⋅cos(θ), maximum when θ = 0°"
        },
        {
            "question": "Kinetic energy of an object of mass 2 kg moving with velocity 10 m/s is:",
            "options": ["20 J", "100 J", "200 J", "400 J"],
            "correct": "B",
            "explanation": "KE = ½mv² = ½ × 2 × 10² = 100 J"
        },
        {
            "question": "Work done against gravity when lifting 5 kg object by 2 m is: (g = 10 m/s²)",
            "options": ["10 J", "50 J", "100 J", "25 J"],
            "correct": "C",
            "explanation": "Work = mgh = 5 × 10 × 2 = 100 J"
        },
        {
            "question": "Power is defined as:",
            "options": ["Work/Time", "Force × velocity", "Energy/Time", "All of the above"],
            "correct": "D",
            "explanation": "Power = Work/Time = Energy/Time = Force⋅velocity"
        },
        {
            "question": "Unit of power is:",
            "options": ["Joule", "Newton", "Watt", "Joule/second"],
            "correct": "C",
            "explanation": "Power is measured in Watts (W)"
        },
        {
            "question": "A spring compressed by 2 cm has potential energy 8 J. Spring constant is:",
            "options": ["200 N/m", "400 N/m", "800 N/m", "40000 N/m"],
            "correct": "D",
            "explanation": "PE = ½kx², 8 = ½k(0.02)², k = 40000 N/m"
        },
        {
            "question": "Work-energy theorem states:",
            "options": ["Work = Energy", "Work = Change in KE", "Work = PE", "Work = Total energy"],
            "correct": "B",
            "explanation": "Work done = Change in kinetic energy"
        },
        {
            "question": "Conservative force is one for which:",
            "options": ["Work depends on path", "Work is independent of path", "Work is always zero", "Work is always positive"],
            "correct": "B",
            "explanation": "Conservative forces have path-independent work"
        },
        {
            "question": "If a body is moving in a circle with constant speed, work done by centripetal force is:",
            "options": ["Maximum", "Minimum", "Zero", "Depends on radius"],
            "correct": "C",
            "explanation": "Centripetal force is perpendicular to displacement, so work = 0"
        },
        {
            "question": "Mechanical energy is conserved when:",
            "options": ["Only conservative forces act", "Only non-conservative forces act", "All forces act", "No forces act"],
            "correct": "A",
            "explanation": "Mechanical energy conservation requires only conservative forces"
        }
    ]
}

# In-memory session storage
active_sessions = {}

class QuizSession:
    def __init__(self, user_id, topic):
        self.user_id = user_id
        self.topic = topic
        self.questions = random.sample(PHYSICS_QUESTIONS[topic], 5)  # 5 random questions
        self.current_question = 0
        self.score = 0
        self.answers = []

# def load_questions_to_db():
#     """Load static questions into database""" 
#     conn = sqlite3.connect('physics_quiz.db')
#     cursor = conn.cursor()
    
#     # Clear existing questions
#     cursor.execute('DELETE FROM questions')
    
#     for topic, questions in PHYSICS_QUESTIONS.items():
#         for q in questions:
#             cursor.execute('''
#                 INSERT INTO questions (topic, question, option_a, option_b, option_c, option_d, correct_option, explanation)
#                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#             ''', (topic, q['question'], q['options'][0], q['options'][1], q['options'][2], q['options'][3], q['correct'], q['explanation']))
    
#     conn.commit()
#     conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    # Send a loading message first
    loading_msg = await update.message.reply_text("🔄 Loading... Please wait a moment.")
    
    keyboard = [
        [InlineKeyboardButton("🎯 Start Quiz", callback_data="select_topic")],
        [InlineKeyboardButton("📊 View Stats", callback_data="stats")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit the loading message with the actual content
    await loading_msg.edit_text(
        "🔬 Welcome to Physics Quiz Bot!\n"
        "📚 Class 11 CBSE Physics Practice\n\n"
        "Ready to test your physics knowledge?",
        reply_markup=reply_markup
    )
    
async def topic_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show topic selection"""
    query = update.callback_query
    
    # Answer the callback query with error handling
    try:
        await query.answer()
    except Exception as e:
        print(f"⚠️ Callback query already answered: {e}")
        # Continue processing even if already answered
    
    # Show loading message
    await query.edit_message_text("🔄 Loading topics...")
    
    keyboard = [
        [InlineKeyboardButton("🚀 Motion in a Straight Line", callback_data="topic_Motion in a Straight Line")],
        [InlineKeyboardButton("⚖️ Laws of Motion", callback_data="topic_Laws of Motion")],
        [InlineKeyboardButton("⚡ Work, Energy and Power", callback_data="topic_Work, Energy and Power")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
    ] # list of buttons

    reply_markup = InlineKeyboardMarkup(keyboard) 
    # wraps the keyboard list into a special format that telegram understands 
    # as a button layout 
    
    await query.edit_message_text(
        "📖 Choose a Physics topic:\n\n"
        "🚀 Motion in a Straight Line - Kinematics, velocity, acceleration\n"
        "⚖️ Laws of Motion - Newton's laws, momentum, force\n"
        "⚡ Work, Energy & Power - Energy conservation, work-energy theorem",
        reply_markup=reply_markup # button attached to the message
    )

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start quiz for selected topic"""
    query = update.callback_query
    
    # Answer the callback query with error handling
    try:
        await query.answer()
    except Exception as e:
        print(f"⚠️ Callback query already answered: {e}")
        # Continue processing even if already answered
    
    topic = query.data.replace("topic_", "")
    user_id = query.from_user.id
    
    # Create new quiz session
    active_sessions[user_id] = QuizSession(user_id, topic)
    
    await show_question(update, context)

async def show_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display current question"""
    query = update.callback_query
    user_id = query.from_user.id
    session = active_sessions[user_id]
    
    if session.current_question >= len(session.questions):
        await show_results(update, context)
        return
    
    current_q = session.questions[session.current_question]
    question_num = session.current_question + 1
    
    keyboard = [
        [InlineKeyboardButton(f"A) {current_q['options'][0]}", callback_data="answer_A")],
        [InlineKeyboardButton(f"B) {current_q['options'][1]}", callback_data="answer_B")],
        [InlineKeyboardButton(f"C) {current_q['options'][2]}", callback_data="answer_C")],
        [InlineKeyboardButton(f"D) {current_q['options'][3]}", callback_data="answer_D")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"📝 Question {question_num}/5\n"
    text += f"📋 Topic: {session.topic}\n\n"
    text += f"Q{question_num}.  {current_q['question']}"
    
    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        print(f"⚠️ Error editing message in show_question: {e}")
        # Try to send a new message if editing fails
        await context.bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=reply_markup
        )

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process answer and show feedback"""
    query = update.callback_query
    
    # Answer the callback query with error handling
    try:
        await query.answer()
    except Exception as e:
        print(f"⚠️ Callback query already answered: {e}")
        # Continue processing even if already answered
    
    user_id = query.from_user.id
    session = active_sessions[user_id]
    user_answer = query.data.replace("answer_", "")
    
    current_q = session.questions[session.current_question]
    correct_answer = current_q['correct']
    is_correct = user_answer == correct_answer
    
    if is_correct:
        session.score += 1
        result_text = "✅ Correct!"
    else:
        result_text = f"❌ Wrong! Correct answer: {correct_answer}"
    
    session.answers.append(user_answer)
    session.current_question += 1
    
    # Show explanation
    keyboard = [[InlineKeyboardButton("➡️ Next Question", callback_data="next_question")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"{result_text}\n\n"
    text += f"💡 {current_q['explanation']}\n\n"
    text += f"📊 Score: {session.score}/{session.current_question}"
    
    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        print(f"⚠️ Error editing message: {e}")
        # Try to send a new message if editing fails
        await context.bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=reply_markup
        )

async def next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Move to next question"""
    query = update.callback_query
    
    # Answer the callback query with error handling
    try:
        await query.answer()
    except Exception as e:
        print(f"⚠️ Callback query already answered: {e}")
        # Continue processing even if already answered
    
    await show_question(update, context)

async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show final quiz results"""
    query = update.callback_query
    
    # Answer the callback query with error handling
    try:
        await query.answer()
    except Exception as e:
        print(f"⚠️ Callback query already answered: {e}")
        # Continue processing even if already answered
    
    user_id = query.from_user.id
    session = active_sessions[user_id]
    
    #Save stats to in-memory storage
    if user_id not in user_stats_memory:
        user_stats_memory[user_id] = []

    user_stats_memory[user_id].insert(0, {
        "topic": session.topic,
        "score": session.score,
        "total_question": 5,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    # Calculate percentage
    percentage = (session.score / 5) * 100
    
    if percentage >= 80:
        grade = "🏆 Excellent!"
    elif percentage >= 60:
        grade = "👍 Good!"
    elif percentage >= 40:
        grade = "👌 Average"
    else:
        grade = "📚 Keep practicing!"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Retry Same Topic", callback_data=f"topic_{session.topic}")],
        [InlineKeyboardButton("📖 Choose New Topic", callback_data="select_topic")],
        [InlineKeyboardButton("📊 View All Stats", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"🎉 Quiz Complete!\n\n"
    text += f"📋 Topic: {session.topic}\n"
    text += f"📊 Score: {session.score}/5 ({percentage:.0f}%)\n"
    text += f"🎖️ {grade}\n\n"
    text += "What would you like to do next?"
    
    await query.edit_message_text(text, reply_markup=reply_markup)
    
    # Clean up session
    del active_sessions[user_id]

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    query = update.callback_query
    
    # Answer the callback query with error handling
    try:
        await query.answer()
    except Exception as e:
        print(f"⚠️ Callback query already answered: {e}")
        # Continue processing even if already answered
    
    user_id = query.from_user.id
    
    results = user_stats_memory.get(user_id, [])
    
    if not results:
        text = "📊 No quiz history found!\nStart a quiz to see your stats."
    else:
        text = "📊 Your Recent Quiz History:\n\n"
        for entry in results:
            topic = entry["topic"]
            score = entry["score"]
            total = entry.get("total_questions", 0)
            date = entry["date"]

            if total == 0:
                percentage = 0
            else:
                percentage = (score / total) * 100
                
            text += f"📖 {topic[:20]}...\n"
            text += f"   Score: {score}/{total} ({percentage:.0f}%) - {date[:10]}\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help information"""
    query = update.callback_query
    
    # Answer the callback query with error handling
    try:
        await query.answer()
    except Exception as e:
        print(f"⚠️ Callback query already answered: {e}")
        # Continue processing even if already answered
    
    text = "🤖 **Physics Quiz Bot Help**\n\n"
    text += "📚 **How to use:**\n"
    text += "• /start - Start the bot\n"
    text += "• /quiz - Quick start new quiz\n"
    text += "• /stats - View your statistics\n\n"
    text += "🎯 **Quiz Process:**\n"
    text += "1️⃣ Choose a physics topic\n"
    text += "2️⃣ Answer 5 MCQ questions\n"
    text += "3️⃣ Get instant feedback\n"
    text += "4️⃣ See your final score\n\n"
    text += "📖 **Available Topics:**\n"
    text += "• Motion in a Straight Line\n"
    text += "• Laws of Motion\n"
    text += "• Work, Energy and Power\n\n"
    text += "💡 **Tips:**\n"
    text += "• Read questions carefully\n"
    text += "• Learn from explanations\n"
    text += "• Practice regularly for better scores!"
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu"""
    query = update.callback_query
    
    # Answer the callback query with error handling
    try:
        await query.answer()
    except Exception as e:
        print(f"⚠️ Callback query already answered: {e}")
        # Continue processing even if already answered
    
    keyboard = [
        [InlineKeyboardButton("🎯 Start Quiz", callback_data="select_topic")],
        [InlineKeyboardButton("📊 View Stats", callback_data="stats")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔬 Physics Quiz Bot - Main Menu\n"
        "📚 Class 11 CBSE Physics Practice\n\n"
        "Choose an option:",
        reply_markup=reply_markup
    )

# Command handlers
async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick quiz command"""
    keyboard = [
        [InlineKeyboardButton("🚀 Motion in a Straight Line", callback_data="topic_Motion in a Straight Line")],
        [InlineKeyboardButton("⚖️ Laws of Motion", callback_data="topic_Laws of Motion")],
        [InlineKeyboardButton("⚡ Work, Energy and Power", callback_data="topic_Work, Energy and Power")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎯 Quick Quiz Start!\n"
        "Choose your topic:",
        reply_markup=reply_markup
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stats command"""
    user_id = update.message.from_user.id
    stats = user_stats_memory.get(user_id, [])
    # conn = sqlite3.connect('physics_quiz.db')
    # cursor = conn.cursor()
    
    # cursor.execute('''
    #     SELECT topic, AVG(score), COUNT(*), MAX(score)
    #     FROM user_stats
    #     WHERE user_id = ?
    #     GROUP BY topic
    # ''', (user_id,))
    
    # results = cursor.fetchall()
    # conn.close()
    
    if not stats:
        text = "📊 No statistics available yet!\n/quiz to start practicing."
    else:
        topic_data = defaultdict(list)
        for entry in stats:
            topic_data[entry['topic']].append(entry['score'])

        text = "📊 **Your Physics Performance:**\n\n"
        for topic, scores in topic_data.items():
            avg_score = sum(scores) / len(scores)
            best_score = max(scores)
            attempts = len(scores)
            text += f"📖 **{topic}**\n"
            text += f"   📈 Average: {avg_score:.1f}/5\n"
            text += f"   🎯 Best Score: {best_score}/5\n"
            text += f"   🔢 Attempts: {attempts}\n\n"
    
    keyboard = [[InlineKeyboardButton("🎯 Take Quiz", callback_data="select_topic")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup)

async def setup_webhook():
    """Set up webhook with Telegram"""
    try:
        await application.bot.set_webhook(url=WEBHOOK_URL)
        print(f"✅ Webhook set successfully: {WEBHOOK_URL}")
    except Exception as e:
        print(f"❌ Failed to set webhook: {e}")

@app.route("/")
def index():
    return "Bot is running!"

@app.route('/test_bot', methods=['GET'])
def test_bot():
    """Test if bot is properly initialized"""
    try:
        if application is None:
            return "❌ Bot application is not initialized"
        
        # Create a new event loop for this request
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Ensure application is initialized
        if not application.running:
            loop.run_until_complete(application.initialize())
        
        bot_info = loop.run_until_complete(application.bot.get_me())
        loop.close()
        return f"✅ Bot is working! Bot name: {bot_info.first_name}"
    except Exception as e:
        return f"❌ Bot test failed: {e}"

@app.route('/webhook_info', methods=['GET'])
def webhook_info():
    """Get webhook information"""
    try:
        # Create a new event loop for this request
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Ensure application is initialized
        if not application.running:
            loop.run_until_complete(application.initialize())
        
        webhook_info = loop.run_until_complete(application.bot.get_webhook_info())
        loop.close()
        return webhook_info.to_dict()
    except Exception as e:
        return f"Failed to get webhook info: {e}"

@app.route('/set_webhook', methods=['GET'])
def set_webhook_route():
    """Manually set webhook (for debugging)"""
    try:
        # Create a new event loop for this request
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Ensure application is initialized
        if not application.running:
            loop.run_until_complete(application.initialize())
        
        loop.run_until_complete(setup_webhook())
        loop.close()
        return "Webhook set successfully!"
    except Exception as e:
        return f"Failed to set webhook: {e}"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook updates from Telegram"""
    try:
        print("📨 Received webhook update from Telegram")
        update_data = request.get_json(force=True)
        print(f"📋 Update data: {update_data}")
        
        update = Update.de_json(update_data, application.bot)
        
        # Check if this update has already been processed
        update_id = update.update_id
        if update_id in processed_updates:
            print(f"⚠️ Update {update_id} already processed, skipping")
            return "ok"
        
        # Add to processed updates
        processed_updates.add(update_id)
        
        # Keep only last 1000 updates to prevent memory issues
        if len(processed_updates) > 1000:
            processed_updates.clear()
        
        # Create a new event loop for this request
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Ensure application is initialized
        if not application.running:
            loop.run_until_complete(application.initialize())
        
        loop.run_until_complete(application.process_update(update))
        loop.close()
        
        print("✅ Successfully processed update")
        return "ok"
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return "error", 500

def main():
    """Main function to run the bot"""
    # Initialize database and load questions
    # init_database()
    # load_questions_to_db()
    
    # Create application
    global application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Initialize the application
    asyncio.run(application.initialize())
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quiz", quiz_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(topic_selection, pattern="select_topic"))
    application.add_handler(CallbackQueryHandler(start_quiz, pattern="topic_"))
    application.add_handler(CallbackQueryHandler(handle_answer, pattern="answer_"))
    application.add_handler(CallbackQueryHandler(next_question, pattern="next_question"))
    application.add_handler(CallbackQueryHandler(show_stats, pattern="^stats$"))
    application.add_handler(CallbackQueryHandler(show_help, pattern="help"))
    application.add_handler(CallbackQueryHandler(main_menu, pattern="main_menu"))
    
    # Run the bot
    print("🤖 Physics Quiz Bot started!")
    print("📚 Loaded topics: Motion, Laws of Motion, Work-Energy-Power")
    print("📊 Questions loaded: 30 total (10 per topic)")
    # application.run_polling()

if __name__ == '__main__':
    # Initialize the bot
    main()
    
    # Set up webhook before starting Flask
    print("🔗 Setting up webhook...")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Ensure application is initialized
        if not application.running:
            loop.run_until_complete(application.initialize())
        
        loop.run_until_complete(setup_webhook())
        loop.close()
    except Exception as e:
        print(f"❌ Failed to set webhook: {e}")
    
    # Start Flask app
    print("🚀 Starting Flask app...")
    app.run(host='0.0.0.0', port=8080, debug=False)
  

