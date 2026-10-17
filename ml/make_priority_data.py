import itertools
import random

import pandas as pd

random.seed(7)

HIGH = [
    "There is a short circuit in my room",
    "Sparks are coming from the switch board",
    "I can smell burning from the socket",
    "There is a gas smell near the kitchen",
    "Water is flooding my room",
    "The bathroom ceiling is about to fall",
    "The main door lock is broken and the hostel is unsafe at night",
    "Someone broke into my room and my laptop was stolen",
    "I got an electric shock from the geyser",
    "There is smoke coming from the AC",
    "The staircase railing has collapsed",
    "A student is injured and needs help",
]
MEDIUM_SUBJECTS = ["fan", "tube light", "tap", "washbasin", "AC", "cupboard", "chair", "study table",
                   "window", "door", "flush", "water cooler", "bed", "WiFi"]
MEDIUM_PROBLEMS = ["is not working", "is leaking", "is broken", "is making noise",
                   "needs repair", "is very slow", "is not closing properly"]
LOW = [
    "Please repaint the wall of my room", "The curtain is missing in my room",
    "I need an extra shelf in my room", "The corridor needs cleaning",
    "Please replace my old mattress cover", "The notice board is empty",
    "Suggestion: please add a water cooler on the second floor", "The paint is peeling on the balcony",
    "I need a new dustbin", "Please clean the common room when possible",
    "The mirror in the washroom has a small crack", "Please add more hooks behind the door",
]
PREFIX = ["", "Please fix: ", "Kindly check, ", "Since yesterday, ", "Hello, "]
HIGH_SUFFIX = ["", " Please come immediately.", " It is dangerous."]
LOW_SUFFIX = ["", " No hurry.", " Not urgent."]


def sample(pool, n):
    random.shuffle(pool)
    return pool[:n]


high = sample([f"{p}{h}.{s}" for p, h, s in itertools.product(PREFIX, HIGH, HIGH_SUFFIX)], 100)
medium = sample([f"{p}The {s} in my room {x}." for p, s, x in
                 itertools.product(PREFIX, MEDIUM_SUBJECTS, MEDIUM_PROBLEMS)], 100)
low = sample([f"{p}{l}.{s}" for p, l, s in itertools.product(PREFIX, LOW, LOW_SUFFIX)], 100)

rows = [(t, "HIGH") for t in high] + [(t, "MEDIUM") for t in medium] + [(t, "LOW") for t in low]
random.shuffle(rows)
pd.DataFrame(rows, columns=["text", "priority"]).to_csv("ml/priority.csv", index=False)
print("Dataset created:", len(rows), "rows")