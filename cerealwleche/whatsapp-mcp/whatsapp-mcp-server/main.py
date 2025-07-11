# main.py - Versión Definitiva y Final

from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Dict, Any

# 1. Importamos TODAS las funciones útiles que ya existen desde whatsapp.py
#    Nos aseguramos de no omitir ninguna.
from whatsapp import (
    search_contacts,
    list_messages,
    list_chats,
    get_chat,
    get_direct_chat_by_contact,
    get_contact_chats,
    get_last_interaction,
    get_message_context,
    send_message,
    send_file,
    send_audio_message,
    download_media,
    save_outgoing_message,
    get_chat_estado,
    set_chat_estado
)   

# 2. Creamos nuestro mapa de herramientas.
#    Esto asocia el nombre de una herramienta (texto) con su función de Python real.
tool_map = {
    "search_contacts": search_contacts,
    "list_messages": list_messages,
    "list_chats": list_chats,
    "get_chat": get_chat,
    "get_direct_chat_by_contact": get_direct_chat_by_contact,
    "get_contact_chats": get_contact_chats,
    "get_last_interaction": get_last_interaction,
    "get_message_context": get_message_context,
    "send_message": send_message,
    "send_file": send_file,
    "send_audio_message": send_audio_message,
    "download_media": download_media,
    "save_outgoing_message": save_outgoing_message,
    "get_chat_estado": get_chat_estado,         
    "set_chat_estado": set_chat_estado          
}

# 3. Creamos nuestra aplicación FastAPI estándar.
app = FastAPI(
    title="Standard WhatsApp Tool Server",
    description="Un servidor de herramientas estándar que reemplaza a FastMCP."
)

# 4. Definimos cómo debe ser el cuerpo de la petición que esperamos recibir.
class ToolCallParams(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)

class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    id: str
    params: ToolCallParams

# 5. Creamos el único endpoint que necesita el sistema en la ruta correcta: /mcp/
@app.post("/mcp/")
def dispatch_tool_call(request: JsonRpcRequest = Body(...)):
    """
    Este único endpoint actúa como un despachador.
    Recibe una petición JSON-RPC, extrae el nombre de la herramienta y sus argumentos,
    y ejecuta la función de Python correspondiente.
    """
    
    # Validamos que el método sea el esperado
    if request.method != "tools/call":
        raise HTTPException(status_code=400, detail="Invalid method. Only 'tools/call' is supported.")

    tool_name = request.params.name
    arguments = request.params.arguments

    print(f"TOOL SERVER: Recibida llamada para la herramienta '{tool_name}' con argumentos: {arguments}")

    # Buscamos la función correspondiente en nuestro mapa
    tool_function = tool_map.get(tool_name)

    if not tool_function:
        print(f"TOOL SERVER: Error - Herramienta '{tool_name}' no encontrada.")
        error_payload = {
            "jsonrpc": "2.0",
            "id": request.id,
            "error": {"code": -32601, "message": f"Method not found: Tool '{tool_name}'"}
        }
        return error_payload

    try:
        # Ejecutamos la función encontrada con los argumentos recibidos
        result = tool_function(**arguments)
        
        # Devolvemos la respuesta en el formato JSON-RPC que el cliente espera
        response_payload = {
            "jsonrpc": "2.0",
            "id": request.id,
            "result": result
        }
        return response_payload

    except Exception as e:
        print(f"TOOL SERVER: Error ejecutando la herramienta '{tool_name}': {e}")
        error_payload = {
            "jsonrpc": "2.0",
            "id": request.id,
            "error": {"code": -32000, "message": str(e)}
        }
        return error_payload