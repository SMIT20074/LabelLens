import re
# Top-level names from the FSSAI "Food Product Categories" list. Keywords are a simple guess, not official.
CATEGORIES = {
 "1": ("Dairy products and analogues", ["milk", "curd", "yogurt", "yoghurt", "cheese", "buttermilk", "cream", "whey", "paneer", "dahi", "lassi"]),
 "2": ("Fats and oils, fat emulsions", ["ghee", "margarine", "fat spread", "shortening", "butter"]),
 "3": ("Edible ices", ["ice cream", "kulfi", "sorbet", "frozen dessert"]),
 "4": ("Fruits and vegetables, nuts and seeds", ["jam", "pickle", "puree", "ketchup", "peanut butter", "dried fruit", "tomato", "mango"]),
 "5": ("Confectionery", ["chocolate", "cocoa", "candy", "toffee", "chewing gum", "lollipop", "confectionery"]),
 "6": ("Cereals and cereal products", ["rice", "wheat", "flour", "atta", "oats", "cereal", "noodle", "pasta", "maida", "semolina", "cornflake"]),
 "7": ("Bakery wares", ["biscuit", "cookie", "bread", "cake", "bun", "rusk", "cracker", "bakery"]),
 "8": ("Meat and meat products", ["chicken", "mutton", "meat", "sausage", "poultry"]),
 "9": ("Fish and fish products", ["fish", "prawn", "shrimp", "tuna"]),
 "11": ("Sweeteners, including honey", ["honey", "jaggery", "sweetener"]),
 "12": ("Salts, spices, soups, sauces", ["spice", "masala", "sauce", "soup", "vinegar", "mustard", "seasoning", "mayonnaise"]),
 "13": ("Foodstuffs for particular nutritional uses", ["infant", "baby food", "protein powder", "supplement", "nutritional"]),
 "14": ("Beverages, excluding dairy", ["juice", "soda", "cola", "carbonated", "energy drink", "tea", "coffee", "drink", "beverage", "squash", "mineral water"]),
 "15": ("Ready-to-eat savouries", ["chips", "crisps", "wafer", "puffed", "roasted nuts", "snack"]),
 "18": ("Indian sweets and snacks", ["mithai", "laddu", "barfi", "halwa", "sev", "bhujia", "namkeen", "gulab jamun", "chakli"]),
}
MEDICINE_WORDS = ["tablet", "capsule", "i.p.", "each tablet", "dosage", "schedule h"]

def guess_category(text):
    t = (text or "").lower()
    scores = {}
    for code, (name, kws) in CATEGORIES.items():
        n = sum(1 for k in kws if re.search(r"\b" + re.escape(k) + r"s?\b", t))
        if n:
            scores[code] = n
    if not scores:
        return None
    top = sorted(scores.items(), key=lambda x: -x[1])
    if len(top) > 1 and top[0][1] == top[1][1]:
        return None
    return top[0][0], CATEGORIES[top[0][0]][0]

def looks_like_medicine(text):
    t = (text or "").lower()
    return any(w in t for w in MEDICINE_WORDS)
