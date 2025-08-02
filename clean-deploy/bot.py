from flask import Flask
import asyncio
from flask import request
from dotenv import load_dotenv
import random
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ApplicationBuilder
from datetime import datetime
from collections import defaultdict

# Load environment variables
load_dotenv()

# Track processed updates to prevent duplicates
processed_updates = set()

app = Flask(__name__) 

# Webhook configuration
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://quiz-bot-971097042152.asia-south1.run.app/webhook")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Create application globally so it can be accessed by Flask routes
application = None

# In-memory session storage
active_sessions = {}
user_stats_memory = {}

# Static Questions for Class 11 CBSE Physics
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
            "question": "Friction force always acts:",
            "options": ["In direction of motion", "Opposite to motion", "Perpendicular to motion", "At 45° to motion"],
            "correct": "B",
            "explanation": "Friction always opposes relative motion"
        },
        {
            "question": "Impulse is equal to:",
            "options": ["Force", "Momentum", "Change in momentum", "Work done"],
            "correct": "C",
            "explanation": "Impulse = Change in momentum"
        },
        {
            "question": "For equilibrium, net force must be:",
            "options": ["Maximum", "Minimum", "Zero", "Constant"],
            "correct": "C",
            "explanation": "For equilibrium, ΣF = 0"
        },
        {
            "question": "Centripetal force is:",
            "options": ["Real force", "Fictitious force", "Contact force", "Field force"],
            "correct": "A",
            "explanation": "Centripetal force is a real force directed toward center"
        }
    ],
    
    "Work, Energy and Power": [
        {
            "question": "Work done by a force is maximum when:",
            "options": ["Force is perpendicular to displacement", "Force is parallel to displacement", "Force is opposite to displacement", "Force is zero"],
            "correct": "B",
            "explanation": "W = F⋅s⋅cos(θ), maximum when θ = 0°"
        },
        {
            "question": "Kinetic energy of a body depends on:",
            "options": ["Mass only", "Velocity only", "Mass and velocity", "Mass and acceleration"],
            "correct": "C",
            "explanation": "KE = ½mv² depends on both mass and velocity"
        },
        {
            "question": "Potential energy is maximum at:",
            "options": ["Ground level", "Maximum height", "Half height", "Any height"],
            "correct": "B",
            "explanation": "PE = mgh, maximum at maximum height"
        },
        {
            "question": "Power is the rate of:",
            "options": ["Work done", "Energy consumed", "Force applied", "Distance covered"],
            "correct": "A",
            "explanation": "Power = Work done/Time"
        },
        {
            "question": "For conservative forces:",
            "options": ["Work done is path dependent", "Work done is path independent", "Work done is always zero", "Work done is always negative"],
            "correct": "B",
            "explanation": "Conservative forces: work independent of path"
        },
        {
            "question": "Mechanical energy is conserved when:",
            "options": ["Only conservative forces act", "Only non-conservative forces act", "Both types act", "No forces act"],
            "correct": "A",
            "explanation": "ME conserved when only conservative forces act"
        },
        {
            "question": "Efficiency of a machine is:",
            "options": ["Output/Input", "Input/Output", "Output × Input", "Output - Input"],
            "correct": "A",
            "explanation": "Efficiency = Useful output/Total input"
        },
        {
            "question": "Work-energy theorem states:",
            "options": ["Work = Energy", "Work = Change in KE", "Work = Change in PE", "Work = Power"],
            "correct": "B",
            "explanation": "Work done = Change in kinetic energy"
        },
        {
            "question": "Power unit in SI system is:",
            "options": ["Joule", "Newton", "Watt", "Pascal"],
            "correct": "C",
            "explanation": "Power is measured in Watts (W)"
        },
        {
            "question": "Energy cannot be:",
            "options": ["Created", "Destroyed", "Both created and destroyed", "Transformed"],
            "correct": "C",
            "explanation": "Energy can be transformed but not created or destroyed"
        }
    ]
}

class QuizSession:
    def __init__(self, user_id, topic):
        self.user_id = user_id
        self.topic = topic
        self.questions = random.sample(PHYSICS_QUESTIONS[topic], 5)  # 5 random questions
        self.current_question = 0
        self.score = 0
        self.answers = []

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
    
    # Send quiz start message
    await context.bot.send_message(
        chat_id=user_id,
        text=f"🎯 Quiz Started!\n\n"
             f"📚 Topic: {topic}\n"
             f"❓ Questions: 5\n\n"
             f"Good luck! 🍀"
    )
    
    await show_question(update, context)

async def show_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display current question as a new message"""
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
    text += f"Q{question_num}. {current_q['question']}"
    
    # Send new message instead of editing
    await context.bot.send_message(
        chat_id=user_id,
        text=text,
        reply_markup=reply_markup
    )

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process answer and show feedback as new message"""
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
    
    # Get the actual answer text for display
    user_answer_text = current_q['options'][ord(user_answer) - ord('A')]
    correct_answer_text = current_q['options'][ord(correct_answer) - ord('A')]
    
    if is_correct:
        session.score += 1
        result_text = "✅ Correct!"
        answer_feedback = f"Your answer: {user_answer}) {user_answer_text}"
    else:
        result_text = "❌ Wrong!"
        answer_feedback = f"Your answer: {user_answer}) {user_answer_text}\nCorrect answer: {correct_answer}) {correct_answer_text}"
    
    session.answers.append(user_answer)
    session.current_question += 1
    
    # Send feedback as new message
    feedback_text = f"{result_text}\n\n"
    feedback_text += f"🎯 {answer_feedback}\n\n"
    feedback_text += f"💡 {current_q['explanation']}\n\n"
    feedback_text += f"📊 Score: {session.score}/{session.current_question}"
    
    await context.bot.send_message(
        chat_id=user_id,
        text=feedback_text
    )
    
    # Show next question button as separate message
    if session.current_question < len(session.questions):
        keyboard = [[InlineKeyboardButton("➡️ Next Question", callback_data="next_question")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=user_id,
            text="Ready for the next question?",
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
    """Show final quiz results as new message"""
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
    
    # Send results as new message
    await context.bot.send_message(
        chat_id=user_id,
        text=text,
        reply_markup=reply_markup
    )
    
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
            total = entry.get("total_question", 0)
            date = entry["date"]

            if total == 0:
                percentage = 0
            else:
                percentage = (score / total) * 100
                
            text += f"📖 {topic}...\n"
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
    text += "2️⃣ Answer 5 questions\n"
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
    
    if not stats:
        text = "📊 No statistics available yet!\n/quiz to start practicing."
    else:
        topic_data = defaultdict(list)
        for entry in stats:
            topic_data[f"{entry['topic']} ({entry['difficulty']})"].append(entry['score'])

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
        
        try:
            # Ensure application is initialized
            if not application.running:
                loop.run_until_complete(application.initialize())
            
            bot_info = loop.run_until_complete(application.bot.get_me())
            return f"✅ Bot is working! Bot name: {bot_info.first_name}"
        finally:
            loop.close()
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
    print(f"🔍 Debug: BOT_TOKEN = {'SET' if os.getenv('BOT_TOKEN') else 'NOT SET'}")
    print(f"🔍 Debug: WEBHOOK_URL = {os.getenv('WEBHOOK_URL', 'NOT SET')}")
    
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is not set!")
    
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
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
  

