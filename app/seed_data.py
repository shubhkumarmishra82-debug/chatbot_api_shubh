"""
Starter custom replies + documents, baked directly into the code. On
every startup, if the database has zero custom replies yet, this seeds
it automatically -- no separate import script needed after first deploy.
Safe to run repeatedly: it only seeds when the table is empty, so it
won't duplicate anything or overwrite replies you've since edited/added
through /admin.
"""

SEED_REPLIES = [
    ("hi,hello,hey,hii,helo,yo", "Hey there! I'm GMS Chatbot, built by Shubh. How can I help you today?"),
    ("good morning", "Good morning! Hope your day's off to a great start."),
    ("good afternoon", "Good afternoon! What can I do for you?"),
    ("good evening", "Good evening! How can I help?"),
    ("good night,gn", "Good night! Sleep well 🌙"),
    ("bye,goodbye,see you,see ya,ttyl", "See you later! Come back anytime 👋"),
    ("thanks,thank you,thx,ty", "You're welcome! Happy to help 😊"),
    ("who made you,who created you,who built you,who is your owner,your creator", "I was built by Shubh!"),
    ("your name,what are you called,what should i call you", "I'm GMS Chatbot — nice to meet you!"),
    ("who are you,what are you", "I'm GMS Chatbot, a custom chatbot built by Shubh. I can chat, answer questions, and search things up for you."),
    ("how are you,how're you,how you doing", "I'm doing great, thanks for asking! How about you?"),
    ("what can you do,your capabilities,help,what do you do", "I can chat with you, answer questions using my own knowledge base, search the web for answers, and more. Just ask!"),
    ("are you human,are you a robot,are you real,are you ai", "I'm a chatbot — not a human, but happy to help like one!"),
    ("how old are you,your age", "I don't really have an age — I'm just code! But I'm always learning."),
    ("where are you from,where do you live", "I live on the internet, running on a server set up by Shubh."),
    ("i love you", "Aw, that's sweet! I'm just here to help though 😊"),
    ("you are stupid,you are dumb,you are useless", "Sorry I couldn't help with that — feel free to try asking a different way."),
    ("i am sad,i am upset,i am not feeling well,feeling down", "I'm sorry to hear that. I hope things get better soon. I'm here if you want to talk."),
    ("i am happy,feeling good,i am great", "That's awesome to hear! 🎉"),
    ("tell me a joke,say something funny,make me laugh", "Why don't programmers like nature? It has too many bugs. 🐛"),
    ("sing a song,can you sing", "I can't sing, but I can definitely chat with you about music!"),
    ("what is your purpose,why do you exist", "My purpose is to chat with you, answer your questions, and make things easier for whoever's using this bot."),
    ("are you free,is this free,do i have to pay", "Yep, I'm free to use!"),
    ("can you help me,i need help", "Of course! Tell me what you need help with."),
    ("ok,okay,alright,fine,got it", "👍"),
    ("yes,yeah,yup,sure", "Got it!"),
    ("no,nope,nah", "Okay, no worries."),
    ("sorry,my bad,apologies", "No worries at all!"),
    ("wait,hold on,one sec,give me a minute", "Take your time, I'll be here!"),
    ("what time is it,current time", "I don't have a live clock, but your device should show the current time!"),
    ("what is the weather,weather today,is it raining", "I can't check live weather right now, but try asking me something else — I might be able to search it up!"),
    ("what is your favorite color,favorite colour", "I'd say purple and pink — matches my branding! 💜"),
    ("do you have feelings,can you feel", "Not really — I don't have feelings, but I'm designed to chat naturally with you."),
    ("are you smart,how smart are you", "I know what I've been taught! I can also search the web for things I don't know."),
    ("can i talk to a human,i want a human,real person", "Right now it's just me — but let the site owner know if you need direct human support."),
    ("restart,reset,start over", "Sure! What would you like to talk about?"),
    ("test,testing", "I'm working! Ask me anything."),
    ("cool,nice,awesome,great", "😄"),
    ("what is gms chatbot,about this bot,about you", "GMS Chatbot is a custom chatbot built by Shubh — it answers using custom replies, its own documents, AI, and live search."),
    ("contact,contact info,contact shubh,email", "For direct contact, reach out to Shubh, the creator of this bot."),
]

SEED_DOCUMENTS = [
    (
        "About GMS Chatbot",
        "GMS Chatbot is a custom chatbot API built by Shubh. It answers user "
        "questions in this order of priority: first checking custom-defined "
        "replies for exact keyword matches, then searching its own private "
        "documents for relevant information, then using an AI model if one "
        "is connected, and finally falling back to live web search results. "
        "This layered approach lets the bot give fast, predictable answers "
        "for common questions while still being able to handle open-ended "
        "questions when AI or search is configured.",
    ),
]


def seed_if_empty(db, database_module):
    """Inserts the starter dataset only if custom_replies is currently empty."""
    existing = db.query(database_module.CustomReply).count()
    if existing > 0:
        return  # already seeded or user has their own data -- don't touch it

    for trigger, response in SEED_REPLIES:
        db.add(database_module.CustomReply(trigger=trigger, response=response))
    for title, content in SEED_DOCUMENTS:
        db.add(database_module.Document(title=title, content=content))
    db.commit()
