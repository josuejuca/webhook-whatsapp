from fastapi import FastAPI, Request, Query
import json
import sqlite3

app = FastAPI()

VERIFY_TOKEN = "7b5a67574d8b1d77d2803b24946950f0"  

# 🔹 Função para iniciar o banco de dados
def init_db():
    conn = sqlite3.connect("whatsapp.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            remetente TEXT,
            mensagem TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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
                        sender = message["from"]  # Número do remetente
                        text = message.get("text", {}).get("body", "Sem texto")

                        # 🔹 Salvando a mensagem no banco de dados
                        conn = sqlite3.connect("whatsapp.db")
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO historico (remetente, mensagem) VALUES (?, ?)", (sender, text))
                        conn.commit()
                        conn.close()

                        print(f"📩 Mensagem salva de {sender}: {text}")

    return {"status": "received"}

# 🔹 Retorna o histórico de mensagens
@app.get("/historico")
def get_historico():
    conn = sqlite3.connect("whatsapp.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM historico ORDER BY timestamp ASC")
    historico = cursor.fetchall()
    conn.close()

    # 🔹 Organiza o histórico no formato JSON
    historico_formatado = [
        {"id": msg[0], "remetente": msg[1], "mensagem": msg[2], "timestamp": msg[3]}
        for msg in historico
    ]

    return {"conversas": historico_formatado}

# 🔹 Inicializa o banco ao rodar a API
init_db()