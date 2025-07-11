# init_whatsapp_db.py (versión con migración de estado)
import sqlite3
import os

DB_PATH = "/data/messages.db"

def initialize_database():
    print(f"Inicializando la base de datos en: {DB_PATH}")
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print("Conexión a la base de datos exitosa.")

        # Crear la tabla 'chats' si no existe (sin cambios)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            jid TEXT PRIMARY KEY,
            name TEXT,
            last_message_time TIMESTAMP
        )
        """)
        print("Tabla 'chats' verificada/creada.")

        # --- LÓGICA NUEVA PARA AÑADIR LA COLUMNA DE ESTADO ---
        try:
            cursor.execute("ALTER TABLE chats ADD COLUMN estado_respuesta TEXT DEFAULT 'contestar'")
            print("Columna 'estado_respuesta' añadida a la tabla 'chats'.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("La columna 'estado_respuesta' ya existe. No se realizan cambios.")
            else:
                raise e
        # --- FIN DE LA LÓGICA NUEVA ---

        # Crear la tabla 'messages' si no existe (sin cambios)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            chat_jid TEXT,
            sender TEXT,
            content TEXT,
            timestamp TIMESTAMP,
            is_from_me BOOLEAN,
            FOREIGN KEY (chat_jid) REFERENCES chats (jid)
        )
        """)
        print("Tabla 'messages' verificada/creada.")

        conn.commit()
        print("Base de datos inicializada correctamente.")

    except sqlite3.Error as e:
        print(f"Error de base de datos durante la inicialización: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    initialize_database()