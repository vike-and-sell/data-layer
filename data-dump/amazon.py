from datasets import load_dataset
import random
import psycopg2

dataset = load_dataset("McAuley-Lab/Amazon-Reviews-2023", "raw_meta_Sports_and_Outdoors", split="full", trust_remote_code=True)
pcodes = ['V9A', 'V9B', 'V9C', 'V9D', 'V9E', 'V8M', 'V8N', 'V8O', 'V8P', 'V8R', 'V8S', 'V8T', 'V8U', 'V8V', 'V8W', 'V8X', 'V8Y', 'V8Z']


with open('data_dump.csv', 'w', newline='', encoding="utf-8") as file:
    field = ["seller_id", "title", "price", "location", "address", "status"]
    file.write(','.join(field)+'\n')

    for i in range(24000):

        conn = psycopg2.connect(
            dbname="vikeandsell",
            user="jerry",
            password="password123",
            host="localhost",
            port=5432
        )

        # Create a cursor object
        cur = conn.cursor()

        # Coordinates
        y, x = random.uniform(-123.3, -123.45), random.uniform(48.4, 48.51)

        # Execute the ll_to_earth function
        cur.execute("SELECT ll_to_earth(%s, %s)", (x, y))

        # Fetch the result
        location = cur.fetchone()

        # Close the cursor and connection
        cur.close()
        conn.close()

        title = dataset[i+1000]["title"]
        price = dataset[i+1000]["price"]
        if price.__eq__('None'):
            price = random.randrange(10, 200)
        seller_id = random.randrange(1, 1000)
        addr = random.choice(pcodes)
        status = 'AVAILABLE'
        row = [str(seller_id), title, str(price), location, addr, status]
        file.write(f"{seller_id},{title[:100].replace(",", "").replace("\"", "")},{price},\"{location[0]}\",{addr},{status}\n")