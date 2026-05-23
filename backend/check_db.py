import sqlite3

conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()

print("=== USERS WITH FACE REGISTERED ===")
cursor.execute('SELECT username, is_face_registered FROM users WHERE user_type="student"')
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]}")

print("")
print("=== STUDENTS WITH CNN_EMBEDDING ===")
cursor.execute("""
    SELECT u.username, length(s.cnn_embedding) 
    FROM student_profiles s 
    JOIN users u ON s.user_id=u.id 
    WHERE s.cnn_embedding IS NOT NULL 
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"{row[0]}: embedding length = {row[1]} chars")

conn.close()
