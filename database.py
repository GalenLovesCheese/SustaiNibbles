import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()
PASS = os.getenv('PASSWORD')

mydb = mysql.connector.connect(
    host="localhost",
    user="user",
    password = PASS,
    database = "table2"#"sustainibbles"
)

mycursor = mydb.cursor()
mycursor.execute("CREATE DATABASE IF NOT EXISTS table2")
mycursor.execute("CREATE TABLE IF NOT EXISTS Users (User VARCHAR(255), Type VARCHAR(255) CHECK(Type = 'Individual' OR Type = 'Business'))")
mycursor.execute("CREATE TABLE IF NOT EXISTS Announcements (Location VARCHAR(255), Message VARCHAR(255), PAX int)")
mycursor.execute("INSERT INTO Users(User, Type) VALUES('Ben', 'Individual'),('Thomas', 'Individual'),('Margaret', 'Individual'),('Dumping Donuts', 'Business'), ('Ivy Cafe','Business'), ('1793678228', 'Business')")
mycursor.execute("INSERT INTO Announcements(Location, Message, PAX) VALUES('Bukit Panjang', 'Extra rice left over at store, up to 5 people can  take', 5), ('King Albert Park', 'Extra prata remaining', 2), ('Choa Chu Kang', 'Extra chicken remaining', 3)")
