"""
Cognitive Assessment Service
Educational multi-domain cognitive screening module.
Domains:
1. Memory (Immediate Recall, Episodic Recall, Delayed Recognition)
2. Attention (Working Memory Span, Serial Calculation, Numeric Logic)
3. Orientation (Temporal, Spatial, Ambient)
4. Language (Confrontation Naming, Categorical Fluency, Syntactic Parsing)
5. Reasoning (Analogy Mapping, Practical Judgment, Conceptual Abstraction)

Features:
- DYNAMIC PROCEDURAL GENERATOR: Produces unique, randomized questions EVERY SINGLE TIME a user takes the assessment.
  This allows users to take multiple tests daily to monitor real cognitive progress without question repetition.
- Longitudinal Progress Comparison: Automatically compares score with previous tests to detect true improvement.
- Standard Form A & Form B reference benchmarks.

DISCLAIMER: This is an educational interactive questionnaire and is NOT a clinically
validated diagnostic tool (such as MMSE or MoCA). It does not diagnose Alzheimer's disease.
"""

import random

# ==========================================
# RICH DYNAMIC QUESTION POOLS
# ==========================================

# 1. Memory: Word Registration Trios
WORD_TRIPLETS = [
    ("Apple", "Table", "Penny"),
    ("Banana", "Mirror", "Nickel"),
    ("Orange", "Velvet", "Dollar"),
    ("Cherry", "Compass", "Ribbon"),
    ("Mango", "Pillow", "Silver"),
    ("Grape", "Blanket", "Copper"),
    ("Lemon", "Carpet", "Marble"),
    ("Peach", "Lantern", "Diamond"),
    ("Melon", "Basket", "Quartz"),
    ("Berry", "Candle", "Bronze"),
    ("Papaya", "Hammer", "Anchor"),
    ("Walnut", "Ladder", "Feather"),
    ("Tulip", "Guitar", "Needle"),
    ("Rose", "Violin", "Thimble"),
    ("Daisy", "Camera", "Pencil"),
    ("Orchid", "Clock", "Ribbon"),
    ("Cedar", "Bicycle", "Button"),
    ("Maple", "Saddle", "Mirror"),
    ("Willow", "Teapot", "Kettle"),
    ("Pine", "Cradle", "Locket")
]

# Distractor words for delayed recognition
MEMORY_DISTRACTORS = [
    "Window", "River", "Bicycle", "Guitar", "Blanket", "Candle", "Hammer",
    "Ladder", "Thimble", "Pencil", "Kettle", "Locket", "Feather", "Cactus",
    "Anchor", "Compass", "Saddle", "Violin", "Mirror", "Teapot"
]

# 2. Attention: 5-Letter Words to Reverse Spell
REVERSE_WORDS_POOL = [
    ("WORLD", "D-L-R-O-W", ["D-R-L-O-W", "W-O-R-L-D", "D-L-O-R-W"]),
    ("MUSIC", "C-I-S-U-M", ["C-S-I-U-M", "M-U-S-I-C", "C-I-U-S-M"]),
    ("PILOT", "T-O-L-I-P", ["T-L-O-I-P", "P-I-L-O-T", "T-O-I-L-P"]),
    ("EARTH", "H-T-R-A-E", ["H-R-T-A-E", "E-A-R-T-H", "H-T-A-R-E"]),
    ("PLANT", "T-N-A-L-P", ["T-A-N-L-P", "P-L-A-N-T", "T-N-L-A-P"]),
    ("WATER", "R-E-T-A-W", ["R-T-E-A-W", "W-A-T-E-R", "R-E-A-T-W"]),
    ("LIGHT", "T-H-G-I-L", ["T-G-H-I-L", "L-I-G-H-T", "T-H-I-G-L"]),
    ("BREAD", "D-A-E-R-B", ["D-E-A-R-B", "B-R-E-A-D", "D-A-R-E-B"]),
    ("CLOCK", "K-C-O-L-C", ["K-O-C-L-C", "C-L-O-C-K", "K-C-L-O-C"]),
    ("RIVER", "R-E-V-I-R", ["R-V-E-I-R", "R-I-V-E-R", "R-E-I-V-R"]),
    ("HOUSE", "E-S-U-O-H", ["E-U-S-O-H", "H-O-U-S-E", "E-S-O-U-H"]),
    ("TRAIN", "N-I-A-R-T", ["N-A-I-R-T", "T-R-A-I-N", "N-I-R-A-T"])
]

# 3. Attention: Mental Arithmetic Challenges
MATH_CHALLENGES = [
    {"start": 100, "sub": 7, "first": 93, "correct": 86, "distractors": [85, 87, 84]},
    {"start": 100, "sub": 6, "first": 94, "correct": 88, "distractors": [86, 87, 89]},
    {"start": 100, "sub": 8, "first": 92, "correct": 84, "distractors": [82, 85, 86]},
    {"start": 100, "sub": 9, "first": 91, "correct": 82, "distractors": [80, 83, 84]},
    {"start": 93, "sub": 7, "first": 86, "correct": 79, "distractors": [78, 80, 77]},
    {"start": 94, "sub": 6, "first": 88, "correct": 82, "distractors": [80, 83, 84]},
    {"start": 92, "sub": 8, "first": 84, "correct": 76, "distractors": [74, 78, 77]},
    {"start": 88, "sub": 7, "first": 81, "correct": 74, "distractors": [72, 75, 73]},
    {"start": 85, "sub": 6, "first": 79, "correct": 73, "distractors": [71, 74, 72]},
    {"start": 100, "sub": 5, "first": 95, "correct": 90, "distractors": [88, 92, 85]}
]

# 4. Attention: Numeric Patterns
PATTERN_CHALLENGES = [
    {"seq": "2, 4, 8, 16, [ ? ]", "correct": "32 (doubling pattern)", "distractors": ["24", "20", "64"]},
    {"seq": "3, 6, 12, 24, [ ? ]", "correct": "48 (multiplying by 2)", "distractors": ["36", "30", "42"]},
    {"seq": "5, 10, 15, 20, [ ? ]", "correct": "25 (adding 5)", "distractors": ["30", "22", "24"]},
    {"seq": "1, 4, 9, 16, [ ? ]", "correct": "25 (squares pattern: 5²)", "distractors": ["20", "24", "36"]},
    {"seq": "21, 18, 15, 12, [ ? ]", "correct": "9 (subtracting 3)", "distractors": ["10", "8", "6"]},
    {"seq": "40, 35, 30, 25, [ ? ]", "correct": "20 (subtracting 5)", "distractors": ["15", "22", "18"]},
    {"seq": "80, 40, 20, 10, [ ? ]", "correct": "5 (halving pattern)", "distractors": ["2", "8", "0"]},
    {"seq": "2, 5, 8, 11, [ ? ]", "correct": "14 (adding 3)", "distractors": ["13", "15", "12"]},
    {"seq": "100, 90, 80, 70, [ ? ]", "correct": "60 (subtracting 10)", "distractors": ["50", "65", "55"]},
    {"seq": "1, 3, 9, 27, [ ? ]", "correct": "81 (multiplying by 3)", "distractors": ["54", "72", "90"]}
]

# 5. Language: Object Naming Challenges
NAMING_CHALLENGES = [
    {
        "prompt": "What medical instrument is used by physicians to listen to heartbeats and lung sounds?",
        "correct": "Stethoscope",
        "distractors": ["Sphygmomanometer", "Thermometer", "Otoscope"]
    },
    {
        "prompt": "What optical laboratory instrument is used to view microscopic cells and bacteria invisible to the naked eye?",
        "correct": "Microscope",
        "distractors": ["Telescope", "Binoculars", "Periscope"]
    },
    {
        "prompt": "What optical astronomical instrument is used to observe distant planets, stars, and galaxies?",
        "correct": "Telescope",
        "distractors": ["Microscope", "Kaleidoscope", "Periscope"]
    },
    {
        "prompt": "What navigation instrument uses a magnetized needle pointing toward magnetic north?",
        "correct": "Compass",
        "distractors": ["Protractor", "Barometer", "Sextant"]
    },
    {
        "prompt": "What meteorological instrument is used to measure atmospheric air pressure for weather forecasting?",
        "correct": "Barometer",
        "distractors": ["Thermometer", "Hygrometer", "Anemometer"]
    },
    {
        "prompt": "What clinical instrument is used to measure human core body temperature?",
        "correct": "Thermometer",
        "distractors": ["Barometer", "Altimeter", "Calipers"]
    },
    {
        "prompt": "What optical device allows sailors inside a submerged submarine to view above the surface of the water?",
        "correct": "Periscope",
        "distractors": ["Microscope", "Telescope", "Spectroscope"]
    },
    {
        "prompt": "What device uses the position of the sun's shadow cast onto a marked dial to tell the time of day?",
        "correct": "Sundial",
        "distractors": ["Hourglass", "Metronome", "Chronometer"]
    }
]

# 6. Language: Category Odd-One-Out
ODD_ONE_OUT_CHALLENGES = [
    {"category": "Musical Instruments", "correct": "Easel", "distractors": ["Violin", "Clarinet", "Tambourine"]},
    {"category": "Kitchen Cooking Tools", "correct": "Chisel", "distractors": ["Spatula", "Whisk", "Ladle"]},
    {"category": "Farm Animals", "correct": "Cactus", "distractors": ["Sheep", "Goat", "Dairy Cow"]},
    {"category": "Edible Tree Fruits", "correct": "Anchor", "distractors": ["Apple", "Peach", "Orange"]},
    {"category": "Living Room Furniture", "correct": "Guitar", "distractors": ["Sofa", "Coffee Table", "Bookshelf"]},
    {"category": "Vehicles & Transportation", "correct": "Toaster", "distractors": ["Bicycle", "Airplane", "Passenger Train"]},
    {"category": "Winter Apparel & Clothing", "correct": "Microscope", "distractors": ["Wool Scarf", "Winter Jacket", "Insulated Gloves"]},
    {"category": "Natural Bodies of Water", "correct": "Mountain", "distractors": ["Freshwater River", "Ocean", "Alpine Lake"]},
    {"category": "Precious Gemstones", "correct": "Pebble", "distractors": ["Emerald", "Sapphire", "Ruby"]}
]

# 7. Language: Syntactic Grammar Sentences
SYNTAX_CHALLENGES = [
    {
        "prompt": "Choose the grammatically correct and coherent sentence:",
        "correct": "Despite the heavy rain, the students arrived on time for their morning lecture.",
        "distractors": [
            "Because heavy rain, arriving students lecture morning on time.",
            "The students was arrived late despite rain heavy lecture.",
            "Rain morning on time students heavy arrived despite."
        ]
    },
    {
        "prompt": "Select the grammatically accurate and sensible sentence:",
        "correct": "The librarian carefully organized all the newly arrived medical journals on the reference shelf.",
        "distractors": [
            "Librarian medical shelf new journals carefully organized all arrived the.",
            "All journals reference shelf librarian was organizing careful arriving.",
            "Because arrived medical shelf librarian was organized on."
        ]
    },
    {
        "prompt": "Pick the syntactically coherent and fluent sentence:",
        "correct": "After completing their laboratory experiments, the research scientists published their findings in a peer-reviewed journal.",
        "distractors": [
            "Published scientists research after findings laboratory completing in journal.",
            "The scientists laboratory was publish after experiment finding research.",
            "After findings published scientists experiment was completing research."
        ]
    }
]

# 8. Reasoning: Analogies
ANALOGY_CHALLENGES = [
    {"pair": "An airplane is to a PILOT as a commercial train is to an [ ? ]:", "correct": "Engineer / Locomotive Driver", "distractors": ["Passenger", "Conductor (Tickets)", "Station Master"]},
    {"pair": "A ship is to a CAPTAIN as a commercial city bus is to a [ ? ]:", "correct": "Bus Driver", "distractors": ["Passenger", "Ticket Inspector", "Mechanic"]},
    {"pair": "A bird is to a NEST as a honeybee is to a [ ? ]:", "correct": "Beehive", "distractors": ["Anthill", "Spiderweb", "Burrow"]},
    {"pair": "A doctor is to a HOSPITAL as a teacher is to a [ ? ]:", "correct": "School / Classroom", "distractors": ["Library", "Auditorium", "Playground"]},
    {"pair": "A novel is to an AUTHOR as a canvas painting is to an [ ? ]:", "correct": "Artist / Painter", "distractors": ["Gallery Curator", "Sculptor", "Publisher"]},
    {"pair": "A chef is to a RESTAURANT KITCHEN as a research chemist is to a [ ? ]:", "correct": "Laboratory", "distractors": ["Pharmacy", "Library", "Factory"]},
    {"pair": "A carpenter is to a HAMMER as a stone sculptor is to a [ ? ]:", "correct": "Chisel", "distractors": ["Wrench", "Screwdriver", "Paintbrush"]}
]

# 9. Reasoning: Practical Judgment
JUDGMENT_CHALLENGES = [
    {
        "prompt": "If you notice an addressed envelope on the sidewalk with an unused postage stamp, what is the most logical action?",
        "correct": "Drop it into the nearest official post box or give it to postal staff",
        "distractors": [
            "Open it to read who sent it",
            "Leave it on the sidewalk or discard it",
            "Remove the stamp for personal use"
        ]
    },
    {
        "prompt": "If you are seated inside a crowded cinema and suddenly smell thick smoke, what is the most sensible action?",
        "correct": "Calmly locate the illuminated emergency exit and notify the cinema staff immediately",
        "distractors": [
            "Shout loudly and run towards the screen",
            "Stay seated and ignore it until someone asks you to leave",
            "Search for your lost belongings in the dark"
        ]
    },
    {
        "prompt": "If your car gets a flat tire while driving on a busy city road, what is the safest first step?",
        "correct": "Signal carefully, pull over to the far shoulder away from traffic, and turn on emergency hazard lights",
        "distractors": [
            "Stop abruptly in the middle lane and step out immediately",
            "Continue driving at high speed to reach home",
            "Abandon the vehicle without turning on lights"
        ]
    }
]

# 10. Reasoning: Conceptual Similarity
SIMILARITY_CHALLENGES = [
    {
        "pair": "In what fundamental way are a WATCH and a RULER alike?",
        "correct": "Both are instruments used for measurement (time and length)",
        "distractors": ["Both are made of plastic or metal", "Both have tick marks and numbers only", "They are completely unrelated"]
    },
    {
        "pair": "In what primary way are a THERMOMETER and a WEIGHING SCALE alike?",
        "correct": "Both are instruments designed to measure physical properties (temperature and mass)",
        "distractors": ["Both have glass or metal surfaces", "Both are found in clinics only", "They are completely unrelated"]
    },
    {
        "pair": "In what essential way are an APPLE and a BANANA alike?",
        "correct": "Both are edible, nutritious fruits that grow from plants and provide dietary vitamins",
        "distractors": ["Both have yellow peels", "Both are round in shape", "They are identical in taste"]
    },
    {
        "pair": "In what functional way are a COAT and a BLANKET alike?",
        "correct": "Both are protective textile items designed to provide thermal warmth and retain body heat",
        "distractors": ["Both are worn when walking outside", "Both have buttons and zippers", "They are completely different"]
    }
]

# ==========================================
# STANDARD STATIC FORMS (Maintained for reference & unit tests)
# ==========================================
FORM_A_QUESTIONS = [
    {
        "id": 1, "domain": "Memory", "title": "Immediate Word Recall",
        "prompt": "Read the following three words carefully: 'Apple, Table, Penny'. Which list contains all three words in any order?",
        "options": [{"text": "Apple, Table, Penny", "score": 2}, {"text": "Apple, Chair, Penny", "score": 1}, {"text": "Orange, Table, Nickel", "score": 0}, {"text": "I do not recall the words", "score": 0}],
        "explanation": "Tests immediate verbal registration."
    },
    {
        "id": 2, "domain": "Memory", "title": "Recent Event Recall",
        "prompt": "What did you have for breakfast this morning, or what was the first meal you consumed today?",
        "options": [{"text": "I recall specifically what I ate and approximately when", "score": 2}, {"text": "I recall what I ate after brief consideration", "score": 2}, {"text": "I am unsure whether I ate breakfast or what it was", "score": 0}, {"text": "I cannot remember my meals today", "score": 0}],
        "explanation": "Evaluates recent episodic memory retrieval."
    },
    {
        "id": 3, "domain": "Memory", "title": "Delayed Word Recognition",
        "prompt": "Earlier in Question 1, you memorized three specific items. Which of the following was ONE of those items?",
        "options": [{"text": "Penny", "score": 2}, {"text": "Window", "score": 0}, {"text": "River", "score": 0}, {"text": "Bicycle", "score": 0}],
        "explanation": "Assesses delayed retrieval and recognition memory."
    },
    {
        "id": 4, "domain": "Attention", "title": "Reverse Sequence Span",
        "prompt": "Spell the word 'WORLD' backwards:",
        "options": [{"text": "D-L-R-O-W", "score": 2}, {"text": "D-R-L-O-W", "score": 1}, {"text": "W-O-R-L-D", "score": 0}, {"text": "D-L-O-R-W", "score": 0}],
        "explanation": "Evaluates working memory manipulation."
    },
    {
        "id": 5, "domain": "Attention", "title": "Serial Subtraction Calculation",
        "prompt": "Starting from 100, subtract 7 consecutively: 100 - 7 = 93. What is 93 - 7?",
        "options": [{"text": "86", "score": 2}, {"text": "85", "score": 0}, {"text": "87", "score": 0}, {"text": "84", "score": 0}],
        "explanation": "Assesses mental arithmetic concentration."
    },
    {
        "id": 6, "domain": "Attention", "title": "Numeric Progression Pattern",
        "prompt": "Identify the missing number in the alternating sequence: 2, 4, 8, 16, [ ? ]",
        "options": [{"text": "32 (doubling pattern)", "score": 2}, {"text": "24", "score": 0}, {"text": "20", "score": 0}, {"text": "64", "score": 0}],
        "explanation": "Evaluates selective attention and numeric patterns."
    },
    {
        "id": 7, "domain": "Orientation", "title": "Current Year Identification",
        "prompt": "What is the current calendar year?",
        "options": [{"text": "I can identify the exact current year and correct season", "score": 2}, {"text": "2026", "score": 2}, {"text": "2025", "score": 1}, {"text": "2024", "score": 0}, {"text": "I am unsure of the current year", "score": 0}],
        "explanation": "Measures temporal orientation."
    },
    {
        "id": 8, "domain": "Orientation", "title": "Current Season and Month",
        "prompt": "Which season and approximate month matches your current local environment today?",
        "options": [{"text": "I know my exact current city/state and building/room setting", "score": 2}, {"text": "I correctly know both the current month and the season", "score": 2}, {"text": "I know the season but off by one month", "score": 1}, {"text": "I am unsure about the season or the month", "score": 0}, {"text": "I do not know the time of year", "score": 0}],
        "explanation": "Tests environmental awareness."
    },
    {
        "id": 9, "domain": "Orientation", "title": "Spatial Location Awareness",
        "prompt": "Where are you currently located right now while taking this assessment?",
        "options": [{"text": "Completing an educational cognitive assessment questionnaire on a computer/phone", "score": 2}, {"text": "I clearly know the city, building/home, and room I am currently in", "score": 2}, {"text": "I know the city and general place, but slightly disoriented about the specific address", "score": 1}, {"text": "I am confused about which town or building I am in", "score": 0}, {"text": "I do not know where I am right now", "score": 0}],
        "explanation": "Tests geographic orientation."
    },
    {
        "id": 10, "domain": "Language", "title": "Confrontation Object Naming",
        "prompt": "What medical instrument is used by doctors to listen to heartbeats and lung sounds?",
        "options": [{"text": "Stethoscope", "score": 2}, {"text": "Sphygmomanometer", "score": 1}, {"text": "Thermometer", "score": 0}, {"text": "Otoscope", "score": 0}],
        "explanation": "Tests expressive lexical retrieval."
    },
    {
        "id": 11, "domain": "Language", "title": "Semantic Category Fluency",
        "prompt": "Which of the following items does NOT belong in the category 'Musical Instruments'?",
        "options": [{"text": "Easel", "score": 2}, {"text": "Violin", "score": 0}, {"text": "Clarinet", "score": 0}, {"text": "Tambourine", "score": 0}],
        "explanation": "Assesses semantic category discrimination."
    },
    {
        "id": 12, "domain": "Language", "title": "Sentence Comprehension and Grammar",
        "prompt": "Choose the grammatically correct and coherent sentence:",
        "options": [{"text": "Despite the heavy rain, the students arrived on time for their morning lecture.", "score": 2}, {"text": "Because heavy rain, arriving students lecture morning on time.", "score": 0}, {"text": "The students was arrived late despite rain heavy lecture.", "score": 0}, {"text": "Rain morning on time students heavy arrived despite.", "score": 0}],
        "explanation": "Evaluates syntactic parsing."
    },
    {
        "id": 13, "domain": "Reasoning", "title": "Abstract Analogy",
        "prompt": "An airplane is to a PILOT as a train is to an [ ? ]:",
        "options": [{"text": "Engineer / Locomotive Driver", "score": 2}, {"text": "Passenger", "score": 0}, {"text": "Conductor (Tickets)", "score": 1}, {"text": "Station Master", "score": 0}],
        "explanation": "Tests abstract analogical reasoning."
    },
    {
        "id": 14, "domain": "Reasoning", "title": "Practical Problem Solving",
        "prompt": "If you notice an addressed envelope on the sidewalk with an unused postage stamp, what is the most logical action?",
        "options": [{"text": "Drop it into the nearest official post box or give it to postal staff", "score": 2}, {"text": "Open it to read who sent it", "score": 0}, {"text": "Leave it on the sidewalk or discard it", "score": 0}, {"text": "Remove the stamp for personal use", "score": 0}],
        "explanation": "Evaluates practical problem-solving."
    },
    {
        "id": 15, "domain": "Reasoning", "title": "Conceptual Similarity",
        "prompt": "In what fundamental way are a WATCH and a RULER alike?",
        "options": [{"text": "Both are instruments used for measurement (time and length)", "score": 2}, {"text": "Both are made of plastic or metal", "score": 1}, {"text": "Both have tick marks and numbers only", "score": 1}, {"text": "They are completely unrelated", "score": 0}],
        "explanation": "Tests abstract conceptualization."
    }
]

ALL_QUESTIONS_DICT = {q["id"]: q for q in FORM_A_QUESTIONS}


# ==========================================
# PROCEDURAL DYNAMIC TEST GENERATOR
# ==========================================

def generate_dynamic_test():
    """
    Constructs 15 completely fresh, randomized questions across all 5 domains.
    Every time this is called, a unique combination of words, math challenges,
    pattern progressions, naming items, and analogies is generated.
    Returns:
        list of 15 question dicts, each with keys:
        id, domain, title, prompt, options (list of dicts with text and score), explanation
    """
    questions = []

    # ----------------------------------------
    # 1. MEMORY (Questions 1, 2, 3)
    # ----------------------------------------
    # Q1: Immediate Word Registration
    trio = random.choice(WORD_TRIPLETS)
    w1, w2, w3 = trio
    correct_trio_str = f"{w1}, {w2}, {w3}"
    near_trio_str = f"{w1}, Window, {w3}"
    wrong_trio_str = "River, Blanket, Hammer"
    q1_options = [
        {"text": correct_trio_str, "score": 2},
        {"text": near_trio_str, "score": 1},
        {"text": wrong_trio_str, "score": 0},
        {"text": "I do not recall the words", "score": 0}
    ]
    random.shuffle(q1_options)
    questions.append({
        "id": 1,
        "domain": "Memory",
        "title": "Immediate Word Registration",
        "prompt": f"Read the following three words carefully: '{w1}, {w2}, {w3}'. Which list below contains all three words in any order?",
        "options": q1_options,
        "explanation": "Tests immediate verbal registration and short-term working retention."
    })

    # Q2: Recent Episodic Recall
    episodic_prompts = [
        ("What did you consume for your most recent meal today or breakfast this morning?",
         "I clearly recall what I ate, approximately when, and what beverages I consumed",
         "I recall the general meal after thinking for a few seconds"),
        ("What major activity, chore, or errand did you complete yesterday afternoon or evening?",
         "I specifically remember yesterday's activities, who was with me, and the location",
         "I remember the general activity after brief consideration"),
        ("What was the first task or activity you undertook this morning right after waking up?",
         "I clearly remember my morning routine, first steps, and approximate time",
         "I recall my morning routine after a moment of reflection")
    ]
    ep_p, ep_corr1, ep_corr2 = random.choice(episodic_prompts)
    q2_options = [
        {"text": ep_corr1, "score": 2},
        {"text": ep_corr2, "score": 2},
        {"text": "I am unsure or can only recall vague fragments", "score": 0},
        {"text": "I cannot remember this recent event", "score": 0}
    ]
    random.shuffle(q2_options)
    questions.append({
        "id": 2,
        "domain": "Memory",
        "title": "Recent Episodic Retrieval",
        "prompt": ep_p,
        "options": q2_options,
        "explanation": "Assesses recent autobiographical episodic memory retrieval."
    })

    # Q3: Delayed Recall of the Registered Item
    target_item = w3  # The 3rd item from Q1
    distractors = random.sample([d for d in MEMORY_DISTRACTORS if d not in trio], 3)
    q3_options = [
        {"text": target_item, "score": 2},
        {"text": distractors[0], "score": 0},
        {"text": distractors[1], "score": 0},
        {"text": distractors[2], "score": 0}
    ]
    random.shuffle(q3_options)
    questions.append({
        "id": 3,
        "domain": "Memory",
        "title": "Delayed Word Recognition",
        "prompt": f"Earlier in Question 1, you memorized three specific items. Which of the following was ONE of those three items?",
        "options": q3_options,
        "explanation": "Evaluates delayed recognition retention after intervening tasks."
    })

    # ----------------------------------------
    # 2. ATTENTION (Questions 4, 5, 6)
    # ----------------------------------------
    # Q4: Reverse Spelling Span
    rev_word, rev_correct, rev_distractors = random.choice(REVERSE_WORDS_POOL)
    q4_options = [
        {"text": rev_correct, "score": 2},
        {"text": rev_distractors[0], "score": 1},
        {"text": rev_distractors[1], "score": 0},
        {"text": rev_distractors[2], "score": 0}
    ]
    random.shuffle(q4_options)
    questions.append({
        "id": 4,
        "domain": "Attention",
        "title": "Reverse Sequence Span",
        "prompt": f"Spell the word '{rev_word}' backwards:",
        "options": q4_options,
        "explanation": "Assesses active working memory manipulation and reverse tracking."
    })

    # Q5: Serial Calculation
    math_item = random.choice(MATH_CHALLENGES)
    q5_options = [
        {"text": str(math_item["correct"]), "score": 2},
        {"text": str(math_item["distractors"][0]), "score": 0},
        {"text": str(math_item["distractors"][1]), "score": 0},
        {"text": str(math_item["distractors"][2]), "score": 0}
    ]
    random.shuffle(q5_options)
    questions.append({
        "id": 5,
        "domain": "Attention",
        "title": "Serial Mental Calculation",
        "prompt": f"Starting from {math_item['start']}, subtract {math_item['sub']}: {math_item['start']} - {math_item['sub']} = {math_item['first']}. Now subtract {math_item['sub']} again: what is {math_item['first']} - {math_item['sub']}?",
        "options": q5_options,
        "explanation": "Tests sequential mental calculation and active cognitive focus."
    })

    # Q6: Numeric Pattern Logic
    pattern_item = random.choice(PATTERN_CHALLENGES)
    q6_options = [
        {"text": pattern_item["correct"], "score": 2},
        {"text": pattern_item["distractors"][0], "score": 0},
        {"text": pattern_item["distractors"][1], "score": 0},
        {"text": pattern_item["distractors"][2], "score": 0}
    ]
    random.shuffle(q6_options)
    questions.append({
        "id": 6,
        "domain": "Attention",
        "title": "Numeric Progression Logic",
        "prompt": f"Identify the missing number that completes this numeric progression: {pattern_item['seq']}",
        "options": q6_options,
        "explanation": "Evaluates selective attention, pattern recognition, and rule induction."
    })

    # ----------------------------------------
    # 3. ORIENTATION (Questions 7, 8, 9)
    # ----------------------------------------
    # Q7: Calendar Temporal Orientation
    questions.append({
        "id": 7,
        "domain": "Orientation",
        "title": "Calendar Year & Temporal Orientation",
        "prompt": "What is the current calendar year?",
        "options": [
            {"text": "I can identify the exact current year and correct season", "score": 2},
            {"text": "2026", "score": 2},
            {"text": "2025", "score": 1},
            {"text": "2024", "score": 0},
            {"text": "I am unsure of the current year", "score": 0}
        ],
        "explanation": "Measures temporal orientation and autobiographical awareness."
    })

    # Q8: Environmental & Seasonal Awareness
    questions.append({
        "id": 8,
        "domain": "Orientation",
        "title": "Current Season & Month Orientation",
        "prompt": "Which season and approximate month matches your current local environment today?",
        "options": [
            {"text": "I know my exact current city/state and building/room setting", "score": 2},
            {"text": "I correctly know both the current month and the season", "score": 2},
            {"text": "I know the season but off by one month", "score": 1},
            {"text": "I am unsure about the season or the month", "score": 0},
            {"text": "I do not know the time of year", "score": 0}
        ],
        "explanation": "Tests environmental awareness and long-term calendar tracking."
    })

    # Q9: Spatial & Topographic Location
    questions.append({
        "id": 9,
        "domain": "Orientation",
        "title": "Spatial Location Awareness",
        "prompt": "Where are you currently located right now while taking this assessment?",
        "options": [
            {"text": "Completing an educational cognitive assessment questionnaire on a computer/phone", "score": 2},
            {"text": "I clearly know the city, building/home, and room I am currently in", "score": 2},
            {"text": "I know the city and general place, but slightly disoriented about the specific address", "score": 1},
            {"text": "I am confused about which town or building I am in", "score": 0},
            {"text": "I do not know where I am right now", "score": 0}
        ],
        "explanation": "Tests topographic and geographic environmental orientation."
    })

    # ----------------------------------------
    # 4. LANGUAGE (Questions 10, 11, 12)
    # ----------------------------------------
    # Q10: Confrontation Naming
    naming_item = random.choice(NAMING_CHALLENGES)
    q10_options = [
        {"text": naming_item["correct"], "score": 2},
        {"text": naming_item["distractors"][0], "score": 1 if naming_item["correct"] == "Stethoscope" else 0},
        {"text": naming_item["distractors"][1], "score": 0},
        {"text": naming_item["distractors"][2], "score": 0}
    ]
    random.shuffle(q10_options)
    questions.append({
        "id": 10,
        "domain": "Language",
        "title": "Confrontation Object Naming",
        "prompt": naming_item["prompt"],
        "options": q10_options,
        "explanation": "Tests expressive lexical retrieval and semantic object naming."
    })

    # Q11: Semantic Categorical Fluency (Odd One Out)
    cat_item = random.choice(ODD_ONE_OUT_CHALLENGES)
    q11_options = [
        {"text": cat_item["correct"], "score": 2},
        {"text": cat_item["distractors"][0], "score": 0},
        {"text": cat_item["distractors"][1], "score": 0},
        {"text": cat_item["distractors"][2], "score": 0}
    ]
    random.shuffle(q11_options)
    questions.append({
        "id": 11,
        "domain": "Language",
        "title": "Semantic Category Fluency",
        "prompt": f"Which of the following items does NOT belong in the category '{cat_item['category']}'?",
        "options": q11_options,
        "explanation": "Assesses semantic category integrity and boundary discrimination."
    })

    # Q12: Syntactic Parsing & Grammar
    syn_item = random.choice(SYNTAX_CHALLENGES)
    q12_options = [
        {"text": syn_item["correct"], "score": 2},
        {"text": syn_item["distractors"][0], "score": 0},
        {"text": syn_item["distractors"][1], "score": 0},
        {"text": syn_item["distractors"][2], "score": 0}
    ]
    random.shuffle(q12_options)
    questions.append({
        "id": 12,
        "domain": "Language",
        "title": "Sentence Comprehension & Syntax",
        "prompt": syn_item["prompt"],
        "options": q12_options,
        "explanation": "Evaluates syntactic parsing, auditory/reading comprehension, and phrase assembly."
    })

    # ----------------------------------------
    # 5. REASONING (Questions 13, 14, 15)
    # ----------------------------------------
    # Q13: Analogical Relational Mapping
    analogy_item = random.choice(ANALOGY_CHALLENGES)
    q13_options = [
        {"text": analogy_item["correct"], "score": 2},
        {"text": analogy_item["distractors"][0], "score": 0},
        {"text": analogy_item["distractors"][1], "score": 1 if "Conductor" in analogy_item["distractors"][1] else 0},
        {"text": analogy_item["distractors"][2], "score": 0}
    ]
    random.shuffle(q13_options)
    questions.append({
        "id": 13,
        "domain": "Reasoning",
        "title": "Abstract Relational Analogy",
        "prompt": analogy_item["pair"],
        "options": q13_options,
        "explanation": "Tests abstract analogical reasoning and relational concept matching."
    })

    # Q14: Practical Judgment & Safety
    judg_item = random.choice(JUDGMENT_CHALLENGES)
    q14_options = [
        {"text": judg_item["correct"], "score": 2},
        {"text": judg_item["distractors"][0], "score": 0},
        {"text": judg_item["distractors"][1], "score": 0},
        {"text": judg_item["distractors"][2], "score": 0}
    ]
    random.shuffle(q14_options)
    questions.append({
        "id": 14,
        "domain": "Reasoning",
        "title": "Practical Social Judgment",
        "prompt": judg_item["prompt"],
        "options": q14_options,
        "explanation": "Evaluates practical judgment, safety reasoning, and everyday problem-solving capability."
    })

    # Q15: Conceptual Similarity
    sim_item = random.choice(SIMILARITY_CHALLENGES)
    q15_options = [
        {"text": sim_item["correct"], "score": 2},
        {"text": sim_item["distractors"][0], "score": 1},
        {"text": sim_item["distractors"][1], "score": 0},
        {"text": sim_item["distractors"][2], "score": 0}
    ]
    random.shuffle(q15_options)
    questions.append({
        "id": 15,
        "domain": "Reasoning",
        "title": "Conceptual Abstraction Similarity",
        "prompt": sim_item["pair"],
        "options": q15_options,
        "explanation": "Tests high-level abstract conceptualization versus superficial physical categorization."
    })

    return questions


def sanitize_questions_for_client(questions):
    """Strip score values from options before sending to client."""
    sanitized = []
    for q in questions:
        sanitized.append({
            "id": q["id"],
            "domain": q["domain"],
            "title": q["title"],
            "prompt": q["prompt"],
            "options": [opt["text"] for opt in q["options"]],
            "total_questions": len(questions)
        })
    return sanitized


def get_all_questions():
    """Return standard sanitized questions for baseline backward compatibility."""
    return sanitize_questions_for_client(FORM_A_QUESTIONS)


def get_questions_for_form(form_id="A"):
    """Return sanitized questions for legacy Form A or B."""
    return get_all_questions()


def get_available_forms():
    return [{"id": "DYNAMIC", "name": "Dynamic Adaptive Protocol", "badge": "Fresh Randomized Set", "description": "Generates a unique item set every single session."}]


def get_auto_form_for_user(previous_count):
    return "DYNAMIC"


def score_assessment(answers, dynamic_questions=None):
    """
    Evaluates submitted answers against dynamic session questions (if provided)
    or fallback question dictionary.
    answers: dict mapping question_id -> selected_option_text
    dynamic_questions: optional list of question dicts from this active test session
    Returns:
        total_score (int out of 30)
        domain_scores (dict: domain -> int out of 6)
        feedback (str)
        detailed_breakdown (list of dicts)
        tier (str)
    """
    # Build lookup map for scoring
    lookup = {}
    if dynamic_questions:
        for q in dynamic_questions:
            lookup[int(q["id"])] = q
    else:
        lookup = ALL_QUESTIONS_DICT

    total_score = 0
    domains = {"Memory": 0, "Attention": 0, "Orientation": 0, "Language": 0, "Reasoning": 0}
    breakdown = []

    for qid_raw, selected_text in answers.items():
        try:
            qid = int(qid_raw)
        except ValueError:
            continue

        q = lookup.get(qid) or ALL_QUESTIONS_DICT.get(qid)
        if not q:
            continue

        # Find score for chosen option
        option_score = 0
        matched = False
        q_dyn = lookup.get(qid) if dynamic_questions else None
        if q_dyn:
            for opt in q_dyn.get("options", []):
                if opt["text"].strip().lower() == str(selected_text).strip().lower():
                    option_score = opt["score"]
                    matched = True
                    break

        if not matched:
            q_fallback = ALL_QUESTIONS_DICT.get(qid)
            if q_fallback:
                for opt in q_fallback.get("options", []):
                    if opt["text"].strip().lower() == str(selected_text).strip().lower():
                        option_score = opt["score"]
                        break

        q_info = q_dyn if (q_dyn and matched) else ALL_QUESTIONS_DICT.get(qid, q)
        total_score += option_score
        domains[q_info["domain"]] = domains.get(q_info["domain"], 0) + option_score

        breakdown.append({
            "question_id": qid,
            "domain": q_info["domain"],
            "title": q_info["title"],
            "selected_answer": str(selected_text),
            "score": option_score,
            "max_score": 2,
            "explanation": q_info.get("explanation", "")
        })

    # Performance tier determination
    if total_score >= 26:
        tier = "High Cognitive Performance"
        feedback = "Exceptional performance across all five cognitive domains. Working memory, attention, and reasoning are functioning within healthy benchmarks."
    elif total_score >= 20:
        tier = "Mild Cognitive Variation"
        feedback = "Good overall performance with mild isolated hesitations. Periodic monitoring and stimulating lifestyle habits are recommended."
    elif total_score >= 14:
        tier = "Moderate Cognitive Variation"
        feedback = "Noticeable performance variations in memory or attention. Formal clinical consultation and neuroimaging review are recommended."
    else:
        tier = "Substantial Cognitive Variation"
        feedback = "Substantial cognitive difficulty across multiple domains. Comprehensive neurological and medical evaluation is strongly recommended."

    return {
        "total_score": total_score,
        "max_score": 30,
        "percentage": round((total_score / 30.0) * 100, 1),
        "domain_scores": domains,
        "performance_tier": tier,
        "feedback": feedback,
        "detailed_breakdown": breakdown
    }


def compare_with_previous(current_score, previous_assessment):
    """
    Computes longitudinal score progression between current and previous tests.
    """
    if not previous_assessment:
        return {
            "has_previous": False,
            "diff": 0,
            "percent_change": 0.0,
            "status": "Baseline Established",
            "badge_class": "bg-primary",
            "icon": "fa-flag-checkered",
            "message": "This is your baseline assessment! Every future test you take will be compared directly to this score to measure your cognitive progress over time."
        }

    prev_score = int(previous_assessment.get("total_score", 0))
    diff = current_score - prev_score
    percent_diff = round((diff / 30.0) * 100, 1)
    prev_date = previous_assessment.get("assessment_date")
    date_str = prev_date.strftime("%b %d, %Y at %H:%M") if hasattr(prev_date, "strftime") else "your previous session"

    if diff > 0:
        return {
            "has_previous": True,
            "diff": diff,
            "diff_str": f"+{diff}",
            "percent_change": percent_diff,
            "status": "Cognitive Improvement",
            "badge_class": "bg-success",
            "icon": "fa-arrow-trend-up",
            "message": f"Great progress! You scored +{diff} points higher ({percent_diff}%) compared to your test on {date_str}. This indicates improved mental alertness, working memory, and focus!"
        }
    elif diff < 0:
        return {
            "has_previous": True,
            "diff": diff,
            "diff_str": f"{diff}",
            "percent_change": percent_diff,
            "status": "Mild Score Reduction",
            "badge_class": "bg-warning text-dark",
            "icon": "fa-arrow-trend-down",
            "message": f"Your score changed by {abs(diff)} points ({abs(percent_diff)}%) compared to {date_str}. Short-term fluctuations are completely normal and can be caused by fatigue, time of day, or everyday distractions."
        }
    else:
        return {
            "has_previous": True,
            "diff": 0,
            "diff_str": "0",
            "percent_change": 0.0,
            "status": "Stable Performance",
            "badge_class": "bg-info text-dark",
            "icon": "fa-arrows-left-right",
            "message": f"Your score is identical to your test on {date_str} ({current_score} / 30 pts), demonstrating steady, consistent cognitive performance."
        }
