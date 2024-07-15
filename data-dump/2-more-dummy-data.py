import psycopg2
from psycopg2 import Error
import random

def main():
    try:
        connection = psycopg2.connect(user='',
                                        password='',
                                        host='',
                                        port='',
                                        database='')
        cursor = connection.cursor()
    except(Exception, Error) as error:
        print("Error connecting to database", error)
        return

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
            query = """ INSERT INTO Users (username, email, password, location, address, joining_date) VALUES (%s, %s, %s, ll_to_earth(%s, %s), %s, '%s-%s-%sT02:19:32.816610+00:00')"""
            t = (user, email, password, round(x, 6), round(y, 6), pcode, year, month, day)
            cursor.execute(query, t)

    connection.commit()
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
    for i in range(1000):
        x, y = random.uniform(-180,180), random.uniform(-90, 90)
        itemstr = ''
        num_desc = random.randrange(0, 3)
        for i in range(num_desc):
            itemstr = itemstr + ' ' + random.choice(desc)
        itemstr = itemstr + ' ' + random.choice(items)
        query = """ INSERT INTO Listings (seller_id, title, price, location, address, status) VALUES (%s, %s, %s, ll_to_earth(%s, %s), %s, 'AVAILABLE')"""
        t = (1, itemstr, random.randrange(20, 10000), round(x, 6), round(y, 6), random.choice(pcodes))
        cursor.execute(query, t)
    connection.commit()
    cursor.close()
    connection.close()
    return

if __name__ == '__main__':
    main()