# agente_activo.py (Versión Final Corregida)

import requests
import json
import time
from datetime import datetime, timezone

WHATSAPP_MCP_SERVER_URL = "http://whatsapp_python_mcp_server:8002/mcp/"
HOST_APP_CHAT_URL = "http://host_fastapi_app:8000/chat"

# Función para llamar a una herramienta en el servidor MCP y devolver el resultado directamente
def mcp_call_tool(server_url, mcp_protocol_method, params_or_arguments={}):
    """Llama a una herramienta en el servidor y devuelve el resultado directamente."""
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": "active-agent-call",
        "params": {
            "name": mcp_protocol_method,
            "arguments": params_or_arguments
        }
    }
    try:
        response = requests.post(server_url, json=payload, headers=headers)
        response.raise_for_status()
        json_response = response.json()
        # La respuesta ahora es simple: el resultado está directamente en la clave 'result'
        return json_response.get("result", [])
    except Exception as e:
        print(f"Error llamando a la herramienta {mcp_protocol_method}: {e}")
        return []

def procesar_mensaje(mensaje):
   
    chat_jid = mensaje.get('chat_jid')
    if not chat_jid:
        print("AGENTE ACTIVO: Mensaje sin chat_jid, ignorando.")
        return
    
    print(f"AGENTE ACTIVO: Verificando estado para el chat {chat_jid}...")
    estado = mcp_call_tool(
        server_url=WHATSAPP_MCP_SERVER_URL,
        mcp_protocol_method="get_chat_estado",
        params_or_arguments={"chat_jid": chat_jid}
    )
    print(f"AGENTE ACTIVO: El estado del chat es '{estado}'.")

    if estado != "contestar":
        print(f"AGENTE ACTIVO: Ignorando mensaje del chat {chat_jid} por estado '{estado}'.")
        return
    
    
    payload = {
        "texto": mensaje.get('content', ''),
        "telefono_cliente": mensaje.get('sender', '').split('@')[0],
        "nombre_cliente": mensaje.get('chat_name', 'Desconocido')
    }
    if not payload["texto"]:
         print("AGENTE ACTIVO: Mensaje sin contenido de texto, ignorando.")
         return

    try:
        print(f"AGENTE ACTIVO: Enviando mensaje '{payload['texto']}' al cerebro para procesar...")
        response = requests.post(HOST_APP_CHAT_URL, json=payload)
        response.raise_for_status()
        print(f"AGENTE ACTIVO: El cerebro procesó el mensaje. Respuesta: {response.json()}")
    except Exception as e:
        print(f"AGENTE ACTIVO: Error al enviar mensaje al cerebro: {e}")

if __name__ == "__main__":
    print("--- Iniciando Agente Activo ---")
    ultimo_timestamp_revisado = datetime.now(timezone.utc)
    print(f"Escuchando mensajes nuevos a partir de: {ultimo_timestamp_revisado.isoformat()}")

    while True:
        try:
            print("\nAGENTE ACTIVO: Buscando mensajes nuevos...")
           
            mensajes_recientes = mcp_call_tool(
                server_url=WHATSAPP_MCP_SERVER_URL,
                mcp_protocol_method="list_messages",
                params_or_arguments={"limit": 15, "is_from_me": False}
            )
          

            print(f"DEBUG: Respuesta recibida de list_messages: {mensajes_recientes}")

            mensajes_nuevos_sin_contestar = []
            if isinstance(mensajes_recientes, list):
                for msg in mensajes_recientes:
                    timestamp_mensaje = datetime.fromisoformat(msg['timestamp'])
                    if timestamp_mensaje > ultimo_timestamp_revisado and not msg['is_from_me']:
                        mensajes_nuevos_sin_contestar.append(msg)

            if mensajes_nuevos_sin_contestar:
                mensajes_nuevos_sin_contestar.sort(key=lambda m: datetime.fromisoformat(m['timestamp']))

                print(f"AGENTE ACTIVO: ¡{len(mensajes_nuevos_sin_contestar)} mensaje(s) nuevo(s) encontrado(s)!")

                for mensaje in mensajes_nuevos_sin_contestar:
                    procesar_mensaje(mensaje)
                    ultimo_timestamp_revisado = datetime.fromisoformat(mensaje['timestamp'])
            else:
                print("AGENTE ACTIVO: No hay mensajes nuevos.")

            time.sleep(15)

        except KeyboardInterrupt:
            print("--- Deteniendo Agente Activo ---")
            break
        except Exception as e:
            print(f"AGENTE ACTIVO: Ocurrió un error inesperado en el bucle principal: {e}")
            time.sleep(30)