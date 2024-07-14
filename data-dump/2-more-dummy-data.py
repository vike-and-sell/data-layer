import psycopg2
from psycopg2 import Error
import random

def main():
    try:
        connection = psycopg2.connect(user='YOUR_DB_USERNAME',
                                        password='YOUR_DB_PASSWORD',
                                        host='YOUR_DB_HOST',
                                        port='YOUR_DB_PORT',
                                        database='YOUR_DB_NAME')
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
            t = (user, email, password, round(x, 6), round(y, 6), pcode, str(year), str(month), str(day))
            cursor.execute(query, t)


    return

if __name__ == '__main__':
    main()