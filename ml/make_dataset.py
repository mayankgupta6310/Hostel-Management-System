import random
import pandas as pd

random.seed(42)

DATA = {
    "ELECTRICAL": (
        ["fan", "light", "tube light", "socket", "switch", "AC", "charging point", "bulb"],
        ["is not working", "stopped working", "is making noise", "is sparking",
         "is flickering", "is broken", "is not turning on"],
    ),
    "PLUMBING": (
        ["tap", "washbasin", "toilet", "shower", "water pipe", "flush", "geyser", "water cooler"],
        ["is leaking", "is blocked", "has no water", "is broken", "is overflowing", "has low pressure"],
    ),
    "FURNITURE": (
        ["bed", "chair", "table", "cupboard", "study table", "mattress", "window", "door lock"],
        ["is broken", "is damaged", "is shaking", "is not closing", "needs repair", "has a loose leg"],
    ),
    "CLEANING": (
        ["room", "bathroom", "corridor", "washroom", "floor", "dustbin", "balcony"],
        ["is very dirty", "has not been cleaned", "smells bad", "needs cleaning", "has garbage"],
    ),
    "INTERNET": (
        ["WiFi", "internet", "router", "network"],
        ["is very slow", "is not connecting", "keeps disconnecting", "is not working", "has no signal"],
    ),
}
PREFIX = ["", "Please fix: ", "Urgent! ", "Since yesterday, ", "Kindly check, "]
OTHER = [
    "I lost my room key", "There is loud noise from the next room at night",
    "Mosquitoes in my room", "Security issue near the main gate",
    "Parking problem in front of the hostel", "The food quality is bad",
    "I need a new roommate", "Someone is using my things",
    "Please update my guardian phone number", "Visitors are not allowed late at night",
    "Laundry service is delayed", "Common room timing should be extended",
]

rows = []
for cat, (subjects, problems) in DATA.items():
    seen = set()
    while len(seen) < 60:
        text = f"{random.choice(PREFIX)}The {random.choice(subjects)} in my room {random.choice(problems)}"
        seen.add(text)
    rows += [(t, cat) for t in seen]

other = set()
while len(other) < 60:
    other.add(f"{random.choice(PREFIX)}{random.choice(OTHER)}")
rows += [(t, "OTHER") for t in other]

random.shuffle(rows)
pd.DataFrame(rows, columns=["text", "category"]).to_csv("ml/complaints.csv", index=False)
print("Dataset created:", len(rows), "rows")