"""Seed / reset demo data in Firestore (used by CLI / Cloud Shell).
Complies strictly with all allergen and exclusion rules and IST date handling:
- demo-ramesh: Telangana, exclusions=["Egg", "All meat"], allergens=["Nuts"] (ZERO nuts/peanuts/almonds/eggs/meat)
- demo-lakshmi: Tamil Nadu, exclusions=["Beef", "Pork"], allergens=[] (ZERO beef/pork)
- demo-ananya: Karnataka, invited
"""
import os
import random
from datetime import datetime, timezone, timedelta
import db

IST = timezone(timedelta(hours=5, minutes=30))

RECIPES = [
    ("Ragi dosa with sambar",        210, 380, []),
    ("Moong dal chilla",             180, 320, []),
    ("Bajra khichdi",                240, 400, []),
    ("Sprouts & cucumber salad",     130, 150, []),
    ("Vegetable oats upma",          190, 350, ["gluten"]),
    ("Palak paneer (low-oil)",       230, 450, ["dairy"]),
    ("Masala egg-white bhurji",      160, 300, ["egg"]),
    ("Grilled fish with vegetables", 260, 380, ["seafood"]),
    ("Chicken curry (low-oil)",      290, 420, ["chicken"]),
    ("Methi thepla (low-oil)",       200, 340, ["gluten"]),
    ("Cucumber raita",                80, 120, ["dairy"]),
    ("Roasted chana chaat",          140, 200, []),
    ("Plain roasted makhana",         90,  60, []),
    ("Lauki sabzi with 2 phulka",    310, 420, ["gluten"]),
    ("Millet vegetable bowl",        280, 300, []),
    ("Buttermilk (unsalted)",         40,  50, ["dairy"]),
]

# Telangana 8-slot Menus for Ramesh (Strictly NO nuts, NO peanuts, NO almonds, NO cashews, NO egg, NO meat)
RAMESH_MENUS = [
    # Menu 0
    [
        {"slot": "wake-up drink", "suggestion": "Warm methi water (1 glass)", "kcal": 5, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 10, "protein_g": 0},
        {"slot": "breakfast", "suggestion": "2 Ragi dosa with vegetable sambar & mint chutney", "kcal": 260, "carbs_g": 42, "sugar_g": 3, "sodium_mg": 380, "protein_g": 8},
        {"slot": "mid-day snack", "suggestion": "Sprouted moong & cucumber salad with lemon", "kcal": 140, "carbs_g": 20, "sugar_g": 2, "sodium_mg": 150, "protein_g": 8},
        {"slot": "lunch", "suggestion": "2 Jonna rotis with tomato pappu & cabbage vepudu", "kcal": 450, "carbs_g": 72, "sugar_g": 4, "sodium_mg": 460, "protein_g": 16},
        {"slot": "evening tea", "suggestion": "Green tea, unsweetened", "kcal": 5, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 5, "protein_g": 0},
        {"slot": "evening snack", "suggestion": "Roasted chana chaat with onion & coriander", "kcal": 150, "carbs_g": 24, "sugar_g": 2, "sodium_mg": 210, "protein_g": 8},
        {"slot": "dinner", "suggestion": "Samalu khichdi with lauki sabzi & bowl of curd", "kcal": 410, "carbs_g": 64, "sugar_g": 4, "sodium_mg": 420, "protein_g": 12},
        {"slot": "bedtime", "suggestion": "Warm low-fat milk with cinnamon", "kcal": 75, "carbs_g": 8, "sugar_g": 6, "sodium_mg": 80, "protein_g": 6},
    ],
    # Menu 1
    [
        {"slot": "wake-up drink", "suggestion": "Warm jeera & ajwain water", "kcal": 5, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 10, "protein_g": 0},
        {"slot": "breakfast", "suggestion": "2 Pesarattu with ginger allam pachadi & sambar", "kcal": 280, "carbs_g": 38, "sugar_g": 2, "sodium_mg": 360, "protein_g": 14},
        {"slot": "mid-day snack", "suggestion": "Guava slices sprinkled with roasted cumin powder", "kcal": 80, "carbs_g": 18, "sugar_g": 9, "sodium_mg": 30, "protein_g": 2},
        {"slot": "lunch", "suggestion": "2 Sajja (bajra) rotis with dosakaya pappu & bendakaya vepudu", "kcal": 460, "carbs_g": 70, "sugar_g": 3, "sodium_mg": 470, "protein_g": 15},
        {"slot": "evening tea", "suggestion": "Lemon ginger herbal tea", "kcal": 5, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 5, "protein_g": 0},
        {"slot": "evening snack", "suggestion": "Plain roasted makhana with pinch of black pepper", "kcal": 120, "carbs_g": 20, "sugar_g": 0, "sodium_mg": 90, "protein_g": 4},
        {"slot": "dinner", "suggestion": "Jowar vegetable upma with cucumber raita", "kcal": 390, "carbs_g": 60, "sugar_g": 4, "sodium_mg": 380, "protein_g": 11},
        {"slot": "bedtime", "suggestion": "Warm water with pinch of turmeric & black pepper", "kcal": 3, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 5, "protein_g": 0},
    ],
    # Menu 2
    [
        {"slot": "wake-up drink", "suggestion": "Cinnamon infused warm water", "kcal": 4, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 5, "protein_g": 0},
        {"slot": "breakfast", "suggestion": "Moong dal chilla with mint coriander chutney", "kcal": 250, "carbs_g": 34, "sugar_g": 2, "sodium_mg": 340, "protein_g": 13},
        {"slot": "mid-day snack", "suggestion": "Roasted pumpkin & sunflower seeds mix", "kcal": 110, "carbs_g": 6, "sugar_g": 0, "sodium_mg": 40, "protein_g": 5},
        {"slot": "lunch", "suggestion": "Samalu (little millet) rice with palak dal & dondakaya vepudu", "kcal": 440, "carbs_g": 68, "sugar_g": 3, "sodium_mg": 440, "protein_g": 14},
        {"slot": "evening tea", "suggestion": "Spiced unsalted buttermilk with curry leaves", "kcal": 45, "carbs_g": 5, "sugar_g": 3, "sodium_mg": 110, "protein_g": 3},
        {"slot": "evening snack", "suggestion": "Boiled kala chana sundal with mustard seeds", "kcal": 140, "carbs_g": 22, "sugar_g": 1, "sodium_mg": 160, "protein_g": 7},
        {"slot": "dinner", "suggestion": "2 Jonna rotis with menthi kura pappu & cucumber salad", "kcal": 420, "carbs_g": 66, "sugar_g": 3, "sodium_mg": 410, "protein_g": 14},
        {"slot": "bedtime", "suggestion": "Warm low-fat milk with pinch of nutmeg", "kcal": 75, "carbs_g": 8, "sugar_g": 6, "sodium_mg": 80, "protein_g": 6},
    ],
    # Menu 3
    [
        {"slot": "wake-up drink", "suggestion": "Warm methi & saunf water", "kcal": 5, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 10, "protein_g": 0},
        {"slot": "breakfast", "suggestion": "3 Steamed ragi idlis with vegetable sambar", "kcal": 240, "carbs_g": 40, "sugar_g": 3, "sodium_mg": 370, "protein_g": 8},
        {"slot": "mid-day snack", "suggestion": "Papaya cubes with lime juice", "kcal": 75, "carbs_g": 18, "sugar_g": 10, "sodium_mg": 25, "protein_g": 1},
        {"slot": "lunch", "suggestion": "2 Jonna rotis with beerakaya (ridge gourd) pappu & tomato salad", "kcal": 430, "carbs_g": 68, "sugar_g": 4, "sodium_mg": 430, "protein_g": 13},
        {"slot": "evening tea", "suggestion": "Tulsi ginger green tea", "kcal": 4, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 5, "protein_g": 0},
        {"slot": "evening snack", "suggestion": "Roasted soybean & puffed murmura chaat", "kcal": 135, "carbs_g": 20, "sugar_g": 1, "sodium_mg": 150, "protein_g": 8},
        {"slot": "dinner", "suggestion": "Korra (foxtail millet) khichdi with mixed vegetable kootu", "kcal": 400, "carbs_g": 62, "sugar_g": 3, "sodium_mg": 390, "protein_g": 11},
        {"slot": "bedtime", "suggestion": "Warm chamomile herbal tea", "kcal": 3, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 5, "protein_g": 0},
    ],
    # Menu 4
    [
        {"slot": "wake-up drink", "suggestion": "Warm jeera water", "kcal": 5, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 10, "protein_g": 0},
        {"slot": "breakfast", "suggestion": "Oats & vegetable uttapam with tomato mint chutney", "kcal": 260, "carbs_g": 42, "sugar_g": 3, "sodium_mg": 350, "protein_g": 9},
        {"slot": "mid-day snack", "suggestion": "Sprouted kala chana chaat with diced tomatoes", "kcal": 130, "carbs_g": 19, "sugar_g": 2, "sodium_mg": 140, "protein_g": 7},
        {"slot": "lunch", "suggestion": "2 Sajja rotis with aratikaya (plantain) kura & tomato rasam", "kcal": 440, "carbs_g": 70, "sugar_g": 3, "sodium_mg": 450, "protein_g": 12},
        {"slot": "evening tea", "suggestion": "Unsweetened cardamom tea with splash of low-fat milk", "kcal": 25, "carbs_g": 3, "sugar_g": 2, "sodium_mg": 20, "protein_g": 1},
        {"slot": "evening snack", "suggestion": "Roasted makhana tossed with turmeric & rock salt", "kcal": 115, "carbs_g": 19, "sugar_g": 0, "sodium_mg": 85, "protein_g": 4},
        {"slot": "dinner", "suggestion": "2 Jonna rotis with palak sabzi & plain low-fat curd", "kcal": 430, "carbs_g": 66, "sugar_g": 4, "sodium_mg": 400, "protein_g": 15},
        {"slot": "bedtime", "suggestion": "Warm low-fat milk with cinnamon", "kcal": 75, "carbs_g": 8, "sugar_g": 6, "sodium_mg": 80, "protein_g": 6},
    ],
    # Menu 5
    [
        {"slot": "wake-up drink", "suggestion": "Warm cinnamon & methi water", "kcal": 5, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 10, "protein_g": 0},
        {"slot": "breakfast", "suggestion": "2 Pesarattu with tomato allam pachadi", "kcal": 270, "carbs_g": 37, "sugar_g": 2, "sodium_mg": 350, "protein_g": 13},
        {"slot": "mid-day snack", "suggestion": "Fresh tender cucumber & carrot sticks with hung curd dip", "kcal": 85, "carbs_g": 12, "sugar_g": 4, "sodium_mg": 70, "protein_g": 4},
        {"slot": "lunch", "suggestion": "Samalu rice with dosakaya pappu & karela (bitter gourd) stir fry", "kcal": 435, "carbs_g": 67, "sugar_g": 3, "sodium_mg": 440, "protein_g": 13},
        {"slot": "evening tea", "suggestion": "Fresh lemon mint water with chia seeds", "kcal": 20, "carbs_g": 3, "sugar_g": 1, "sodium_mg": 10, "protein_g": 1},
        {"slot": "evening snack", "suggestion": "Roasted chana & puffed jowar mix", "kcal": 130, "carbs_g": 21, "sugar_g": 1, "sodium_mg": 140, "protein_g": 6},
        {"slot": "dinner", "suggestion": "Jowar dahlia vegetable soup with 1 jonna roti", "kcal": 390, "carbs_g": 60, "sugar_g": 3, "sodium_mg": 380, "protein_g": 11},
        {"slot": "bedtime", "suggestion": "Warm water with turmeric & crushed black pepper", "kcal": 3, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 5, "protein_g": 0},
    ],
    # Menu 6
    [
        {"slot": "wake-up drink", "suggestion": "Warm water with soaked chia seeds & lemon", "kcal": 15, "carbs_g": 2, "sugar_g": 0, "sodium_mg": 10, "protein_g": 1},
        {"slot": "breakfast", "suggestion": "2 Moong dal & spinach chillas with mint chutney", "kcal": 255, "carbs_g": 33, "sugar_g": 2, "sodium_mg": 330, "protein_g": 14},
        {"slot": "mid-day snack", "suggestion": "Sprouted moong & pomegranate salad", "kcal": 125, "carbs_g": 21, "sugar_g": 6, "sodium_mg": 90, "protein_g": 6},
        {"slot": "lunch", "suggestion": "2 Jonna rotis with menthi kura pappu & dondakaya vepudu", "kcal": 460, "carbs_g": 71, "sugar_g": 3, "sodium_mg": 460, "protein_g": 15},
        {"slot": "evening tea", "suggestion": "Spiced chaas (buttermilk) with roasted jeera", "kcal": 40, "carbs_g": 4, "sugar_g": 2, "sodium_mg": 100, "protein_g": 3},
        {"slot": "evening snack", "suggestion": "Boiled moong sundal tempered with mustard & curry leaves", "kcal": 120, "carbs_g": 18, "sugar_g": 1, "sodium_mg": 130, "protein_g": 6},
        {"slot": "dinner", "suggestion": "Korra khichdi with bottle gourd stew & cucumber salad", "kcal": 405, "carbs_g": 63, "sugar_g": 3, "sodium_mg": 390, "protein_g": 10},
        {"slot": "bedtime", "suggestion": "Warm low-fat milk with cardamom", "kcal": 75, "carbs_g": 8, "sugar_g": 6, "sodium_mg": 80, "protein_g": 6},
    ],
    # Menu 7
    [
        {"slot": "wake-up drink", "suggestion": "Warm jeera & methi water", "kcal": 5, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 10, "protein_g": 0},
        {"slot": "breakfast", "suggestion": "2 Ragi dosas with onion tomato sambar", "kcal": 250, "carbs_g": 40, "sugar_g": 3, "sodium_mg": 360, "protein_g": 7},
        {"slot": "mid-day snack", "suggestion": "Roasted watermelon & pumpkin seeds", "kcal": 105, "carbs_g": 5, "sugar_g": 0, "sodium_mg": 35, "protein_g": 5},
        {"slot": "lunch", "suggestion": "2 Sajja rotis with tomato pappu & bendakaya vepudu", "kcal": 450, "carbs_g": 69, "sugar_g": 4, "sodium_mg": 450, "protein_g": 15},
        {"slot": "evening tea", "suggestion": "Tulsi green tea with ginger", "kcal": 5, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 5, "protein_g": 0},
        {"slot": "evening snack", "suggestion": "Spiced roasted makhana with chaat masala", "kcal": 115, "carbs_g": 19, "sugar_g": 0, "sodium_mg": 85, "protein_g": 4},
        {"slot": "dinner", "suggestion": "Samalu khichdi with mixed vegetable sambar & curd", "kcal": 410, "carbs_g": 64, "sugar_g": 4, "sodium_mg": 410, "protein_g": 12},
        {"slot": "bedtime", "suggestion": "Warm chamomile herbal tea", "kcal": 3, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 5, "protein_g": 0},
    ]
]

# Tamil Nadu 8-slot Menus for Lakshmi (Strictly NO beef, NO pork; fish/chicken/eggs allowed)
LAKSHMI_MENUS = [
    # Menu 0
    [
        {"slot": "wake-up drink", "suggestion": "Warm curry leaves & coriander seed water", "kcal": 5, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 10, "protein_g": 0},
        {"slot": "breakfast", "suggestion": "2 Kambu (bajra) dosai with tomato kurma & mint chutney", "kcal": 230, "carbs_g": 36, "sugar_g": 3, "sodium_mg": 340, "protein_g": 7},
        {"slot": "mid-day snack", "suggestion": "Konda kadalai sundal (boiled black chana with coconut)", "kcal": 130, "carbs_g": 18, "sugar_g": 1, "sodium_mg": 160, "protein_g": 7},
        {"slot": "lunch", "suggestion": "Steamed brown ponni rice + Meen kulambu (grilled seer fish curry) + cabbage poriyal", "kcal": 390, "carbs_g": 50, "sugar_g": 2, "sodium_mg": 420, "protein_g": 26},
        {"slot": "evening tea", "suggestion": "Sukku malli coffee (unsweetened ginger-coriander brew)", "kcal": 8, "carbs_g": 2, "sugar_g": 0, "sodium_mg": 10, "protein_g": 0},
        {"slot": "evening snack", "suggestion": "Pasi paruppu sundal (yellow moong sundal)", "kcal": 110, "carbs_g": 16, "sugar_g": 1, "sodium_mg": 130, "protein_g": 6},
        {"slot": "dinner", "suggestion": "Varagu (kodo millet) adai with mixed vegetable avial", "kcal": 330, "carbs_g": 50, "sugar_g": 3, "sodium_mg": 360, "protein_g": 12},
        {"slot": "bedtime", "suggestion": "Warm low-fat milk with crushed cardamom", "kcal": 70, "carbs_g": 7, "sugar_g": 6, "sodium_mg": 75, "protein_g": 5},
    ],
    # Menu 1
    [
        {"slot": "wake-up drink", "suggestion": "Warm lemon water with soaked chia seeds", "kcal": 15, "carbs_g": 2, "sugar_g": 0, "sodium_mg": 5, "protein_g": 1},
        {"slot": "breakfast", "suggestion": "3 Thinai (foxtail millet) idlis with murungakkai (drumstick) sambar", "kcal": 220, "carbs_g": 36, "sugar_g": 2, "sodium_mg": 330, "protein_g": 7},
        {"slot": "mid-day snack", "suggestion": "Cucumber & raw mango slices with chaat masala", "kcal": 50, "carbs_g": 11, "sugar_g": 4, "sodium_mg": 40, "protein_g": 1},
        {"slot": "lunch", "suggestion": "Kuthiraivali (barnyard millet) rice with keerai (spinach) kootu & 2 egg-white podimas", "kcal": 380, "carbs_g": 52, "sugar_g": 2, "sodium_mg": 390, "protein_g": 20},
        {"slot": "evening tea", "suggestion": "Neer mor (spiced buttermilk with ginger & asafoetida)", "kcal": 35, "carbs_g": 3, "sugar_g": 2, "sodium_mg": 90, "protein_g": 2},
        {"slot": "evening snack", "suggestion": "Roasted edamame & makhana mix", "kcal": 115, "carbs_g": 14, "sugar_g": 1, "sodium_mg": 70, "protein_g": 6},
        {"slot": "dinner", "suggestion": "Grilled vanjaram (seer fish) with sauteed beans, carrots & 1 multigrain phulka", "kcal": 320, "carbs_g": 24, "sugar_g": 2, "sodium_mg": 350, "protein_g": 28},
        {"slot": "bedtime", "suggestion": "Chamomile herbal infusion", "kcal": 2, "carbs_g": 0, "sugar_g": 0, "sodium_mg": 5, "protein_g": 0},
    ],
    # Menu 2
    [
        {"slot": "wake-up drink", "suggestion": "Warm water with crushed cumin & methi seeds", "kcal": 5, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 10, "protein_g": 0},
        {"slot": "breakfast", "suggestion": "Ragi semiya upma with green peas & carrots + coconut chutney", "kcal": 240, "carbs_g": 40, "sugar_g": 3, "sodium_mg": 320, "protein_g": 6},
        {"slot": "mid-day snack", "suggestion": "Vellai sundal (boiled white chickpeas tempered with mustard)", "kcal": 135, "carbs_g": 19, "sugar_g": 1, "sodium_mg": 150, "protein_g": 7},
        {"slot": "lunch", "suggestion": "2 Multigrain phulkas with Naatu kozhi kulambu (lean chicken curry) & cucumber raita", "kcal": 410, "carbs_g": 46, "sugar_g": 3, "sodium_mg": 430, "protein_g": 28},
        {"slot": "evening tea", "suggestion": "Sukku coffee (dry ginger tea, unsweetened)", "kcal": 6, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 5, "protein_g": 0},
        {"slot": "evening snack", "suggestion": "Kollu (horse gram) sundal with grated fresh coconut", "kcal": 120, "carbs_g": 16, "sugar_g": 1, "sodium_mg": 120, "protein_g": 7},
        {"slot": "dinner", "suggestion": "Samai (little millet) vegetable khichdi with kathirikai kootu", "kcal": 330, "carbs_g": 52, "sugar_g": 3, "sodium_mg": 360, "protein_g": 10},
        {"slot": "bedtime", "suggestion": "Warm low-fat turmeric milk", "kcal": 70, "carbs_g": 7, "sugar_g": 6, "sodium_mg": 75, "protein_g": 5},
    ],
    # Menu 3
    [
        {"slot": "wake-up drink", "suggestion": "Warm tulsi & cinnamon water", "kcal": 4, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 5, "protein_g": 0},
        {"slot": "breakfast", "suggestion": "2 Varagu (kodo millet) dosai with tomato onion chutney", "kcal": 230, "carbs_g": 38, "sugar_g": 2, "sodium_mg": 330, "protein_g": 6},
        {"slot": "mid-day snack", "suggestion": "Guava wedges with pinch of black salt", "kcal": 65, "carbs_g": 15, "sugar_g": 8, "sodium_mg": 30, "protein_g": 2},
        {"slot": "lunch", "suggestion": "Steamed brown rice with Nethili meen kulambu (anchovy fish curry) & beetroot poriyal", "kcal": 390, "carbs_g": 50, "sugar_g": 2, "sodium_mg": 410, "protein_g": 25},
        {"slot": "evening tea", "suggestion": "Green tea with fresh mint leaves", "kcal": 4, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 5, "protein_g": 0},
        {"slot": "evening snack", "suggestion": "Mochai (field beans) sundal tempered with mustard", "kcal": 125, "carbs_g": 17, "sugar_g": 1, "sodium_mg": 130, "protein_g": 7},
        {"slot": "dinner", "suggestion": "2 Chapati with mealmaker (soya chunks) & vegetable kurma", "kcal": 340, "carbs_g": 48, "sugar_g": 3, "sodium_mg": 370, "protein_g": 18},
        {"slot": "bedtime", "suggestion": "Warm low-fat milk with nutmeg", "kcal": 70, "carbs_g": 7, "sugar_g": 6, "sodium_mg": 75, "protein_g": 5},
    ],
    # Menu 4
    [
        {"slot": "wake-up drink", "suggestion": "Warm curry leaves & cumin infusion", "kcal": 5, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 10, "protein_g": 0},
        {"slot": "breakfast", "suggestion": "Kavuni arisi (black rice) idli with vegetable sambar", "kcal": 225, "carbs_g": 36, "sugar_g": 2, "sodium_mg": 320, "protein_g": 6},
        {"slot": "mid-day snack", "suggestion": "Thattai payaru (cowpea/black-eyed pea) sundal", "kcal": 130, "carbs_g": 18, "sugar_g": 1, "sodium_mg": 140, "protein_g": 7},
        {"slot": "lunch", "suggestion": "Samai rice with murungakkai sambar, snake gourd kootu & boiled egg", "kcal": 385, "carbs_g": 54, "sugar_g": 3, "sodium_mg": 400, "protein_g": 17},
        {"slot": "evening tea", "suggestion": "Neer mor (spiced buttermilk)", "kcal": 35, "carbs_g": 3, "sugar_g": 2, "sodium_mg": 90, "protein_g": 2},
        {"slot": "evening snack", "suggestion": "Roasted makhana seasoned with curry leaf powder", "kcal": 100, "carbs_g": 16, "sugar_g": 0, "sodium_mg": 60, "protein_g": 4},
        {"slot": "dinner", "suggestion": "Steamed fish fillet with stir-fried kovakkai (ivy gourd) & 1 multigrain roti", "kcal": 310, "carbs_g": 26, "sugar_g": 2, "sodium_mg": 350, "protein_g": 26},
        {"slot": "bedtime", "suggestion": "Chamomile infusion", "kcal": 2, "carbs_g": 0, "sugar_g": 0, "sodium_mg": 5, "protein_g": 0},
    ],
    # Menu 5
    [
        {"slot": "wake-up drink", "suggestion": "Warm ginger & coriander seed decoction", "kcal": 5, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 5, "protein_g": 0},
        {"slot": "breakfast", "suggestion": "2 Kambu (pearl millet) adai with murungai keerai & tomato chutney", "kcal": 250, "carbs_g": 38, "sugar_g": 2, "sodium_mg": 340, "protein_g": 8},
        {"slot": "mid-day snack", "suggestion": "Papaya slices with a squeeze of lime", "kcal": 70, "carbs_g": 16, "sugar_g": 9, "sodium_mg": 20, "protein_g": 1},
        {"slot": "lunch", "suggestion": "Brown ponni rice with Kozhi rasam (pepper chicken broth) & vazhaipoo (banana flower) poriyal", "kcal": 400, "carbs_g": 48, "sugar_g": 2, "sodium_mg": 420, "protein_g": 27},
        {"slot": "evening tea", "suggestion": "Sukku malli herbal tea", "kcal": 6, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 5, "protein_g": 0},
        {"slot": "evening snack", "suggestion": "Pasi payaru (green gram) sundal with mustard & asafoetida", "kcal": 120, "carbs_g": 17, "sugar_g": 1, "sodium_mg": 130, "protein_g": 7},
        {"slot": "dinner", "suggestion": "Thinai (foxtail millet) upma with mixed country vegetables & curd", "kcal": 325, "carbs_g": 50, "sugar_g": 3, "sodium_mg": 350, "protein_g": 9},
        {"slot": "bedtime", "suggestion": "Warm low-fat milk with cardamom", "kcal": 70, "carbs_g": 7, "sugar_g": 6, "sodium_mg": 75, "protein_g": 5},
    ],
    # Menu 6
    [
        {"slot": "wake-up drink", "suggestion": "Warm lemon water with chia seeds", "kcal": 15, "carbs_g": 2, "sugar_g": 0, "sodium_mg": 5, "protein_g": 1},
        {"slot": "breakfast", "suggestion": "3 Ragi idlis with tomato onion chutney & vegetable sambar", "kcal": 220, "carbs_g": 37, "sugar_g": 2, "sodium_mg": 330, "protein_g": 7},
        {"slot": "mid-day snack", "suggestion": "Sprouted moong salad with diced cucumber & coriander", "kcal": 110, "carbs_g": 16, "sugar_g": 2, "sodium_mg": 110, "protein_g": 7},
        {"slot": "lunch", "suggestion": "Kuthiraivali rice with Meen kulambu (fish curry) & vendakkai (okra) poriyal", "kcal": 390, "carbs_g": 50, "sugar_g": 2, "sodium_mg": 410, "protein_g": 26},
        {"slot": "evening tea", "suggestion": "Spiced buttermilk with curry leaves", "kcal": 35, "carbs_g": 3, "sugar_g": 2, "sodium_mg": 90, "protein_g": 2},
        {"slot": "evening snack", "suggestion": "Roasted edamame / makhana mix", "kcal": 110, "carbs_g": 14, "sugar_g": 1, "sodium_mg": 70, "protein_g": 6},
        {"slot": "dinner", "suggestion": "2 Multigrain phulkas with egg podimas (scrambled eggs with onions) & rasam", "kcal": 340, "carbs_g": 38, "sugar_g": 2, "sodium_mg": 380, "protein_g": 20},
        {"slot": "bedtime", "suggestion": "Warm water with turmeric", "kcal": 3, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 5, "protein_g": 0},
    ],
    # Menu 7
    [
        {"slot": "wake-up drink", "suggestion": "Warm curry leaves & coriander water", "kcal": 5, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 10, "protein_g": 0},
        {"slot": "breakfast", "suggestion": "2 Samai (little millet) dosai with coconut mint chutney & sambar", "kcal": 235, "carbs_g": 38, "sugar_g": 2, "sodium_mg": 340, "protein_g": 6},
        {"slot": "mid-day snack", "suggestion": "Konda kadalai sundal", "kcal": 125, "carbs_g": 17, "sugar_g": 1, "sodium_mg": 150, "protein_g": 7},
        {"slot": "lunch", "suggestion": "Brown rice with chicken & keerai kootu + cucumber salad", "kcal": 405, "carbs_g": 47, "sugar_g": 2, "sodium_mg": 420, "protein_g": 28},
        {"slot": "evening tea", "suggestion": "Green tea with lemon", "kcal": 4, "carbs_g": 1, "sugar_g": 0, "sodium_mg": 5, "protein_g": 0},
        {"slot": "evening snack", "suggestion": "Boiled sweet corn with pepper and lime", "kcal": 115, "carbs_g": 22, "sugar_g": 3, "sodium_mg": 80, "protein_g": 3},
        {"slot": "dinner", "suggestion": "Varagu adai with mixed vegetable avial", "kcal": 325, "carbs_g": 49, "sugar_g": 3, "sodium_mg": 360, "protein_g": 12},
        {"slot": "bedtime", "suggestion": "Warm low-fat milk with cardamom", "kcal": 70, "carbs_g": 7, "sugar_g": 6, "sodium_mg": 75, "protein_g": 5},
    ]
]

RAMESH_ACTIVITIES = [
    "30-min brisk walk after morning tea + 15 min yoga (Vajrasana, Bhujangasana & Ardha Matsyendrasana)",
    "30-min evening walk + 15 min yoga (Pawanmuktasana, Setu Bandhasana & Tadasana)",
    "25-min brisk walk + 20 min yoga (Vrikshasana, Paschimottanasana & Mandukasana)",
    "30-min morning walk + 15 min yoga (Bhujangasana, Gomukhasana & Shavasana)",
    "35-min park walk + 15 min yoga (Vajrasana, Dhanurasana & Anjaneyasana)",
    "30-min brisk walk + 15 min yoga (Ardha Matsyendrasana, Uttanasana & Balasana)",
    "30-min post-breakfast walk + 15 min yoga (Setu Bandhasana, Trikonasana & Pranamasana)",
    "25-min morning walk + 20 min yoga (Pawanmuktasana, Mandukasana & Vajrasana)"
]

LAKSHMI_ACTIVITIES = [
    "35-min morning brisk walk + 15 min yoga (Trikonasana, Vrikshasana & Bhujangasana)",
    "30-min park walk + 15 min yoga (Vajrasana, Setu Bandhasana & Baddhakonasana)",
    "35-min morning walk + 15 min yoga (Ardha Matsyendrasana, Tadasana & Shavasana)",
    "40-min brisk walk + 10 min yoga (Pawanmuktasana, Paschimottanasana & Balasana)",
    "30-min morning walk + 20 min yoga (Marjaryasana, Bitilasana & Gomukhasana)",
    "35-min neighborhood walk + 15 min yoga (Vrikshasana, Uttanasana & Bhujangasana)",
    "30-min walk + 15 min yoga (Setu Bandhasana, Vajrasana & Ananda Balasana)",
    "35-min brisk walk + 15 min yoga (Ardha Matsyendrasana, Trikonasana & Pranayama)"
]


def run_reset():
    firestore_client = db.client()
    for name, kcal, sodium, contains in RECIPES:
        firestore_client.collection("recipes").document(name.lower().replace(" ", "-")).set({
            "name": name, "kcal": kcal, "sodium_mg": sodium,
            "contains": contains, "low_gi": True})

    org = firestore_client.collection("orgs").document(db.ORG)
    org.set({"name": "Sunrise Diabetes Clinic (demo)"})

    # Clear all alerts
    for a in org.collection("alerts").stream():
        a.reference.delete()

    # Clean up any extraneous / duplicate patients
    allowed_ids = {"demo-ramesh", "demo-lakshmi", "demo-ananya"}
    for p_doc in org.collection("patients").stream():
        if p_doc.id not in allowed_ids:
            for sub in ["vitals", "meals", "plans"]:
                for doc in p_doc.reference.collection(sub).stream():
                    doc.reference.delete()
            p_doc.reference.delete()

    today = datetime.now(IST).date()

    # =========================================================================
    # 1. PATIENT: demo-ramesh (Telangana, 30 days)
    # =========================================================================
    ramesh_ref = org.collection("patients").document("demo-ramesh")
    ramesh_ref.set({
        "name": "Ramesh Kumar (synthetic)",
        "dob": "1968-03-12",
        "gender": "Male",
        "height_cm": 170,
        "weight_kg": 78,
        "food_exclusions": ["Egg", "All meat"],
        "allergens": ["Nuts"],
        "state": "Telangana",
        "status": "active",
        "link_token": "DEMO1234",
        "guide": "Fasting sugar improved to 135 mg/dL! Let's maintain jowar rotis and evening methi water this week.",
        "guide_updated_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    })

    for sub in ["vitals", "meals", "plans"]:
        for doc in ramesh_ref.collection(sub).stream():
            doc.reference.delete()

    ramesh_unlogged = {26, 21, 15, 9, 3}

    for days_ago in range(29, -1, -1):
        d = today - timedelta(days=days_ago)
        d_str = d.isoformat()
        if days_ago in ramesh_unlogged:
            continue

        progress = (29 - days_ago) / 29.0
        base_sugar = 165 - (30 * progress)
        sugar = int(base_sugar + random.uniform(-4, 4))
        sys_bp = int(142 - (10 * progress) + random.uniform(-3, 3))
        dia_bp = int(90 - (6 * progress) + random.uniform(-2, 2))
        hr = int(78 + random.uniform(-3, 3))

        if days_ago == 18:
            sugar = 265
            sys_bp = 158
            dia_bp = 96
        elif days_ago == 7:
            sugar = 252
            sys_bp = 154
            dia_bp = 94

        dt_vitals = datetime.combine(d, datetime.strptime("06:30:00", "%H:%M:%S").time(), tzinfo=IST).astimezone(timezone.utc)
        ramesh_ref.collection("vitals").add({
            "sugar": sugar, "sys": sys_bp, "dia": dia_bp, "hr": hr,
            "ts": dt_vitals.isoformat()
        })

        # Menu rotation from RAMESH_MENUS
        menu_idx = days_ago % len(RAMESH_MENUS)
        daily_menu = RAMESH_MENUS[menu_idx]

        plan_slots = [
            {"slot": item["slot"], "suggestion": item["suggestion"], "kcal": item["kcal"]}
            for item in daily_menu
        ]

        nutri_summary = {
            "kcal": sum(item["kcal"] for item in daily_menu),
            "carbs_g": sum(item["carbs_g"] for item in daily_menu),
            "sugar_g": sum(item["sugar_g"] for item in daily_menu),
            "sodium_mg": sum(item["sodium_mg"] for item in daily_menu),
            "protein_g": sum(item["protein_g"] for item in daily_menu)
        }

        activity_str = RAMESH_ACTIVITIES[days_ago % len(RAMESH_ACTIVITIES)]

        if days_ago == 18:
            brief = "Fasting sugar elevated (265 mg/dL). Care team flagged. Emphasize complex millet carbs and stay well hydrated."
        elif days_ago == 7:
            brief = "Fasting sugar spike (252 mg/dL). Care team notified. Maintain light dinner with high fiber, avoid late evening snacks."
        elif days_ago <= 5:
            brief = "Excellent progress! Fasting sugar steady in the 135 mg/dL range. Continue complex jowar/ragi carbs and daily brisk walks."
        else:
            brief = "Target fasting sugar < 130 mg/dL. Focus on complex millet carbs (jowar/ragi) and keeping sodium under 2g."

        ramesh_ref.collection("plans").document(d_str).set({
            "date": d_str,
            "generated_at": dt_vitals.isoformat(),
            "brief": brief,
            "activity": activity_str,
            "targets": {
                "kcal": nutri_summary["kcal"],
                "sodium_g": round(nutri_summary["sodium_mg"] / 1000.0, 1),
                "steps": 6000
            },
            "nutrition_summary": nutri_summary,
            "meal_plan": plan_slots,
            "vitals": {"sugar": sugar, "sys": sys_bp, "dia": dia_bp, "hr": hr}
        })

        slots_to_log = ["wake-up drink", "breakfast", "lunch", "evening snack", "dinner"]
        if days_ago == 0:
            slots_to_log = ["wake-up drink", "breakfast", "lunch"]

        times = {
            "wake-up drink": "06:45:00",
            "breakfast": "08:30:00",
            "mid-day snack": "11:15:00",
            "lunch": "13:30:00",
            "evening tea": "17:00:00",
            "evening snack": "17:30:00",
            "dinner": "20:15:00",
            "bedtime": "22:00:00"
        }

        for slot in slots_to_log:
            dish_info = next((item for item in daily_menu if item["slot"] == slot), None)
            if not dish_info:
                continue

            time_str = times.get(slot, "12:00:00")
            dt_meal = datetime.combine(d, datetime.strptime(time_str, "%H:%M:%S").time(), tzinfo=IST).astimezone(timezone.utc)
            ramesh_ref.collection("meals").add({
                "slot": slot,
                "dish": dish_info["suggestion"],
                "kcal": dish_info["kcal"],
                "carbs_g": dish_info["carbs_g"],
                "sugar_g": dish_info["sugar_g"],
                "sodium_mg": dish_info["sodium_mg"],
                "protein_g": dish_info["protein_g"],
                "ts": dt_meal.isoformat()
            })

    # Add 2 unresolved alerts for Ramesh's spike days
    org.collection("alerts").add({
        "patient_id": "demo-ramesh",
        "message": "Ramesh Kumar: sugar 265 mg/dL, BP 158/96 — review advised",
        "severity": "critical",
        "ts": (datetime.now(timezone.utc) - timedelta(days=18, hours=-2)).isoformat(),
        "resolved": False
    })
    org.collection("alerts").add({
        "patient_id": "demo-ramesh",
        "message": "Ramesh Kumar: sugar 252 mg/dL, BP 154/94 — review advised",
        "severity": "critical",
        "ts": (datetime.now(timezone.utc) - timedelta(days=7, hours=-3)).isoformat(),
        "resolved": False
    })

    # =========================================================================
    # 2. PATIENT: demo-lakshmi (Tamil Nadu, 30 days)
    # =========================================================================
    lakshmi_ref = org.collection("patients").document("demo-lakshmi")
    lakshmi_ref.set({
        "name": "Lakshmi Devi (synthetic)",
        "dob": "1974-06-18",
        "gender": "Female",
        "height_cm": 158,
        "weight_kg": 66,
        "food_exclusions": ["Beef", "Pork"],
        "allergens": [],
        "state": "Tamil Nadu",
        "status": "active",
        "link_token": "LAKSHMI01",
        "guide": "Excellent control! Keep up the morning walks and steamed fish meals.",
        "guide_updated_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    })

    for sub in ["vitals", "meals", "plans"]:
        for doc in lakshmi_ref.collection(sub).stream():
            doc.reference.delete()

    lakshmi_unlogged = {14}

    for days_ago in range(29, -1, -1):
        d = today - timedelta(days=days_ago)
        d_str = d.isoformat()
        if days_ago in lakshmi_unlogged:
            continue

        sugar = int(115 + random.uniform(-8, 8))
        sys_bp = int(120 + random.uniform(-4, 4))
        dia_bp = int(78 + random.uniform(-3, 3))
        hr = int(70 + random.uniform(-3, 3))

        dt_vitals = datetime.combine(d, datetime.strptime("06:15:00", "%H:%M:%S").time(), tzinfo=IST).astimezone(timezone.utc)
        lakshmi_ref.collection("vitals").add({
            "sugar": sugar, "sys": sys_bp, "dia": dia_bp, "hr": hr,
            "ts": dt_vitals.isoformat()
        })

        # Menu rotation from LAKSHMI_MENUS
        menu_idx = days_ago % len(LAKSHMI_MENUS)
        daily_menu = LAKSHMI_MENUS[menu_idx]

        plan_slots = [
            {"slot": item["slot"], "suggestion": item["suggestion"], "kcal": item["kcal"]}
            for item in daily_menu
        ]

        nutri_summary = {
            "kcal": sum(item["kcal"] for item in daily_menu),
            "carbs_g": sum(item["carbs_g"] for item in daily_menu),
            "sugar_g": sum(item["sugar_g"] for item in daily_menu),
            "sodium_mg": sum(item["sodium_mg"] for item in daily_menu),
            "protein_g": sum(item["protein_g"] for item in daily_menu)
        }

        activity_str = LAKSHMI_ACTIVITIES[days_ago % len(LAKSHMI_ACTIVITIES)]

        lakshmi_ref.collection("plans").document(d_str).set({
            "date": d_str,
            "generated_at": dt_vitals.isoformat(),
            "brief": "Readings are well in target range. Continue low-glycemic traditional millets and lean proteins.",
            "activity": activity_str,
            "targets": {
                "kcal": nutri_summary["kcal"],
                "sodium_g": round(nutri_summary["sodium_mg"] / 1000.0, 1),
                "steps": 7500
            },
            "nutrition_summary": nutri_summary,
            "meal_plan": plan_slots,
            "vitals": {"sugar": sugar, "sys": sys_bp, "dia": dia_bp, "hr": hr}
        })

        slots_to_log = ["wake-up drink", "breakfast", "mid-day snack", "lunch", "evening snack", "dinner"]
        if days_ago == 0:
            slots_to_log = ["wake-up drink", "breakfast", "lunch"]

        times_lakshmi = {
            "wake-up drink": "06:30:00",
            "breakfast": "08:15:00",
            "mid-day snack": "11:00:00",
            "lunch": "13:00:00",
            "evening tea": "16:45:00",
            "evening snack": "17:15:00",
            "dinner": "20:00:00",
            "bedtime": "21:45:00"
        }

        for slot in slots_to_log:
            dish_info = next((item for item in daily_menu if item["slot"] == slot), None)
            if not dish_info:
                continue

            time_str = times_lakshmi.get(slot, "12:00:00")
            dt_meal = datetime.combine(d, datetime.strptime(time_str, "%H:%M:%S").time(), tzinfo=IST).astimezone(timezone.utc)
            lakshmi_ref.collection("meals").add({
                "slot": slot,
                "dish": dish_info["suggestion"],
                "kcal": dish_info["kcal"],
                "carbs_g": dish_info["carbs_g"],
                "sugar_g": dish_info["sugar_g"],
                "sodium_mg": dish_info["sodium_mg"],
                "protein_g": dish_info["protein_g"],
                "ts": dt_meal.isoformat()
            })

    # =========================================================================
    # 3. PATIENT: demo-ananya (Karnataka, Invited)
    # =========================================================================
    ananya_ref = org.collection("patients").document("demo-ananya")
    ananya_ref.set({
        "name": "Ananya Reddy (synthetic)",
        "dob": "1988-11-24",
        "gender": "Female",
        "height_cm": 162,
        "weight_kg": 64,
        "food_exclusions": ["All meat"],
        "allergens": [],
        "state": "Karnataka",
        "status": "invited",
        "link_token": "ANANYA01"
    })
    for sub in ["vitals", "meals", "plans"]:
        for doc in ananya_ref.collection(sub).stream():
            doc.reference.delete()

    return {"status": "ok", "message": "Demo data reset successfully"}
