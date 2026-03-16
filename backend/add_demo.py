import sqlite3, bcrypt
conn=sqlite3.connect('dealbot.db')
c=conn.cursor()
hash_pw=bcrypt.hashpw(b'demo123', bcrypt.gensalt()).decode('utf-8')
try:
    c.execute('INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)', ('demo', 'demo@example.com', hash_pw))
    conn.commit()
    print('Demo user created')
except sqlite3.IntegrityError:
    print('Demo user already exists')

