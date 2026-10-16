import re
from pathlib import Path

ROOT = Path(".")
SKIP_DIRS = {"venv", "migrations", "__pycache__", "staticfiles", "media", "ml", ".git", "static"}
SKIP_FILES = {"make_english.py"}

PAIRS = [
    # ---------- accounts / dashboards / login ----------
    ("Yeh account {label} ka nahi hai. Sahi role chuno.", "This account does not belong to {label}. Please choose the correct role."),
    ("Rooms banao, occupancy dekho", "Create rooms and view occupancy"),
    ("Register, bed allot, checkout", "Register, allot beds, check out"),
    ("Invoice banao, payment mark karo", "Generate invoices, mark payments"),
    ("Deposit aur refund", "Deposits and refunds"),
    ("Staff ko assign karo", "Assign to staff"),
    ("Visitor entry-exit record", "Visitor entry and exit records"),
    ("Room change approve karo", "Approve room changes"),
    ("Menu aur meal count", "Menu and meal count"),
    ("Charts aur Excel export", "Charts and Excel export"),
    ("Users aur data manage", "Manage users and data"),
    ("Occupancy dekho", "View occupancy"),
    ("Invoice aur payment", "Invoices and payments"),
    ("Visitor record", "Visitor records"),
    ("Menu dekho", "View menu"),
    ("Invoice aur receipt PDF", "Invoices and receipt PDF"),
    ("Complaint daalo aur track karo", "Submit and track complaints"),
    ("Request aur QR code", "Request and QR code"),
    ("Dusre bed ki request", "Request a different bed"),
    ("Mere Tasks", "My Tasks"),
    ("Assigned kaam aur status", "Assigned work and status"),
    ("Out / In aur visitors", "Out / In and visitors"),
    ("Gate pass scan karo", "Scan gate passes"),
    ("Naya visitor", "New visitor"),
    ("Poora record", "Full record"),
    ("Weekly menu dekho", "View weekly menu"),
    ("Menu Set Karo", "Set Menu"),
    ("Din aur meal ka menu", "Menu by day and meal"),
    ("Kal kitne log khayenge", "How many will eat tomorrow"),
    ("Ratings aur comments", "Ratings and comments"),
    ("Beds bhare", "Beds occupied"),
    ("Rent baaki", "Rent due"),
    ("Khuli complaints", "Open complaints"),
    ("Pending gate pass", "Pending gate passes"),
    ("Active gate pass", "Active gate passes"),
    ("Abhi bahar", "Currently out"),
    ("Nikalne wale", "Waiting to leave"),
    ("Andar visitors", "Visitors inside"),
    ("Namaste,", "Hello,"),
    ("Namaste ", "Hello "),
    ("Apna role chuno aur login karo", "Choose your role and log in"),
    ("Username ya password galat hai.", "Incorrect username or password."),
    ("Role badlo", "Change role"),

    # ---------- rooms ----------
    ("aur {self.object.capacity} beds ban gaye.", "and {self.object.capacity} beds created."),
    ("Room update ho gaya.", "Room updated."),
    ("Room delete ho gaya.", "Room deleted."),
    ("Is room ke beds par tenant allotted hai, delete nahi ho sakta.", "A tenant is allotted to a bed in this room, so it cannot be deleted."),
    ("Kitne beds hain", "Number of beds"),
    ("Abhi koi room nahi hai.", "No rooms yet."),
    ("Iske saare beds bhi delete ho jayenge.", "All its beds will also be deleted."),
    ("Haan, delete karo", "Yes, delete"),
    ("Room {{ object.room_no }} delete karna hai?", "Delete Room {{ object.room_no }}?"),

    # ---------- tenants ----------
    (" register ho gaya.", " registered successfully."),
    ("Bed Allot Karo", "Allot Bed"),
    ("Yeh bed abhi kisi aur ko mil chuka hai.", "This bed has just been allotted to someone else."),
    ("Is tenant ko pehle se bed allotted hai.", "This tenant already has a bed."),
    (" ko {bed} allot ho gaya.", " has been allotted {bed}."),
    (" ka checkout ho gaya, bed free hai.", " has been checked out. The bed is now free."),
    ("Yeh username pehle se hai.", "This username already exists."),
    ("Kaunsa bed chahiye", "Which bed do you want"),
    ("/mahina)", "/month)"),
    ("Aapki ek request pehle se pending hai.", "You already have a pending request."),
    ("Aapko abhi bed allot nahi hua hai.", "You have not been allotted a bed yet."),
    ("Yeh aapka abhi ka hi bed hai.", "This is your current bed."),
    ("Room change request bhej di gayi.", "Room change request submitted."),
    ("Galat action.", "Invalid action."),
    ("Is request par pehle hi decision ho chuka hai.", "A decision has already been made on this request."),
    ("Tenant ka active allotment nahi hai.", "Tenant has no active allotment."),
    ("Yeh bed ab khali nahi hai.", "This bed is no longer vacant."),
    ("Aapki room change request {req.get_status_display()} hui.", "Your room change request was {req.get_status_display()}."),
    ("Naya bed:", "New bed:"),
    (" ko {req.requested_bed} mein shift kar diya.", " has been moved to {req.requested_bed}."),
    ("Abhi koi tenant nahi hai.", "No tenants yet."),
    (">Dekho</a>", ">View</a>"),
    ("Allot nahi hua", "Not allotted"),
    ("Checkout karna hai?", "Do you want to check out?"),
    ("+ Nayi Request", "+ New Request"),
    ("<th>Abhi ka bed</th>", "<th>Current bed</th>"),
    ("<th>Abhi ka</th>", "<th>Current</th>"),
    ("<th>Chahiye</th>", "<th>Requested</th>"),
    ("Abhi koi request nahi hai.", "No requests yet."),
    ("Koi request nahi mili.", "No requests found."),
    ("Request bhejo", "Send request"),

    # ---------- billing ----------
    (" ka rent invoice ban gaya hai.", " rent invoice has been generated."),
    ("Last date:", "Due date:"),
    (" naye invoice bane.", " new invoice(s) created."),
    ("Yeh invoice pehle se paid hai.", "This invoice is already paid."),
    (" paid mark ho gaya.", " marked as paid."),
    (" ka payment mil gaya (", " payment received ("),
    ("Receipt portal se download karo: My Rent.", "You can download the receipt from the portal: My Rent."),
    ("Order match nahi hua.", "Order mismatch."),
    ("Payment verify nahi hua.", "Payment verification failed."),
    ("Galat data.", "Invalid data."),
    ("Payment ho gaya. Receipt download kar sakte ho.", "Payment successful. You can download the receipt."),
    ("Order nahi bana", "Could not create order"),
    ("Verify nahi hua", "Verification failed"),
    ("Yeh computer-generated receipt hai.", "This is a computer-generated receipt."),
    ("ka rent {inv.due_date:%d %b %Y} tak dena hai.", "rent is due by {inv.due_date:%d %b %Y}."),
    ("Late hone par overdue mark hoga.", "It will be marked overdue if paid late."),
    ("Mahine ki 1 tarikh", "First day of the month"),
    ("Warden ko pay karo", "Pay to the warden"),
    ("Abhi koi invoice nahi hai.", "No invoices yet."),
    ("Is mahine ke invoices banao", "Generate this month's invoices"),
    ("Total baaki (Pending + Overdue):", "Total due (Pending + Overdue):"),
    ("Koi invoice nahi mila.", "No invoices found."),
    ("Deposit record ho gaya.", "Deposit recorded."),
    ("Yeh deposit pehle hi refund ho chuka hai.", "This deposit has already been refunded."),
    (" refund mark ho gaya.", " marked as refunded."),
    ("Aapka security deposit refund process ho gaya.", "Your security deposit refund has been processed."),
    ("Amount 0 se zyada hona chahiye.", "Amount must be greater than 0."),
    ("Deduction negative nahi ho sakta.", "Deduction cannot be negative."),
    ("Deduction deposit (Rs. {self.instance.amount}) se zyada nahi ho sakta.", "Deduction cannot be more than the deposit (Rs. {self.instance.amount})."),
    ("Deduction hai to reason likho.", "Please enter a reason for the deduction."),
    ("Deduction (Rs.), damage ya dues ke liye", "Deduction (Rs.), for damage or dues"),
    ("Deduction ka reason", "Deduction reason"),
    ("Abhi hostel ke paas total deposit:", "Total deposit currently held:"),
    ("Pehle checkout karo", "Check out first"),
    ("Abhi koi deposit record nahi hai.", "No deposit records yet."),
    ("Is tenant ka rent baaki hai. Chaho to wo amount deduction mein daal sakte ho.", "This tenant has unpaid rent. You may include that amount in the deduction."),
    ("Refund karo", "Process refund"),
    ("Refund mila:", "Refund received:"),
    ("Checkout ke baad damage kaat ke refund hoga.", "The refund will be processed after checkout, minus any damage deductions."),
    ("Aapka deposit abhi record nahi hua hai.", "Your deposit has not been recorded yet."),

    # ---------- complaints ----------
    ("Electrical (bijli)", "Electrical"),
    ("Plumbing (paani)", "Plumbing"),
    ("Cleaning / Safai", "Cleaning"),
    ("Aapki tenant profile nahi bani hai. Warden se register karwao.", "Your tenant profile has not been created. Please ask the warden to register you."),
    ("Complaint darj ho gayi.", "Complaint submitted."),
    (" ko {staff.username} ko assign kar diya.", " assigned to {staff.username}."),
    ("Resolved complaint assign nahi ho sakti.", "A resolved complaint cannot be assigned."),
    ("Staff select karo.", "Please select a staff member."),
    ("Galat status.", "Invalid status."),
    (" update ho gayi.", " updated."),
    ("Aapki complaint ", "Your complaint "),
    ("resolve ho gayi hai.", "has been resolved."),
    (" resolve ho gayi", " has been resolved"),
    ("Nayi Complaint", "New Complaint"),
    ("Abhi koi complaint nahi hai.", "No complaints yet."),
    ("Koi complaint nahi mili.", "No complaints found."),
    ("Staff chuno", "Select staff"),
    ("Abhi koi task assign nahi hai.", "No tasks assigned yet."),

    # ---------- gate pass / visitors ----------
    ("Bahar hai", "Out"),
    ("Wapas aaya", "Returned"),
    ("Kab nikalna hai", "When are you leaving"),
    ("Kab tak wapas aaoge", "When will you return"),
    ("Wapas aane ka time nikalne ke time se baad ka hona chahiye.", "Return time must be after the departure time."),
    ("Gate pass request bhej di gayi.", "Gate pass request submitted."),
    (" ab {gp.get_status_display()} hai.", " is now {gp.get_status_display()}."),
    (" bahar gaya.", " has gone out."),
    (" LATE wapas aaya.", " returned LATE."),
    (" time par wapas aaya.", " returned on time."),
    ("Visitor ki entry ho gayi.", "Visitor entry recorded."),
    (" ka exit mark ho gaya.", " has exited."),
    ("Galat QR / token.", "Invalid QR / token."),
    ("Yeh pass nahi mila.", "Pass not found."),
    (" BAHAR gaya.", " has gone OUT."),
    (" time par WAPAS aaya.", " has RETURNED on time."),
    ("Yeh pass pehle hi use ho chuka hai.", "This pass has already been used."),
    ("Pass {gp.get_status_display()} hai, scan nahi ho sakta.", "Pass is {gp.get_status_display()} and cannot be scanned."),
    ("Nayi Request", "New Request"),
    ("Abhi koi gate pass nahi hai.", "No gate passes yet."),
    (">Nikalna<", ">Leaving<"),
    (">Wapas (expected)<", ">Expected return<"),
    ("Nikalne wale (Approved passes)", "About to leave (approved passes)"),
    (">Bahar gaya</button>", ">Mark Out</button>"),
    (">Wapas aaya</button>", ">Mark Returned</button>"),
    ("Koi approved pass nahi.", "No approved passes."),
    ("Abhi bahar hain", "Currently out"),
    ("<th>Nikla</th>", "<th>Left at</th>"),
    ("Abhi koi bahar nahi hai.", "Nobody is out right now."),
    ("Abhi andar visitors", "Visitors currently inside"),
    ("Kisse milne", "Meeting"),
    ("Koi visitor andar nahi hai.", "No visitors inside."),
    ("Abhi koi visitor entry nahi hai.", "No visitor entries yet."),
    (">Andar<", ">Inside<"),
    ("Camera se scan", "Scan with camera"),
    ("Ya token manually daalo", "Or enter the token manually"),
    ("Token paste karo", "Paste token"),
    ("Camera nahi chala. Token manually daalo.", "Camera not working. Please enter the token manually."),

    # ---------- mess ----------
    ("Jaise: Roti, Dal, Aloo Gobhi, Chawal", "For example: Roti, Dal, Mixed Veg, Rice"),
    ("Menu save ho gaya.", "Menu saved."),
    ("Aapki tenant profile nahi bani hai.", "Your tenant profile has not been created."),
    ("Galat date.", "Invalid date."),
    ("Galat meal.", "Invalid meal."),
    ("Sirf kal se agle 3 din tak ke meals badal sakte ho.", "You can only change meals from tomorrow for the next 3 days."),
    ("} ka {meal.title()} ON ho gaya.", "} {meal.title()} is now ON."),
    ("} ka {meal.title()} OFF ho gaya.", "} {meal.title()} is now OFF."),
    ("Feedback ke liye shukriya.", "Thank you for your feedback."),
    ("Feedback do", "Give Feedback"),
    ("Menu set karo", "Set Menu"),
    (">Aaj<", ">Today<"),
    ("Default mein saare meals ON hote hain. Jo meal nahi khana, use OFF karo. Aaj ka meal change nahi ho sakta, kal se agle 3 din tak badal sakte ho.",
     "All meals are ON by default. Turn OFF any meal you will not eat. Today's meal cannot be changed; you can change meals from tomorrow for the next 3 days."),
    ("Hostel mein abhi total tenants:", "Total tenants in the hostel right now:"),
    ("</span> log", "</span> people"),
    ("{{ m.off }} ne OFF kiya", "{{ m.off }} turned OFF"),
    ("Abhi koi feedback nahi hai.", "No feedback yet."),

    # ---------- notices / reports / seed ----------
    ("Naya Notice", "New Notice"),
    ("Post karo", "Post"),
    ("Important (upar dikhega, laal border)", "Important (shown at the top with a red border)"),
    ("Notice post ho gaya.", "Notice posted."),
    ("Notice delete ho gaya.", "Notice deleted."),
    ("Delete karna hai?", "Delete this notice?"),
    ("Abhi koi notice nahi hai.", "No notices yet."),
    ("beds bhare", "beds occupied"),
    ("beds khali", "beds vacant"),
    ("complaints khuli", "open complaints"),
    ("Koi defaulter nahi.", "No defaulters."),
    ("Hostel Management demo mein aapka swagat hai.", "Welcome to the Hostel Management demo."),
    (" ke Papa", "'s Father"),
]
PAIRS.sort(key=lambda p: len(p[0]), reverse=True)

LEFTOVER = re.compile(
    r"\b(aur|nahi|hai|hain|karo|dekho|abhi|koi|gaya|gayi|chahiye|daalo|chuno|baaki|"
    r"mahine|tarikh|wapas|bahar|naye|mein|liye|hoga|ka|ki|ko)\b", re.IGNORECASE)

def files():
    for p in ROOT.rglob("*"):
        if p.suffix not in (".py", ".html") or p.name in SKIP_FILES:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p

changed, leftovers = 0, []
for p in files():
    with open(p, encoding="utf-8", newline="") as f:
        text = f.read()
    new = text
    for old, rep in PAIRS:
        new = new.replace(old, rep)
    if new != text:
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(new)
        changed += 1
        print("Updated:", p)
    for n, line in enumerate(new.splitlines(), 1):
        if LEFTOVER.search(line):
            leftovers.append(f"{p}:{n}: {line.strip()[:110]}")

print(f"\nDone. {changed} files updated.")
if leftovers:
    print(f"\nPlease review these {len(leftovers)} lines (may still contain Hinglish):")
    print("\n".join(leftovers))
else:
    print("No Hinglish words found.")