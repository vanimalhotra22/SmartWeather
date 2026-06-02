import os
import sqlite3
from datetime import datetime

# Database path in the same directory as this file
DB_PATH = os.path.join(os.path.dirname(__file__), 'agro.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def db_init():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            google_id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            name TEXT NOT NULL,
            picture TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Crop recommendation history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crop_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            google_id TEXT NOT NULL,
            temperature REAL,
            ph REAL,
            moisture REAL,
            rainfall REAL,
            humidity REAL,
            sunlight REAL,
            irrigation TEXT,
            fertilizer TEXT,
            pesticide REAL,
            duration INTEGER,
            recommended_crop TEXT,
            confidence REAL,
            predicted_yield REAL,
            sowing_date TEXT,
            harvest_date TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (google_id) REFERENCES users (google_id)
        )
    ''')
    
    # 3. Disease detection history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disease_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            google_id TEXT NOT NULL,
            image_path TEXT,
            prediction TEXT,
            description TEXT,
            prevention TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (google_id) REFERENCES users (google_id)
        )
    ''')
    
    # 4. Chat history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            google_id TEXT NOT NULL,
            message TEXT,
            reply TEXT,
            language TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (google_id) REFERENCES users (google_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def db_save_user(google_id, email, name, picture):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (google_id, email, name, picture)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(google_id) DO UPDATE SET
            email=excluded.email,
            name=excluded.name,
            picture=excluded.picture
    ''', (google_id, email, name, picture))
    conn.commit()
    conn.close()

def db_save_crop_recommendation(google_id, temperature, ph, moisture, rainfall, humidity, sunlight,
                               irrigation, fertilizer, pesticide, duration, recommended_crop,
                               confidence, predicted_yield, sowing_date, harvest_date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO crop_history (
            google_id, temperature, ph, moisture, rainfall, humidity, sunlight,
            irrigation, fertilizer, pesticide, duration, recommended_crop,
            confidence, predicted_yield, sowing_date, harvest_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (google_id, temperature, ph, moisture, rainfall, humidity, sunlight,
          irrigation, fertilizer, pesticide, duration, recommended_crop,
          confidence, predicted_yield, sowing_date, harvest_date))
    conn.commit()
    conn.close()

def db_get_crop_history(google_id, limit=20):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM crop_history
        WHERE google_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (google_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def db_save_disease_detection(google_id, image_path, prediction, description, prevention):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO disease_history (google_id, image_path, prediction, description, prevention)
        VALUES (?, ?, ?, ?, ?)
    ''', (google_id, image_path, prediction, description, prevention))
    conn.commit()
    conn.close()

def db_get_disease_history(google_id, limit=20):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM disease_history
        WHERE google_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (google_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def db_save_chat(google_id, message, reply, language):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chat_history (google_id, message, reply, language)
        VALUES (?, ?, ?, ?)
    ''', (google_id, message, reply, language))
    conn.commit()
    conn.close()

def db_get_chat_history(google_id, limit=20):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM chat_history
        WHERE google_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (google_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def db_get_stats(google_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total recommendations
    cursor.execute('SELECT COUNT(*) FROM crop_history WHERE google_id = ?', (google_id,))
    total_crops = cursor.fetchone()[0]
    
    # Total diseases checked
    cursor.execute('SELECT COUNT(*) FROM disease_history WHERE google_id = ?', (google_id,))
    total_diseases = cursor.fetchone()[0]
    
    # Total chatbot queries
    cursor.execute('SELECT COUNT(*) FROM chat_history WHERE google_id = ?', (google_id,))
    total_chats = cursor.fetchone()[0]
    
    # Get distribution of recommended crops
    cursor.execute('''
        SELECT recommended_crop, COUNT(*) as count 
        FROM crop_history 
        WHERE google_id = ? 
        GROUP BY recommended_crop
        ORDER BY count DESC
        LIMIT 5
    ''', (google_id,))
    crop_dist = [dict(row) for row in cursor.fetchall()]
    
    # Get ratio of healthy vs diseased checks
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN LOWER(prediction) = 'healthy' THEN 1 ELSE 0 END) as healthy_count,
            SUM(CASE WHEN LOWER(prediction) != 'healthy' THEN 1 ELSE 0 END) as diseased_count
        FROM disease_history 
        WHERE google_id = ?
    ''', (google_id,))
    row = cursor.fetchone()
    disease_stats = {
        "healthy": row['healthy_count'] or 0,
        "diseased": row['diseased_count'] or 0
    }
    
    conn.close()
    return {
        "total_recommendations": total_crops,
        "total_diseases_checked": total_diseases,
        "total_chats": total_chats,
        "crop_distribution": crop_dist,
        "disease_stats": disease_stats
    }
