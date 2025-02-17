from fastapi import FastAPI, Request, Query
import json
import sqlite3

app = FastAPI()

VERIFY_TOKEN = "7b5a67574d8b1d77d2803b24946950f0"  

@app.get("/")
async def root():
    return {"message": "Hello Clancy"}
    
# 🔹 Função para iniciar o banco de dados    
def init_db():
    conn = sqlite3.connect("whatsapp.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            remetente TEXT,
            wa_id TEXT,
            phone_number_id TEXT,
            message_id TEXT,
            mensagem TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            mensagem_tipo TEXT
        )
    """)
    conn.commit()
    conn.close()

# 🔹 Verifica a conexão com o WhatsApp API
@app.get("/webhook/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge")
):
    """Verifica a conexão com o WhatsApp API (Webhook Verification)."""
    if hub_mode == "subscribe" and hub_token == VERIFY_TOKEN:
        return int(hub_challenge)  # Retorna o challenge para confirmar a verificação
    return {"error": "Invalid token"}

# 🔹 Recebe e processa mensagens do WhatsApp
@app.post("/webhook/whatsapp")
async def receive_whatsapp_message(request: Request):
    data = await request.json()
    print(json.dumps(data, indent=2))  # Debug, pode remover depois

    if "entry" in data:
        for entry in data["entry"]:
            for change in entry["changes"]:
                if "messages" in change["value"]:
                    for message in change["value"]["messages"]:
                        # Extrair dados relevantes
                        sender = message["from"]  # Número do remetente
                        text = message.get("text", {}).get("body", "Sem texto")
                        message_id = message["id"]
                        message_type = message["type"]
                        timestamp = message["timestamp"]
                        metadata = change["value"].get("metadata", {})
                        phone_number_id = metadata.get("phone_number_id", "Desconhecido")
                        wa_id = None
                        if "contacts" in change["value"]:
                            wa_id = change["value"]["contacts"][0].get("wa_id", "Desconhecido")

                        # 🔹 Salvando a mensagem no banco de dados
                        conn = sqlite3.connect("whatsapp.db")
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO historico (remetente, wa_id, phone_number_id, message_id, mensagem, timestamp, mensagem_tipo)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (sender, wa_id, phone_number_id, message_id, text, timestamp, message_type))
                        conn.commit()
                        conn.close()

                        print(f"📩 Mensagem salva de {sender}: {text} - ID: {message_id}")

    return {"status": "received"}


# 🔹 Retorna o histórico de mensagens
@app.get("/historico")
def get_historico():
    try:
        with sqlite3.connect("whatsapp.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM historico ORDER BY timestamp ASC")
            historico = cursor.fetchall()

        # 🔹 Organiza o histórico no formato JSON
        historico_formatado = [
            {
                "id": msg[0],
                "remetente": msg[1],
                "wa_id": msg[2],
                "phone_number_id": msg[3],
                "message_id": msg[4],
                "mensagem": msg[5],
                "timestamp": msg[6],
                "mensagem_tipo": msg[7]
            }
            for msg in historico
        ]

        return {"conversas": historico_formatado}
    except sqlite3.Error as e:
        return {"error": f"Erro ao acessar o banco de dados: {str(e)}"}

# 🔹 Inicializa o banco ao rodar a API
init_db()

