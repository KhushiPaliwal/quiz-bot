# 📌 MVP(Minimum Viable Product): Telegram Educational Quiz Bot

## 🎯 Problem Statement
Students often want a quick way to revise thier weak topics or practice questions on the go, especially during breaks or while commuting. A Telegram bot can offer instant access to subject-specific questions without needing an app or login.

---

## 🌱 MVP Goal
Create a simple Telegram bot that:
- Sends static, hardcoded questions from one subject.
- Responds to basic commands like `/start`, `/quiz`, etc.
- Works without a database or backend — fully offline logic.

---

## ✅ Features Included in MVP
- Static question bank hardcoded in a `.py` or `.json` file
- Bot responds with a question when the user sends a command
- Simple flow: question → user reply → show correct answer

---

## 🚫 Features NOT Included in MVP
These can be added later but are not part of the MVP:
- Dynamic subject selection
- AI genrating questions at run time
- Tracking user's answers
- Storing user progress
- Admin panel for adding/editing questions

---

## 📌 Tech Stack
- Python
- python-telegram-bot library
- Database - SQLite(for storing static questions and stats)
- Hosting - local development setup


## 📌 Bot Flow
1. Student comes in and type /start - the bot will give him subjects to choose from (subjects as buttons)
2. After pressing a subject(button), he will be given a list of topics from that sub
3. He will again choose a topic from the list 
4. We will need a static question bank already stored  in a database/file 
5. The quiz session will be of 5-10 questions per session 
6. Each question will have multiple choices/options (4 choices to choose from).
7. The bot will immediately show result of each question, and show correct answer for wrong responses 
8. Bot can track the scores, topic wise history 
9. The student can type in /quiz for a new session and /help for instructions



## 📌

- Only taking one subject, Physics
- Selected Three topics as of now

Selected Topics (Class 11 CBSE):

Motion in a Straight Line - Kinematics, velocity, acceleration
Laws of Motion - Newton's laws, momentum, force
Work, Energy and Power - Energy conservation, work-energy theorem