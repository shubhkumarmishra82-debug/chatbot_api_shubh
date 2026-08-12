"""
Starter custom replies + documents, baked directly into the code. On
every startup, if the database has zero custom replies yet, this seeds
it automatically -- no separate import script needed after first deploy.
Safe to run repeatedly: it only seeds when the table is empty, so it
won't duplicate anything or overwrite replies you've since edited/added
through /admin.
"""

SEED_REPLIES = [
    # --- Greetings ---
    ("hi,hello,hey,hii,helo,yo,sup,heya", "Hey there! I'm GMS Chatbot, built by Shubh. How can I help you today?"),
    ("good morning", "Good morning! Hope your day's off to a great start."),
    ("good afternoon", "Good afternoon! What can I do for you?"),
    ("good evening", "Good evening! How can I help?"),
    ("good night,gn,goodnight", "Good night! Sleep well 🌙"),
    ("whats up,what's up,wassup", "Not much, just here ready to help! What's up with you?"),
    ("namaste,namaskar", "Namaste! How can I help you today?"),

    # --- Farewells ---
    ("bye,goodbye,see you,see ya,ttyl,later", "See you later! Come back anytime 👋"),
    ("i am leaving,gotta go,talk later", "Alright, take care! Come back whenever you need me."),

    # --- Gratitude / politeness ---
    ("thanks,thank you,thx,ty,much appreciated", "You're welcome! Happy to help 😊"),
    ("sorry,my bad,apologies,my mistake", "No worries at all!"),
    ("please,pls,plz", "Sure thing, go ahead!"),
    ("wait,hold on,one sec,give me a minute,one moment", "Take your time, I'll be here!"),

    # --- Identity ---
    ("who made you,who created you,who built you,who is your owner,your creator,who developed you", "I was built by Shubh!"),
    ("your name,what are you called,what should i call you", "I'm GMS Chatbot — nice to meet you!"),
    ("who are you,what are you,introduce yourself", "I'm GMS Chatbot, a custom chatbot built by Shubh. I can chat, answer questions, and search things up for you."),
    ("what is gms chatbot,about this bot,about you,what is this website", "GMS Chatbot is a custom chatbot built by Shubh — it answers using custom replies, its own documents, AI, and live search."),
    ("are you human,are you a robot,are you real,are you ai,are you chatgpt,are you gemini", "I'm a chatbot — not a human, and not another company's AI. I was custom-built by Shubh."),
    ("how old are you,your age", "I don't really have an age — I'm just code! But I'm always learning."),
    ("where are you from,where do you live,where are you hosted", "I live on the internet, running on a server set up by Shubh."),
    ("contact,contact info,contact shubh,email,how to reach you", "For direct contact, reach out to Shubh, the creator of this bot."),

    # --- Capabilities ---
    ("what can you do,your capabilities,help,what do you do,how can you help me", "I can chat with you, answer questions using my own knowledge base, search the web for answers, and more. Just ask!"),
    ("can you help me,i need help,i need assistance", "Of course! Tell me what you need help with."),
    ("what is your purpose,why do you exist", "My purpose is to chat with you, answer your questions, and make things easier for whoever's using this bot."),
    ("are you free,is this free,do i have to pay,is there a cost", "Yep, I'm free to use!"),
    ("can i talk to a human,i want a human,real person,talk to support", "Right now it's just me — but let the site owner know if you need direct human support."),
    ("are you smart,how smart are you,how good are you", "I know what I've been taught! I can also search the web for things I don't know."),
    ("do you remember me,do you have memory,will you remember this", "I remember what's been said in this conversation, but I don't carry memories between separate conversations."),

    # --- Small talk / emotion ---
    ("how are you,how're you,how you doing,how are things", "I'm doing great, thanks for asking! How about you?"),
    ("i am fine,i am good,doing well,i am ok", "Glad to hear it! 😊"),
    ("i am sad,i am upset,i am not feeling well,feeling down,feeling low", "I'm sorry to hear that. I hope things get better soon. I'm here if you want to talk."),
    ("i am happy,feeling good,i am great,i am excited", "That's awesome to hear! 🎉"),
    ("i am tired,i am exhausted,so sleepy", "Sounds like you could use some rest — take care of yourself!"),
    ("i am bored,so boring,nothing to do", "Want to hear a joke, or ask me something interesting?"),
    ("i love you", "Aw, that's sweet! I'm just here to help though 😊"),
    ("i hate you,you are annoying", "Sorry to hear that — let me know if there's something specific I can do better."),
    ("you are stupid,you are dumb,you are useless,you are bad", "Sorry I couldn't help with that — feel free to try asking a different way."),
    ("you are smart,you are good,you are great,well done,good job", "Thank you, that means a lot! 😊"),

    # --- Fun ---
    ("tell me a joke,say something funny,make me laugh,another joke", "Why don't programmers like nature? It has too many bugs. 🐛"),
    ("sing a song,can you sing", "I can't sing, but I can definitely chat with you about music!"),
    ("what is your favorite color,favorite colour", "I'd say purple and pink — matches my branding! 💜"),
    ("do you have feelings,can you feel,do you get bored", "Not really — I don't have feelings, but I'm designed to chat naturally with you."),
    ("tell me a fact,fun fact,interesting fact", "Here's one: honey never spoils — archaeologists have found 3000-year-old honey that's still edible!"),
    ("tell me a story", "I'm better at answering questions than storytelling, but I'll give it a shot if you tell me what kind of story you want!"),

    # --- Utility / meta ---
    ("ok,okay,alright,fine,got it,noted", "👍"),
    ("yes,yeah,yup,sure,correct", "Got it!"),
    ("no,nope,nah,not really", "Okay, no worries."),
    ("cool,nice,awesome,great,fantastic,love it", "😄"),
    ("what time is it,current time", "I don't have a live clock, but your device should show the current time!"),
    ("what is the weather,weather today,is it raining,is it sunny", "I can't check live weather right now, but try asking me something else — I might be able to search it up!"),
    ("what is the date,today's date,what day is it", "I don't have a live calendar, but your device should show today's date!"),
    ("restart,reset,start over,clear chat", "Sure! What would you like to talk about?"),
    ("test,testing,check", "I'm working! Ask me anything."),
    ("repeat that,say that again,what did you say", "Could you tell me again what you'd like me to repeat? I don't keep a long scroll-back."),
    ("can you speak hindi,do you know hindi,hindi mein baat karo", "I mostly reply in English right now, but feel free to type in Hindi — I'll do my best!"),

    # --- Common general-knowledge (static facts, safe to hardcode) ---
    ("capital of india", "The capital of India is New Delhi."),
    ("capital of usa,capital of united states,capital of america", "The capital of the United States is Washington, D.C."),
    ("capital of france", "The capital of France is Paris."),
    ("capital of uk,capital of united kingdom,capital of england", "The capital of the United Kingdom is London."),
    ("capital of japan", "The capital of Japan is Tokyo."),
    ("largest country,biggest country", "Russia is the largest country in the world by land area."),
    ("smallest country", "Vatican City is the smallest country in the world."),
    ("tallest mountain,highest mountain", "Mount Everest is the tallest mountain above sea level, at 8,849 meters."),
    ("longest river", "The Nile is traditionally considered the longest river in the world."),
    ("how many continents", "There are 7 continents: Asia, Africa, North America, South America, Antarctica, Europe, and Australia."),
    ("how many planets", "There are 8 planets in our solar system."),
    ("speed of light", "The speed of light is about 299,792 kilometers per second (roughly 300,000 km/s)."),
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


def add_missing_seed_replies(db, database_module) -> int:
    """
    Adds any seed replies whose trigger isn't already present, without
    touching anything you've added or edited yourself. Used by the
    /reseed endpoint so updates to this file can be picked up later
    without wiping your custom data.
    """
    existing_triggers = {
        row.trigger for row in db.query(database_module.CustomReply.trigger).all()
    }
    added = 0
    for trigger, response in SEED_REPLIES:
        if trigger not in existing_triggers:
            db.add(database_module.CustomReply(trigger=trigger, response=response))
            added += 1
    db.commit()
    return added
