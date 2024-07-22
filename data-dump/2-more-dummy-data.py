import random

def main():
    fnames = ['mary', 'james', 'michael', 'william', 'george', 'thomas', 'susan', 'olivia', 'elizabeth', 'lisa']
    lnames = ['smith', 'brown', 'miller', 'johnson', 'garcia', 'li', 'singh', 'anderson', 'young', 'williams']
    pcodes = ['V9A', 'V9B', 'V9C', 'V9D', 'V9E', 'V8M', 'V8N', 'V8O', 'V8P', 'V8R', 'V8S', 'V8T', 'V8U', 'V8V', 'V8W', 'V8X', 'V8Y', 'V8Z']
    for fname in fnames:
        for lname in lnames:
            user = fname + '_' + lname
            email = user + '@uvic.ca'
            password = str(hex(random.getrandbits(256)))
            x, y = random.uniform(-180,180), random.uniform(-90, 90)
            pcode = random.choice(pcodes)
            year = random.randrange(1970, 2024)
            month = random.randrange(1, 12)
            day = random.randrange(1, 28)
            query = f"('{user}', '{email}', '{password[2:]}', ll_to_earth({round(x, 6)}, {round(y,6)}), '{pcode}', '{year}-{month}-{day}T02:19:32.816610+00:00'),"
            #USERS
            #print(query)

    desc = [
    "red",
    "lightweight",
    "fast",
    "comfortable",
    "educational",
    "ceramic",
    "touchscreen",
    "ergonomic",
    "durable",
    "wireless",
    "mechanical",
    "optical",
    "high-resolution",
    "lined",
    "insulated",
    "portable",
    "ballpoint",
    "breathable",
    "adjustable",
    "multifunction"
    ]
    items = [
    "apple",
    "laptop",
    "car",
    "bicycle",
    "book",
    "coffee mug",
    "smartphone",
    "desk chair",
    "backpack",
    "headphones",
    "keyboard",
    "mouse",
    "monitor",
    "notebook",
    "water bottle",
    "tablet",
    "pen",
    "sneakers",
    "lamp",
    "printer" 
    ]
    for i in range(500):
        x, y = random.uniform(-180,180), random.uniform(-90, 90)
        itemstr = ''
        num_desc = random.randrange(0, 3)
        for i in range(num_desc):
            itemstr = itemstr +  random.choice(desc) + ' '
        itemstr = itemstr + random.choice(items)
        query = f"({random.randrange(1, 100)}, '{itemstr.title()}', {random.randrange(20, 10000)}, ll_to_earth({round(x, 6)}, {round(y, 6)}), '{random.choice(pcodes)}', 'AVAILABLE'),"
        #LISTINGS
        #print(query)

    for i in range(100):
        year = random.randrange(1970, 2024)
        month = random.randrange(1, 12)
        day = random.randrange(1, 28)
        search = ''
        num_desc = random.randrange(0, 3)
        for i in range(num_desc):
            search = search + random.choice(desc) + " "
        search = search + random.choice(items)
        query = f"({random.randrange(1, 100)}, '{search}', '{year}-{month}-{day}'),"
        #SEARCHES
        #print(query.lstrip().title())

    messages = [
    "Can you tell me more about the condition of this?",
    "Is the price flexible?",
    "Do you have more pics?",
    "Is there a warranty?",
    "Does it work okay?",
    "What is your return policy?",
    "Any scratches or damage?",
    "Can I pick this up locally?",
    "Is this the final price, or are there extra fees?",
    "Is the original packaging included?",
    "Any accessories with it?",
    "What is the exact model number?",
    "Is this authentic?",
    "Do you take lower offers?",
    "Can I see this in person before buying?",
    "How old is this item?",
    "Why are you selling it?",
    "Has it been repaired before?",
    "Any issues I should know about?",
    "Is there a user manual included?",
    "Does it come from a smoke-free home?",
    "Is it pet-friendly?",
    "Has it been in storage long?"]

    for i in range(100):
        year = random.randrange(1970, 2024)
        month = random.randrange(1, 12)
        day = random.randrange(1, 28)
        buyer = random.randrange(1, 100)
        seller = random.randrange(1, 100)
        listing =random.randrange(1, 1000)
        message = random.choice(messages)
        query = f"({buyer}, {seller}, {listing}),"
        query2 = f"({random.randrange(1, 100)}, {random.choice([buyer, seller])}, '{message}', '{year}-{month}-{day}T02:19:32.816610+00:00'),"
        #CHATS & MESSAGES
        #print(query)
        #print(query2)

    for i in range(100):
        year = random.randrange(1970, 2024)
        month = random.randrange(1, 12)
        day = random.randrange(1, 28)
        query = f"({random.randrange(1, 1000)}, {random.randrange(1, 100)}, {random.randrange(1, 6)}, '{year}-{month}-{day}T02:19:32.816610+00:00'),"
        #RATINGS
        #print(query)


    reviews = [
        "Great condition, exactly as described!",
        "Item arrived on time and well-packaged.",
        "Really happy with this purchase, thanks!",
        "Product works perfectly, no issues at all.",
        "Seller was very responsive and helpful.",
        "Good value for the money.",
        "Exceeded my expectations!",
        "Would definitely buy from this seller again.",
        "Exactly what I was looking for!",
        "Item was just as pictured.",
        "Highly recommend this seller.",
        "Quality is top-notch.",
        "Fast shipping and great service.",
        "Five stars all the way!",
        "Not as described, a bit disappointed.",
        "Item arrived late but in good condition.",
        "Packaging could have been better.",
        "The product has some minor scratches.",
        "Item did not work as expected.",
        "Good communication from seller.",
        "Overall, a decent purchase.",
        "Would have preferred better packaging.",
        "Item is okay, but not great.",
        "Had some issues, but seller resolved them quickly."
    ]

    for i in range(100):
        year = random.randrange(1970, 2024)
        month = random.randrange(1, 12)
        day = random.randrange(1, 28)
        review = random.choice(reviews)
        query = f"({random.randrange(1, 1000)}, {random.randrange(1, 100)}, '{review}', '{year}-{month}-{day}T02:19:32.816610+00:00'),"
        #REVIEWS
        #print(query)

    for i in range(100):
        year = random.randrange(1970, 2024)
        month = random.randrange(1, 12)
        day = random.randrange(1, 28)
        query = f"({random.randrange(1, 1000)}, {random.randrange(1, 100)}, '{year}-{month}-{day}T02:19:32.816610+00:00'),"
        #SALES
        print(query)

    return

if __name__ == '__main__':
    main()