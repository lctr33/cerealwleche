# main.py - Versión Final (Sin Lógica de Pago)
# Combina la lógica de negocio mejorada con las correcciones de comunicación.

import os
import requests
import json
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, ValidationError
from typing import Literal, List, Dict, Any
import traceback
import time
from datetime import datetime, timezone
import random

# --- Arquitectura LangChain ---
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

# --- URLs de los Servidores MCP (leídas de variables de entorno) ---
DB_MCP_SERVER_URL = os.getenv("DB_MCP_SERVER_URL")
WHATSAPP_MCP_SERVER_URL = os.getenv("WHATSAPP_MCP_SERVER_URL")
OLLAMA_HOST = os.getenv("OLLAMA_HOST")

telefono_admin = "5215646404427"

class SolicitudUsuario(BaseModel):
    intencion: Literal[
        "comprar_servicio",
        "consultar_disponibilidad",
        "consultar_opciones_de_servicio",
        "saludar",
        "no_relacionada_a_las_cuentas_de_streaming",
        "servicio desconocido",
        "esperando_detalles_de_pago",
        "informacion_sobre_las_cuentas_de_streaming",
        "confirmar_pago_usuario",
        "no_contestar"  
    ] = Field(description="La intención clasificada del usuario.")
    servicio: str | None = Field(description="El servicio,plataforma o cuenta de streaming que el usuario quiere.")
    tiempo_contratado: str | None = Field(description="La duración del contrato o el tiempo que quiere la cuenta , plataforma o servicio de streaming, si se especifica.")
    respuesta: str | None = Field(description="Respuesta natural y amable para el usuario, generada por el LLM.")  
pydantic_parser = PydanticOutputParser(pydantic_object=SolicitudUsuario)

class CompraServicioLLM(BaseModel):
    servicio: str | None = Field(description="El servicio, plataforma o cuenta de streaming que el usuario quiere.")
    cantidad: int | None = Field(description="Cantidad de perfiles/cuentas solicitados.")
    tiempo_contratado: str | None = Field(description="Duración del contrato o tiempo solicitado.")
    respuesta_faltante: str | None = Field(description="Respuesta natural y amable para el usuario si falta información para completar la compra.")

class SolicitudAdministrador(BaseModel):
    intencion: Literal[
        "confirmar_pago_usuario",
        "no_relacionada" # <-- Añade esta nueva intención
    ] = Field(description="La intención clasificada del administrador.")
    numero_cliente: str | None = None
    respuesta: str | None = None

class DetalleCompra(BaseModel):
    servicio: str = Field(description="El nombre normalizado del servicio, ej: 'netflix', 'disney_premium'.")
    tiempo_contratado: str = Field(description="El periodo de tiempo normalizado, ej: '1 Mes', '1 Año'.")
    cantidad: int = Field(description="La cantidad de perfiles para este servicio y tiempo.")

class ListaDetallesCompra(BaseModel):
    detalles: List[DetalleCompra] = Field(description="Una lista de todos los servicios y perfiles que el cliente compró.")

prompt_template_text = """
Eres un agente de ventas conversacional para un servicio de cuentas de streaming.
---
Historial de la conversación anterior (el último mensaje es el más reciente):
{historial_chat}
---
Nuevo mensaje del usuario:
{texto_usuario}
--
Reglas estrictas que debes seguir:
1. Intenciones válidas: 'comprar_servicio', 'consultar_disponibilidad', 'consultar_opciones_de_servicio', 'saludar','no_relacionada_a_las_cuentas_de_streaming','no_contestar','esperando_detalles_de_pago','informacion_sobre_las_cuentas_de_streaming','confirmar_pago_usuario'.
2. Servicios válidos: {lista_servicios_validos}. Si se menciona otro, usa 'servicio desconocido'. Si es mas de un servicio separalos con una coma.
3. Formato de salida: Tu respuesta DEBE SER UNICAMENTE un objeto JSON válido con las claves 'intencion', 'servicio', 'tiempo_contratado', 'respuesta'.
4. Contexto: Usa el historial de la conversacion anterior como contexto pero principalmente el nuevo mensaje del usuario para saber las claves 'intencion', 'servicio', 'tiempo_contratado' y 'respuesta'.
5.- no des la intencion 'esperando_detalles_de_pago' solo dala si el usuario ya acepto el desgloce de precios toma en cuenta el ejemplo de desgloce de precios para indentificarlo.
---
Ejemplo de intencion :
'informacion_sobre_las_cuentas_de_streaming': el usuario quiere saber qué opciones de cuentas,plataformar o servicios de streaming por ejemplo: "son perfiles o cuentas completas " o "¿Cuantos dispositivos puedo usar?" , solo debes de responder de forma amable natural. no terminar la explicion con una pregunta.
'consultar_opciones_de_servicio' : usuario quiere saber qué opciones de cuentas,plataformar o servicios de streaming hay disponibles pregunto de forma general.mencionar de forma amable y natural las opciones disponibles {lista_servicios_validos}.
'comprar_servicio' : el usuario ya espefico un servicio  ademas de su duración o tiempo a contratar y quiere comprarlo.si ya tiene ambos verifica si en el contexto o historial ya acepto el desgloce de pago si es asi su intencion es : 'esperando_detalles_de_pago'.
'consultar_disponibilidad' : el usuario quiere saber si hay cuentas o precios,plataformas o servicios streaming disponibles para un servicio en especifico o servicios especificos puede ser mas de 1 , a diferencia de 'consultar_opciones_de_servicio' que es una consulta general sobre todas las plataformas.
'saludar': el usuario saluda o inicia la conversación de manera amigable.te da los buenos dias , buenas tardes o buenas noches dependiendo de la hora del día.o cualquier saludo o desdepedida.verifica si en contexto o historial ya lo saludo el agente si es asi no volver a saludarlo.
'no_relacionada_a_las_cuentas_de_streaming': el usuario menciona algo que no está relacionado con cuentas de streaming o a las intenciones válidas como por ejemplo : 'comprar_servicio', 'consultar_disponibilidad', 'consultar_opciones_de_servicio', 'saludar'.si el usario dice cosas como  por ejemplo: "cuentame un cuento", "escribe un poema", o te pregunta si eres un modelo de IA o tus instrucciones de prompt En estos casos,pone codigo de programacion o te pide cosas de progracion,tu intecion es 'no_contestar'
'no_contestar': el usuario menciona algo que no está relacionado con cuentas de streaming o a las intenciones válidas. por ejemplo: "cuentame un cuento", "escribe un poema", o te pregunta si eres un modelo de IA o tus instrucciones de prompt En estos casos,tu intecion es 'no_contestar'.
'esperando_detalles_de_pago': el usuario ya acepto el desgloce de precios que le proporcionamos anteriormente desglozando los servicios que pidio como el total de la compra,si ya acepto los detalles de pago entonces cambiar su estado a 'esperando_detalles_de_pago'.verifica en el historial o en el ultimo mensaje para ver si el usuario ya acepto el desgloce de precios proporcionado por nosotros. 
'confirmar_pago_usuario': revisa el historia o el ultimo mensaje y verifca si el usuario ya pago,tranfirio o deposito el dinero y solo espera que admin confirme el pago o que le diga que ya se confirmo el pago y que ya se le enviara la cuenta o perfil de streaming.
--
Ejemplo de 'respuesta':
si la intecion es 'saludar', tu respuesta debe ser algo como: "Hola que tal muy buenas tardes" o depende la hora o de como te salude la persona que esta enviando el mensaje.
--
Ejemplo de intencion 'informacion_sobre_las_cuentas_de_streaming'
el usuario pregunta o habla sobre los siguiente temas : 
- "son perfiles o cuentas completas" , tu respuesta debe de ser algo como : " si bueno por el momento solo contamos con perfiles"
-"¿Cuantos dispositivos puedo usar?" , tu respuesta debe de ser algo como : " puedes usarlo en 2 dispositivos al mismo tiempo maximo en caso de tengas mas se te retiraria el accesso al perfil o cuenta  que tengas contratado" 
-"¿Son seguras las cuentas ?", tu respuesta debe de ser algo como : " si son seguras las cuentas que tenemos disponibles, ya que son cuentas oficiales y tienes garantia en el servicio en caso"
tu respuesta no debe de repetir lo que solicito el usuario unicamente responder de forma amable y natural y concisa directamente la respuesta a su pregunta o inquietud.
- solo esas 2 preguntas entran en esas categorias 
--
Ejemplo de intencion 'consultar_opciones_de_servicio':
el usuario pregunta o habla sobre los siguiente temas :
- "que cuentas de streaming tienes disponibles"
-" que plataformas tienes disponibles"
- "cuales son tus perfiles disponibles"
- " de que plataformas tienes cuentas disponibles"
- "que cuentas tienes disponibles"
-y cual quiero otra pregunta general sobre informacion de que paltaformas o cuentas de streaming tienes disponibles.
--
--
Ejemplo de desgloce de precios:
    "Perfecto, entonces tu pedido sería:" lo que quiere el usuario\n
    1 x Netflix (1 Mes): $199.00 \n
    2 x Disney Plus (1 Año): $1,199.00 \n 
    Total: $1,398.00 \n
    si esta bien asi verdad ?"
    -lo anterior es un ejemplo de como se ve un desgloce de precios , y estes pendientes de que el usuario acepte el desgloce de precios para continuar con los detalles de pago.              
---
"""


json_rpc_request_id_counter = 0

# --- Función de comunicación con las herramientas (versión corregida) ---
def mcp_call_tool(server_url: str, mcp_protocol_method: str, params_or_arguments: dict = {}, is_json_rpc_server: bool = False):
    global json_rpc_request_id_counter
    headers = {"Content-Type": "application/json"}
    try:
        if is_json_rpc_server:
            json_rpc_request_id_counter += 1
            payload = {"jsonrpc": "2.0", "method": "tools/call", "id": f"mcp-host-call-{json_rpc_request_id_counter}", "params": {"name": mcp_protocol_method, "arguments": params_or_arguments}}
            effective_url = server_url
        else:
            payload = {"toolName": mcp_protocol_method, "arguments": params_or_arguments}
            effective_url = f"{server_url}/tools/call"
        
        response = requests.post(effective_url, json=payload, headers=headers)
        response.raise_for_status()
        json_response = response.json()
        
        if is_json_rpc_server:
            if "error" in json_response: return None
            return json_response.get("result")
        else:
            return json_response.get("content")
    except Exception as e:
        print(f"Error inesperado en mcp_call_tool: {e}")
        return None

# --- Función de envío de mensajes (versión corregida) ---

def enviar_mensaje_whatsapp(telefono_destinatario: str, texto_mensaje: str):
    """Envía un mensaje y luego lo guarda en la base de datos local."""
    print(f"ANFITRIÓN: Preparando para enviar WhatsApp a {telefono_destinatario}: '{texto_mensaje}'")
    if not telefono_destinatario or not texto_mensaje:
        return False

    numero_limpio = telefono_destinatario.split(':')[0]
    destinatario_jid_wa = f"{numero_limpio}@s.whatsapp.net"

    argumentos_para_envio = {"recipient": destinatario_jid_wa, "message": texto_mensaje}

    print(f"ANFITRIÓN: Llamando a la herramienta 'send_message' de WHATSAPP MCP")


    resultado_envio = mcp_call_tool(
        server_url=WHATSAPP_MCP_SERVER_URL,
        mcp_protocol_method="send_message",
        params_or_arguments=argumentos_para_envio,
        is_json_rpc_server=True
    )

    # Verificamos si el envío fue exitoso
    if resultado_envio and isinstance(resultado_envio, list) and len(resultado_envio) > 0 and resultado_envio[0] is True:
        print(f"ANFITRIÓN: Mensaje enviado exitosamente. Ahora guardando en la BD local...")

        # --- LÓGICA NUEVA PARA GUARDAR EL MENSAJE ENVIADO ---
        message_id = f"agent-sent-{int(time.time() * 1000)}"
        message_data = {
            "id": message_id,
            "chat_jid": destinatario_jid_wa,
            "sender": "agent", # O un identificador para el agente
            "content": texto_mensaje,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "is_from_me": True
        }

        mcp_call_tool(
            server_url=WHATSAPP_MCP_SERVER_URL,
            mcp_protocol_method="save_outgoing_message",
            params_or_arguments={"message_data": message_data},
            is_json_rpc_server=True
        )
        # --- FIN DE LA LÓGICA NUEVA ---

        return True

    print(f"ANFITRIÓN: Falló el envío del mensaje de WhatsApp. Respuesta cruda: {resultado_envio}")
    return False

def formatear_historial(historial: List[Dict[str, Any]]) -> str:
    if not historial:
        return "No hay historial previo."
    texto_formateado = ""
    for msg in reversed(historial):
        nombre_emisor = msg.get('chat_name', 'Usuario') if not msg.get('is_from_me') else "Agente"
        contenido = msg.get('content', '')
        if contenido:
             texto_formateado += f"{nombre_emisor}: {contenido}\n"
    return texto_formateado.strip()

def resumir_historial_streaming(historial_formateado: str, llm_provider: str = "openai") -> str:
    """Envía el historial al LLM y obtiene un resumen solo de lo relevante a cuentas de streaming."""
    prompt_resumen = f"""
    Eres un asistente que ayuda a un agente de ventas de cuentas de streaming. Tu tarea es leer la siguiente conversación y generar un resumen breve, claro y estructurado SOLO de lo relevante sobre cuentas de streaming.

    Instrucciones:
    - Resume únicamente los temas relacionados con cuentas, perfiles o plataformas de streaming.
    - Indica si ya se han saludado mutuamente (tanto el agente como el usuario deben haber respondido un saludo para considerarlo).
    - Enfócate en las intenciones del usuario: si quiere comprar, consultar precios, disponibilidad, o si ya aceptó el desglose de precios y solo espera detalles de pago.
    - Si el usuario mencionó servicios específicos y tiempos de contratación, inclúyelos en el resumen.
    - Ignora cualquier tema no relacionado con cuentas de streaming.
    - El resumen debe ser breve, directo y útil para que el agente entienda el contexto actual de la conversación.
    -incluye informacion si usuario quieres comprar un servicio o varios servicios pero te hace falta informacion, como el tiempo de contratacion o la cantidad de cuentas o perfiles que quiere. 
    --en acciones recomendadas del agente nunca pongas que consulte disponibilidad de los servicios ya que si el usuario ya te dijo que quiere comprar un servicio o varios servicios es porque ya sabe que hay disponibilidad de los servicios.
    --si el usuario no especifica la cantidad de perfiles o cuentas que quiere, asume que es 1 por defecto.
    --NO DES ACCIONES RECOMENDADAS DEL AGENTE, SOLO UN RESUMEN DE LO RELEVANTE SOBRE CUENTAS DE STREAMING.
    Ejemplo de desgloce de precios:
        "Perfecto, entonces tu pedido sería:" lo que quiere el usuario\n
        1 x Netflix (1 Mes): $199.00 \n
        2 x Disney Plus (1 Año): $1,199.00 \n 
        Total: $1,398.00 MXN\n
        si esta bien asi verdad ?"
      -lo anterior es un ejemplo de como se ve un desgloce de precios , y estes pendientes de que el usuario acepte el desgloce de precios para continuar con los detalles de pago.              
    ---
    CONVERSACIÓN:
    {historial_formateado}
    """
    llm = get_llm__deepseek_v1(provider=llm_provider)
    respuesta = llm.invoke(prompt_resumen)
    if hasattr(respuesta, 'content'):
        return respuesta.content.strip()
    elif isinstance(respuesta, str):
        return respuesta.strip()
    return str(respuesta)

# --- Lógica de la aplicación FastAPI ---
def get_llm(provider: str = "openai"):
    if provider == "openai":
        # NOTA: Guardar API Keys en el código no es una buena práctica para producción.
        # Es mejor usar variables de entorno.
        api_key = "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"
        if not api_key: raise ValueError("OPENAI_API_KEY no encontrada.")
        return ChatOpenAI(model="gpt-4.1-mini-2025-04-14", openai_api_key=api_key)
    return ChatOllama(model="llama3:8b", base_url=OLLAMA_HOST)


def get_llm_barato(provider: str = "openai"):
    if provider == "openai":
        # NOTA: Guardar API Keys en el código no es una buena práctica para producción.
        api_key = "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"
        if not api_key: raise ValueError("OPENAI_API_KEY no encontrada.")
        return ChatOpenAI(model="gpt-4.1-nano-2025-04-14", openai_api_key=api_key)
    return ChatOllama(model="llama3:8b", base_url=OLLAMA_HOST)

def get_llm__deepseek(provider: str = "openai"):
    print("ANFITRIÓN: Creando cliente LLM para DeepSeek Reasoner (deepseek-reasoner).")
    
    # Usamos la clase ChatOpenAI porque la API de DeepSeek es compatible con la de OpenAI
    return ChatOpenAI(
        model="deepseek-chat", # El nombre específico del modelo que querías
        openai_api_base="https://api.deepseek.com/v1",
        openai_api_key="sk-d89b08e0657f4adab29da3055b7cc80a"
    )

def get_llm__deepseek_v1(provider: str = "openai"):
    print("ANFITRIÓN: Creando cliente LLM para DeepSeek Reasoner (deepseek-reasoner).")
    
    # Usamos la clase ChatOpenAI porque la API de DeepSeek es compatible con la de OpenAI
    return ChatOpenAI(
        model="deepseek-reasoner", # El nombre específico del modelo que querías
        openai_api_base="https://api.deepseek.com/v1",
        openai_api_key="sk-d89b08e0657f4adab29da3055b7cc80a"
    )



app = FastAPI(title="Agente de Ventas con Contexto")

class MensajeChat(BaseModel):
    texto: str
    telefono_cliente: str 
    nombre_cliente: str = "Cliente Test"

# Reemplaza tu función @app.post("/chat") entera con esta
class informacion(BaseModel):
    servicio: str | None = Field(description="El servicio,plataforma o cuenta de streaming que el usuario quiere.")
    cantidad: int | None = Field(description="Cantidad de perfiles/cuentas solicitados.")
    tiempo_contratado: str | None = Field(description="La duración del contrato o el tiempo que quiere la cuenta , plataforma o servicio de streaming, si se especifica.")
    respuesta_faltante: str | None = Field(description="Si falta información esencial (servicio, cantidad o tiempo), genera una respuesta natural y amable para pedirla al usuario.")  
pydantic_parser2 = PydanticOutputParser(pydantic_object=informacion)

def normalizar_tiempo(texto_tiempo: str) -> str | None:
    """Convierte diferentes formas de escribir el tiempo a un formato estándar."""
    if not texto_tiempo:
        return None
    
    texto = texto_tiempo.lower()
    if "1 mes" in texto or "un mes" in texto:
        return "1 Mes"
    if "2 meses" in texto:
        return "2 Meses"
    if "3 meses" in texto:
        return "3 Meses"
    if "6 meses" in texto:
        return "6 Meses"
    if "1 año" in texto or "un año" in texto:
        return "1 Año"
    return None # No se pudo normalizar

# Pega este nuevo endpoint en tu main.py del host_app

class EstadoChat(BaseModel):
    telefono_cliente: str
    nuevo_estado: Literal["contestar", "no contestar"]

@app.post("/cambiar_estado_chat")
def cambiar_estado_chat(estado_info: EstadoChat):
    """
    Endpoint para cambiar el estado de respuesta de un chat específico.
    """
    print(f"ANFITRIÓN: Recibida petición para cambiar estado del chat del número {estado_info.telefono_cliente} a '{estado_info.nuevo_estado}'")

    # 1. Convertimos el número de teléfono al formato JID que usa la base de datos
    numero_limpio = estado_info.telefono_cliente.split(':')[0]
    chat_jid = f"{numero_limpio}@s.whatsapp.net"

    # 2. Preparamos los argumentos para nuestra herramienta
    argumentos_herramienta = {
        "chat_jid": chat_jid,
        "nuevo_estado": estado_info.nuevo_estado
    }

    # 3. Llamamos a la herramienta usando mcp_call_tool
    exito = mcp_call_tool(
        server_url=WHATSAPP_MCP_SERVER_URL,
        mcp_protocol_method="set_chat_estado",
        params_or_arguments=argumentos_herramienta,
        is_json_rpc_server=True  # Recuerda que el servidor de WhatsApp usa JSON-RPC
    )

    # 4. Devolvemos una respuesta para saber si funcionó
    if exito:
        print(f"ANFITRIÓN: El estado del chat {chat_jid} se cambió exitosamente a '{estado_info.nuevo_estado}'.")
        return {"status": "éxito", "detalle": f"El estado del chat {chat_jid} se cambió a {estado_info.nuevo_estado}"}
    else:
        print(f"ANFITRIÓN: Falló el cambio de estado para el chat {chat_jid}.")
        raise HTTPException(status_code=500, detail="No se pudo cambiar el estado del chat.")

# Añade esta función a tu main.py

def generar_desglose_y_guardar_pedido(plataformas_pedidas: list, telefono_cliente: str, nombre_cliente: str) -> tuple[str, str]:
    """
    Toma la lista de plataformas pedidas, genera el texto del desglose,
    y guarda el pedido en el estado pendiente. Devuelve el texto del desglose y el ID del pedido.
    """
    servicios_a_consultar = list(set([item.servicio for item in plataformas_pedidas if item.servicio]))
    precios_por_servicio = mcp_call_tool(DB_MCP_SERVER_URL, "listar_precios_de_servicio", {"servicio": servicios_a_consultar})
    
    resumen_orden = []
    total = 0.0
    
    for item in plataformas_pedidas:
        servicio = item.servicio
        cantidad = int(item.cantidad or 1)
        tiempo = item.tiempo_contratado # Asumimos que ya está normalizado
        precio = None

        if precios_por_servicio and servicio in precios_por_servicio:
            for plan in precios_por_servicio[servicio]:
                if plan.get("tiempo_contratado") == tiempo:
                    precio = float(plan.get("precio_mxn", 0))
                    break
        
        if precio:
            subtotal = precio * cantidad
            resumen_orden.append(f"{cantidad} x {servicio.replace('_', ' ').title()} ({tiempo}): ${subtotal:.2f} MXN")
            total += subtotal
        else:
            resumen_orden.append(f"{cantidad} x {servicio.replace('_', ' ').title()} ({tiempo}): Precio no disponible")

    resumen_texto = "\n".join(resumen_orden)
    
    # Guardar el pedido pendiente en el estado de la app
    pedido_id = f"PEDIDO-{int(time.time() * 1000)}"
    if not hasattr(app.state, 'clientes_pendientes'):
        app.state.clientes_pendientes = {}
    
    app.state.clientes_pendientes[pedido_id] = {
        "telefono": telefono_cliente,
        "nombre": nombre_cliente,
        "descripcion_compra": resumen_texto,
        "total_mxn": total,
        "status": "esperando_pago" # Nuevo estado inicial
    }
    print(f"ANFITRIÓN: Pedido {pedido_id} guardado en estado 'esperando_pago'.")
    
    return resumen_texto, f"${total:.2f} MXN"


@app.post("/chat")
def procesar_mensaje_de_chat(mensaje: MensajeChat, llm_provider: str = "openai"):
    
    print(f"------------------INICIA FLUJO DE PROCESAMIENTO DE MENSAJE DE CHAT----------------------------")
    print(f"Mensaje Recibido: {mensaje.texto} de {mensaje.telefono_cliente} ({mensaje.nombre_cliente})")
    print(f"\n--- ANFITRIÓN: Petición a /chat por '{mensaje.telefono_cliente}' con '{mensaje.texto}' ---")
    numero_limpio_remitente = mensaje.telefono_cliente.split(':')[0]
    if telefono_admin == numero_limpio_remitente:
        print("ANFITRIÓN: Mensaje recibido del administrador, ignorando procesamiento.")
        # clasificamos el mensaje del administrador para obtner las herramientas que tiene acceso
        prompt_admin = f"""
        Tu tarea es clasificar el mensaje de un administrador y DEBES responder SIEMPRE con un objeto JSON válido.
        Las intenciones válidas son: 'confirmar_pago_usuario' y 'no_relacionada'.

        1. Si el mensaje contiene 'confirmo-' seguido de un número (ej: "confirmo-5215541234567"), la intención es 'confirmar_pago_usuario' y debes extraer el número completo en 'numero_cliente'.
        2. Para CUALQUIER OTRO mensaje (como "hola", "¿cómo estás?", etc.), la intención DEBE SER 'no_relacionada'.
        3. Formato de salida: Tu respuesta DEBE SER UNICAMENTE un objeto JSON válido con las claves 'intencion', 'numero_cliente','respuesta'.
        Mensaje del administrador: "{mensaje.texto}"

        -tu 'respuesta' debe de ser la respuesta final que le enviaras al administrador si es que la intencion es 'confirmar_pago_usuario' o 'no_relacionada'
        """
        pydantic_parser2 = PydanticOutputParser(pydantic_object=SolicitudAdministrador)
        final_prompt_admin = PromptTemplate.from_template(template=prompt_admin)
        llm_admin = get_llm_barato(provider=llm_provider)
        chain_admin = final_prompt_admin | llm_admin | pydantic_parser2
        resultado_llm_admin = chain_admin.invoke({})
        
        print(f"ANFITRIÓN: Intención del administrador: {resultado_llm_admin.intencion}")

        if resultado_llm_admin.intencion == "confirmar_pago_usuario":
            print("ANFITRIÓN: Confirmación de pago del usuario detectada.")
            numero_cliente = resultado_llm_admin.numero_cliente
            if numero_cliente and numero_cliente.startswith("confirmo-"):
                #cambiamos el estado del estatus del pedido del cliente a 'pagado'
                estatus_chat = "pagado"
                info_chat = f"El administrador ha confirmado el pago del cliente con número {numero_cliente}."
                mcp_call_tool(DB_MCP_SERVER_URL, "modificar_estatus_chat", {"numero_del_chat":numero_cliente, "nuevo_estatus": estatus_chat, "nueva_informacion": info_chat})
                # Enviamos un mensaje de confirmación al 
                print(f"ANFITRIÓN: Enviando mensaje de confirmación al administrador.")
                enviar_mensaje_whatsapp(mensaje.telefono_cliente, f"El pago del cliente {numero_cliente} ha sido confirmado y el pedido se ha marcado como pagado.")
                return {"status": "ok", "message": f"Pago del cliente {numero_cliente} confirmado y pedido marcado como pagado."}
            else:
                print("ANFITRIÓN: Formato de confirmación incorrecto.")
                enviar_mensaje_whatsapp(mensaje.telefono_cliente, "Formato de confirmación incorrecto. Por favor, usa 'confirmo-numerodelcliente'.")
            return {"status": "error", "message": "Formato de confirmación incorrecto."}
        else:
            print("ANFITRIÓN: Mensaje del administrador no relacionado con confirmación de pago.")
            enviar_mensaje_whatsapp(mensaje.telefono_cliente, "Mensaje del administrador recibido, no se procesará.")
        return {"status": "ok", "message": "Mensaje del administrador recibido, no se procesará."}
    try:
        chat_jid = f"{mensaje.telefono_cliente.split(':')[0]}@s.whatsapp.net"
        args_historial = {"chat_jid": chat_jid, "limit": 10}
        historial_mensajes = mcp_call_tool(WHATSAPP_MCP_SERVER_URL, "list_messages", args_historial, is_json_rpc_server=True)
        historial_formateado = formatear_historial(historial_mensajes if historial_mensajes else [])
        #print(f"ANFITRIÓN: Historial obtenido:\n---\n{historial_formateado}\n---")

        # Llama a la función para resumir el historial y úsalo como contexto
        resumen_historial = resumir_historial_streaming(historial_formateado, llm_provider)
        print(f"ANFITRIÓN: Resumen del historial relevante:\n{resumen_historial}\n---")

        servicios_activos_db_response = mcp_call_tool(DB_MCP_SERVER_URL, "listar_servicios_disponibles")
        if not servicios_activos_db_response:
            return enviar_mensaje_whatsapp(mensaje.telefono_cliente, "Lo siento, no puedo consultar los servicios en este momento.")
            
        lista_servicios_para_prompt = ', '.join([f"'{s}'" for s in servicios_activos_db_response])
        
        final_prompt_text = prompt_template_text.format(
            lista_servicios_validos=lista_servicios_para_prompt,
            historial_chat=resumen_historial,
            texto_usuario=mensaje.texto
        )
        
        final_prompt = PromptTemplate.from_template(template=final_prompt_text)
        llm = get_llm(provider=llm_provider)
        chain = final_prompt | llm | pydantic_parser
        resultado_llm = chain.invoke({})

        print(f"ANFITRIÓN: Intención extraída por la IA: {resultado_llm.intencion}")
        respuesta_final_para_enviar = ""

        if resultado_llm.intencion == "consultar_opciones_de_servicio":
            print("ANFITRIÓN: Intención de consultar TODAS las opciones detectada.")
            precios_por_servicio = mcp_call_tool(DB_MCP_SERVER_URL, "listar_precios_de_servicio")
            if precios_por_servicio and isinstance(precios_por_servicio, dict):
                respuesta_formateada = "si por el momento solo tengo estas plataformas disponibles , quedo a tus ordenes cualquier otra duda \n\nPERFILES PREMIUM DISPONIBLES 🤯\n\n"
                for servicio, planes in precios_por_servicio.items():
                    nombre_servicio_formateado = servicio.replace('_', ' ').upper()
                    respuesta_formateada += f"*{nombre_servicio_formateado}* 🍿:\n"
                    for plan in planes:
                        respuesta_formateada += f"- {plan.get('tiempo_contratado', 'N/A')}: ${plan.get('precio_mxn', 'N/A')} MXN\n"
                    respuesta_formateada += "\n"
                respuesta_final_para_enviar = respuesta_formateada.strip()
            else:
                respuesta_final_para_enviar = "Lo siento, no pude obtener la lista de precios en este momento."

        elif resultado_llm.intencion == "consultar_disponibilidad":
            servicios_solicitados = resultado_llm.servicio
            print(f"ANFITRIÓN: Intención de consultar disponibilidad para '{servicios_solicitados}' detectada.")
            if servicios_solicitados:
                # Permite uno o varios servicios separados por coma
                lista_servicios = [s.strip() for s in servicios_solicitados.split(",")] if "," in servicios_solicitados else [servicios_solicitados.strip()]
                precios_especificos = mcp_call_tool(DB_MCP_SERVER_URL, "listar_precios_de_servicio", {"servicio": lista_servicios if len(lista_servicios) > 1 else lista_servicios[0]})
                servicios_encontrados = [s for s in lista_servicios if precios_especificos and s in precios_especificos]
                if precios_especificos and servicios_encontrados:
                    # Llama al LLM para generar un encabezado natural basado en el mensaje del usuario
                    encabezado_prompt = f"""
                    Eres un asistente de ventas de cuentas de streaming. Escribe un encabezado breve, natural y amable para responder a este mensaje del usuario, explicando que tienes disponibles los planes para las plataformas que menciona. No repitas el mensaje del usuario, solo responde de forma cordial y simple.
                    nunca termines el encabezado con un signo de interrogación o pregunta.
                    tampoco inicies el encabezado con un saludo como hola , claro , por supuesto o algo similar.
                    podrias decir algo como : " con mucho gusto para esas plataformas tengo estos planes disponibles :  \n\n quedo a tus ordenes cualquier otra cosa o duda " o la oracion en singular .
                    Mensaje del usuario: "{mensaje.texto}"
                    """
                    llm_encabezado = get_llm_barato(provider=llm_provider)
                    encabezado_respuesta = llm_encabezado.invoke(encabezado_prompt)
                    if hasattr(encabezado_respuesta, 'content'):
                        encabezado_texto = encabezado_respuesta.content.strip()
                    elif isinstance(encabezado_respuesta, str):
                        encabezado_texto = encabezado_respuesta.strip()
                    else:
                        encabezado_texto = "Aquí tienes los planes disponibles:"

                    respuesta_formateada = f"{encabezado_texto}\n\n"
                    for servicio in servicios_encontrados:
                        respuesta_formateada += f"*{servicio.replace('_', ' ').upper()}* 🍿:\n"
                        for plan in precios_especificos[servicio]:
                            respuesta_formateada += f"- {plan.get('tiempo_contratado', 'N/A')}: ${plan.get('precio_mxn', 'N/A')} MXN\n"
                        respuesta_formateada += "\n"
                    respuesta_final_para_enviar = respuesta_formateada.strip()
                else:
                    # Si no hay servicios encontrados válidos, muestra los servicios disponibles reales
                    print("ANFITRIÓN: No se encontraron servicios válidos en la base de datos.")
                    servicios_validos_str = ', '.join(servicios_activos_db_response)
                    no_tenemos_el_servicio_prompt = f"""
                    Eres un asistente de ventas de cuentas de streaming.
                    El usuario ha preguntado por un servicio que no tenemos disponible en este momento.
                    Tu tarea es responder de forma natural y amable, explicando que no tienes ese servicio en este momento, pero que tienes otros servicios disponibles.
                    Explícale que tenemos estos servicios disponibles y que si le interesan.

                    Servicios disponibles: {servicios_validos_str}
                    Mensaje del usuario: "{mensaje.texto}"

                    reglas que debes seguir:
                    1. No repitas el mensaje del usuario, solo responde de forma cordial y simple
                    2.- no inicies saludando o diciendo hola , claro , por supuesto o algo similar.
                    3.- no termines con un signo de interrogacion o pregunta.
                    
                    -- Ejemplo de respuesta:
                    "disculpame pero no tengo esa plataforma ahorita por el momento . pero tengo estos disponibles por si te interesan :" seguido de los servicios disponibles con un buen formato y emojis si quieres. 

                    """
                    llm_no_tenemos = get_llm_barato(provider=llm_provider)
                    respuesta_no_tenemos = llm_no_tenemos.invoke(no_tenemos_el_servicio_prompt)
                    if hasattr(respuesta_no_tenemos, 'content'):
                        respuesta_final_para_enviar = respuesta_no_tenemos.content.strip()
                    elif isinstance(respuesta_no_tenemos, str):
                        respuesta_final_para_enviar = respuesta_no_tenemos.strip()
            else:
                respuesta_final_para_enviar = "entonces de que plataforma de streaming te gustaria saber los precios ? "
                respuesta_final_para_enviar = "error api deepseek reasoner no disponible por el momento , por favor intentalo mas tarde"
        elif resultado_llm.intencion == "saludar":
            print("ANFITRIÓN: Intención de saludar detectada.")
            respuesta_final_para_enviar = resultado_llm.respuesta or "Hola que tal muy buenas tardes"
        # Reemplaza el bloque elif de "comprar_servicio" con esta versión

        elif resultado_llm.intencion == "comprar_servicio":
            print("ANFITRIÓN: Intención de comprar un servicio detectada.")
            # Mantenemos tu excelente idea de usar un prompt específico para estructurar la compra.
            servicios_activos_db_response = mcp_call_tool(DB_MCP_SERVER_URL, "listar_servicios_disponibles")
            if not servicios_activos_db_response:
                return enviar_mensaje_whatsapp(mensaje.telefono_cliente, "Lo siento, no puedo consultar los servicios en este momento.")
                
            lista_servicios_para_prompt = ', '.join([f"'{s}'" for s in servicios_activos_db_response])

            prompt_plataformas = f"""
            Eres un agente de ventas de cuentas de streaming. Analiza el historial y el último mensaje del usuario para identificar exactamente qué plataformas, servicios o perfiles de streaming quiere comprar el usuario y por cuánto tiempo cada uno.
            Devuelve SIEMPRE una lista de objetos JSON, cada uno con las claves:
            - 'servicio': nombre del servicio/plataforma. Normaliza los nombres encontrados de la plataforma que coincida con {lista_servicios_para_prompt}(ej: 'disney plus' a 'disney_premium') si es mas de uno separalo con una coma.
            - 'cantidad': número de perfiles/cuentas (asume 1 si no se especifica),si tiene mas de un servicio entonces separalos por una coma y en el orden que escribas el servicio.
            - 'tiempo_contratado': periodo de tiempo (ej: "un mes", "1 año"). Déjalo como null si no se especifica.
            - 'respuesta_faltante': si falta información esencial, pon aquí una pregunta natural y amable para el usuario (si no falta nada, déjalo como null).
            ejemplo de respuesta 'cantidad':
            - 'cantidad': (si es una plataforma y no se especifica la cantidad) 1
            - 'cantidad': (si es mas de una plataforma y no se especifica la cantidad) 1, 1, 1 (por ejemplo si son 3 plataformas diferentes en el orden que mandes servicio)
            Historial relevante:
            {resumen_historial}
            Último mensaje del usuario:
            "{mensaje.texto}"
            """
            llm_plataformas = get_llm__deepseek_v1(provider=llm_provider)
            # Usamos un parser específico para la respuesta de esta llamada
            compra_parser = PydanticOutputParser(pydantic_object=CompraServicioLLM)
            
            # Creamos y ejecutamos la cadena para parsear la compra
            chain_compra = PromptTemplate.from_template(template=prompt_plataformas) | llm_plataformas
            respuesta_llm_compra = chain_compra.invoke({})
            
            plataformas_pedidas = []
            respuesta_faltante = None
            servicios_faltan_tiempo = []
            try:
                json_str = respuesta_llm_compra.content.strip()
                if json_str.startswith("```json"):
                    json_str = json_str[7:-3].strip()
                parsed = json.loads(json_str)
                # Si el LLM devuelve un solo objeto, lo convertimos en lista
                if isinstance(parsed, dict):
                    parsed = [parsed]
                # Si el LLM devuelve servicios/cantidades como string separados por coma, los expandimos
                expanded = []
                for item in parsed:
                    # Si servicio es string separado por coma, y cantidad también, los separamos y mapeamos
                    servicios = [s.strip() for s in str(item.get('servicio', '')).split(',') if s.strip()]
                    cantidades = str(item.get('cantidad', '')).split(',') if 'cantidad' in item else []
                    cantidades = [c.strip() for c in cantidades if c.strip()]
                    # Si no hay cantidades, asumimos 1 para cada servicio
                    if not cantidades or len(cantidades) != len(servicios):
                        cantidades = ['1'] * len(servicios)
                    # Si tiempo_contratado es string separado por coma, lo separamos, si no, lo replicamos
                    tiempos = str(item.get('tiempo_contratado', '')).split(',') if 'tiempo_contratado' in item and item['tiempo_contratado'] else []
                    tiempos = [t.strip() for t in tiempos if t.strip()]
                    if not tiempos or len(tiempos) != len(servicios):
                        tiempos = [item.get('tiempo_contratado', None)] * len(servicios)
                    # respuesta_faltante puede ser una sola o lista
                    respuestas_faltantes = str(item.get('respuesta_faltante', '')).split(',') if 'respuesta_faltante' in item and item['respuesta_faltante'] else []
                    respuestas_faltantes = [r.strip() for r in respuestas_faltantes if r.strip()]
                    if not respuestas_faltantes or len(respuestas_faltantes) != len(servicios):
                        respuestas_faltantes = [item.get('respuesta_faltante', None)] * len(servicios)
                    # Expandimos a objetos individuales
                    for idx, servicio in enumerate(servicios):
                        obj = CompraServicioLLM(
                            servicio=servicio,
                            cantidad=int(cantidades[idx]) if idx < len(cantidades) else 1,
                            tiempo_contratado=normalizar_tiempo(tiempos[idx]) if idx < len(tiempos) else None,
                            respuesta_faltante=respuestas_faltantes[idx] if idx < len(respuestas_faltantes) else None
                        )
                        if not obj.tiempo_contratado:
                            servicios_faltan_tiempo.append(obj.servicio)
                        if obj.respuesta_faltante:
                            respuesta_faltante = obj.respuesta_faltante
                        plataformas_pedidas.append(obj)
            except (json.JSONDecodeError, ValidationError, Exception) as e:
                print(f"Error parseando o validando la respuesta del LLM para compra: {e}")
                plataformas_pedidas = []

            # --- Lógica para actuar según lo parseado ---

            if servicios_faltan_tiempo:
                # Si falta el tiempo para algún servicio, pedimos que lo especifiquen
                prompt_pedir_tiempo = f"""Eres un agente de ventas de cuentas de streaming. El usuario ha solicitado los siguientes servicios, pero no especificó el tiempo de contratación para algunos de ellos: {', '.join(servicios_faltan_tiempo)}.
                Tu tarea es preguntar de forma natural y amable cuánto tiempo le gustaría contratar el servicio al que le falto especificar el tiempo de contratación.
                Responde con una pregunta clara y directa, por ejemplo: "Solo una duda, disculpa, para  'servicio que falta especificar el tiempo ' cuanto tiempo te gustaría contratar? Muchas gracias."
                puede buscar esa información en el historial de chat si es necesario.
                -Mensaje del usuario: "{mensaje.texto}"
                -historial relevante:
                {resumen_historial}
                """
                llm_pedir_tiempo = get_llm_barato(provider=llm_provider)
                respuesta_llm_tiempo = llm_pedir_tiempo.invoke(prompt_pedir_tiempo)
                if hasattr(respuesta_llm_tiempo, 'content'):
                    respuesta_final_para_enviar = respuesta_llm_tiempo.content.strip()
                elif isinstance(respuesta_llm_tiempo, str):
                    respuesta_final_para_enviar = respuesta_llm_tiempo.strip()
                else:
                    # Fallback si no se pudo parsear correctamente
                    print("ANFITRIÓN: No se pudo parsear la respuesta del LLM para pedir tiempo.")
                    # Creamos una respuesta genérica
                    respuesta_faltante = "Solo una duda, disculpa,por cuanto tiempo serian los servicios ? muchas gracias"
            elif respuesta_faltante:
                # Si el LLM generó una pregunta para el usuario
                respuesta_final_para_enviar = respuesta_faltante
            
            elif not plataformas_pedidas:
                # Si no pudimos entender el pedido
                respuesta_final_para_enviar = "ok perdoname la vida entonces que plataformas vas a querer disculpame no entendi bien jaja "
            
            else:
                # Tenemos toda la información, procedemos a crear el desglose
                servicios_a_consultar = list(set([item.servicio for item in plataformas_pedidas if item.servicio]))
                precios_por_servicio = mcp_call_tool(DB_MCP_SERVER_URL, "listar_precios_de_servicio", {"servicio": servicios_a_consultar})
                
                resumen_orden = []
                total = 0.0

                for item in plataformas_pedidas:
                    servicio = item.servicio
                    cantidad = int(item.cantidad or 1)
                    tiempo = item.tiempo_contratado # Ya está normalizado
                    precio = None

                    # Búsqueda de precio corregida y robusta
                    if precios_por_servicio and servicio in precios_por_servicio:
                        for plan in precios_por_servicio[servicio]:
                            if plan.get("tiempo_contratado") == tiempo:
                                precio = float(plan.get("precio_mxn", 0))
                                break
                    
                    if precio:
                        subtotal = precio * cantidad
                        resumen_orden.append(f"{cantidad} x {servicio.replace('_', ' ').title()} ({tiempo}): ${subtotal:.2f} MXN")
                        total += subtotal
                    else:
                        resumen_orden.append(f"{cantidad} x {servicio.replace('_', ' ').title()} ({tiempo}): Precio no disponible")

                resumen_texto = "\n".join(resumen_orden)
                
                # Le pedimos a la IA que formatee amablemente nuestro desglose
                prompt_desglose = f"""
                Eres un agente de ventas amable. Redacta de forma natural el siguiente desglose de compra para el usuario, incluyendo el total y preguntando si está de acuerdo para proceder.

                Desglose:
                {resumen_texto}
                Total: ${total:.2f} MXN

                 --
                 Ejemplo de respuesta:
                 "Perfecto, entonces tu pedido sería:" lo que quiere el usuario\n
                   1 x Netflix (1 Mes): $199.00 \n
                   2 x Disney Plus (1 Año): $1,199.00 \n 
                     Total: $1,398.00 MXN\n
                   si esta bien asi verdad ?"
                -lo anterior es un ejemplo de como deberia ser la respuesta no lo utilices como verdadero.  
                """
                llm_desglose = get_llm_barato(provider=llm_provider)
                respuesta_llm_final = llm_desglose.invoke(prompt_desglose)
                
                if hasattr(respuesta_llm_final, 'content'):
                    respuesta_final_para_enviar = respuesta_llm_final.content.strip()
                else: # Fallback por si acaso
                    respuesta_final_para_enviar = f"Perfecto, entonces tu pedido sería:\n{resumen_texto}\n*Total: ${total:.2f} MXN*\n\n¿esta bien asi verdad ?"

        elif resultado_llm.intencion == "no_relacionada_a_las_cuentas_de_streaming":
            print("ANFITRIÓN: Intención no relacionada a cuentas de streaming detectada.")
            resultado_llm.intencion = "no_contestar"
        elif resultado_llm.intencion == "esperando_detalles_de_pago":
            print("ANFITRIÓN: Intención de esperar detalles de pago detectada.")
            respuesta_final_para_enviar = (
                "vale muchas gracias entonces te comparto mis datos para la transferencia\n\n"
                "¡Hola! Te comparto mi información para realizar el pago:\n\n"
                "Entidad: NU MEXICO\n"
                "Número CLABE: 638180010135607304\n"
                "Nombre: Bryan Amaro Vazquez"
            )
            #modificamos el estatus del chat en la base de datos de streaming con agente mcp
            prompt_info_chat = f"""eres un agente de ventas de cuentas de streaming.
            con base al historial del chat ,genera un mensaje para el administrador con 
            la informacion de compra del cliente ,
            
            ejemplo de respuesta:
            "Cliente: {mensaje.nombre_cliente} ({mensaje.telefono_cliente})\n"
            "servicios solicitados:" los servicios que el cliente quiere comprar separados por coma.
            "total a pagar:" total a pagar por los servicios que el cliente quiere comprar.
            "verificca si ya te llego el deposito o transferencia administrador"
            --lo anterior es un ejemplo de como deberia ser la respuesta no lo utilices como verdadero.
            -historial relevante:
            {resumen_historial}
            -mensaje del usuario: "{mensaje.texto}"
            """

            llm_info_chat = get_llm__deepseek(provider=llm_provider)
            info_chat = llm_info_chat.invoke(prompt_info_chat)
            if hasattr(info_chat, 'content'):
                info_chat = info_chat.content.strip()
            else:
                info_chat = "Cliente: {mensaje.nombre_cliente} ({mensaje.telefono_cliente})\n" \
                            "servicios solicitados: " + ", ".join([item.servicio for item in plataformas_pedidas if item.servicio]) + "\n" \
                            "total a pagar: " + str(total) + "\n" \
                            "verifica si ya te llego el deposito o transferencia administrador" 
            estatus_chat ="esperando_confirmacion_de_pago"
            mcp_call_tool(DB_MCP_SERVER_URL, "ingresar_estatus_chat", {"numero_del_chat":mensaje.telefono_cliente, "nuevo_estatus": estatus_chat, "nueva_informacion": info_chat})
            # Enviamos un mensaje al administrador para que confirme el pago
            enviar_mensaje_whatsapp(telefono_admin, info_chat)
            print(f"ANFITRIÓN: Mensaje enviado al administrador para confirmar el pago del cliente {mensaje.nombre_cliente} ({mensaje.telefono_cliente}).")
        elif resultado_llm.intencion == "no_contestar":
            print("ANFITRIÓN: Intención de no contestar detectada.")
            cambiar_estado_chat(EstadoChat(telefono_cliente=mensaje.telefono_cliente, nuevo_estado="no contestar"))
        elif resultado_llm.intencion == "informacion_sobre_las_cuentas_de_streaming":
            print("ANFITRIÓN: Intención de información sobre cuentas de streaming detectada.")
            respuesta_final_para_enviar = resultado_llm.respuesta 
        elif resultado_llm.intencion == "confirmar_pago_usuario":
            print("ANFITRIÓN: Intención de 'confirmar_pago_usuario' detectada. Consultando estatus del chat...")
            estatus_compra = mcp_call_tool(DB_MCP_SERVER_URL, "buscar_estatus_chat", {"numero_del_chat": mensaje.telefono_cliente})

            if not estatus_compra:
                print("ANFITRIÓN: No se encontró un pedido pendiente para este cliente.")
                # Opcional: Enviar un mensaje si no hay nada pendiente.
                # respuesta_final_para_enviar = "Hola, parece que no tienes ningún pedido pendiente de confirmación. ¿En qué te puedo ayudar?"
                return {"status": "ok", "message": "No hay pedido pendiente."}

            estatus = estatus_compra.get('estatus')
            informacion_compra = estatus_compra.get('informacion_de_la_compra')
            print(f"ANFITRIÓN: Estatus encontrado: {estatus} | Información: {informacion_compra}")

            if estatus == 'pagado':
                print("ANFITRIÓN: El pago ya fue confirmado. Procediendo a entregar credenciales.")
                
                # 1. Usar un LLM para parsear la información de la compra a un formato estructurado
                prompt_parser_compra = f"""
                Analiza el siguiente texto que describe una compra de streaming y extráelo a una lista de objetos JSON.
                Cada objeto debe tener 'servicio', 'tiempo_contratado' (normalizado a 'X Mes' o 'X Año'), y 'cantidad'.

                Texto de la Compra:
                ---
                {informacion_compra}
                ---

                Ejemplo de cómo parsear:
                Texto: "Cliente: Juan (52155...)\\nservicios solicitados: 1 x Netflix (1 Mes), 2 x Disney Plus (1 Año)\\ntotal a pagar: $1398.00"
                Salida JSON:
                {{
                    "detalles": [
                        {{ "servicio": "netflix", "tiempo_contratado": "1 Mes", "cantidad": 1 }},
                        {{ "servicio": "disney_premium", "tiempo_contratado": "1 Año", "cantidad": 2 }}
                    ]
                }}
                --lo anterior es un ejemplo de como deberia ser la respuesta no lo utilices como verdadero.
                Tu respuesta DEBE ser únicamente el objeto JSON.
                """
                parser_compra = PydanticOutputParser(pydantic_object=ListaDetallesCompra)
                chain_parser = PromptTemplate.from_template(template=prompt_parser_compra) | get_llm_barato(provider=llm_provider) | parser_compra
                
                try:
                    detalles_compra = chain_parser.invoke({})
                    print(f"ANFITRIÓN: Detalles de la compra parseados: {detalles_compra.detalles}")
                except Exception as e:
                    print(f"ANFITRIÓN: ERROR CRÍTICO - No se pudo parsear la información de la compra. {e}")
                    enviar_mensaje_whatsapp(telefono_admin, f"¡ERROR CRÍTICO! No se pudieron parsear los detalles de la compra para el cliente {mensaje.telefono_cliente}. Por favor, entrégale las credenciales manualmente. Info: {informacion_compra}")
                    respuesta_final_para_enviar = "ya me llego el deposito muchisimas gracias , en un momento te comparto los datos de accesso para las cuentas gracias"
                    enviar_mensaje_whatsapp(mensaje.telefono_cliente, respuesta_final_para_enviar)
                    enviar_mensaje_whatsapp(telefono_admin, f"¡ALERTA! No se pudieron parsear los detalles de la compra para el cliente {mensaje.telefono_cliente}. Por favor, entrégale las credenciales manualmente. Info: {informacion_compra}")
                    return {"status":  "error", "message": "Fallo al parsear detalles"}

                # 2. Registrar al cliente para obtener su ID
                id_cliente = mcp_call_tool(DB_MCP_SERVER_URL, "registrar_cliente", {"nombre": mensaje.nombre_cliente, "telefono": mensaje.telefono_cliente})
                if not id_cliente:
                    print("ANFITRIÓN: ERROR CRÍTICO - No se pudo registrar al cliente.")
                    enviar_mensaje_whatsapp(telefono_admin, f"¡ERROR CRÍTICO! No se pudo registrar al cliente {mensaje.telefono_cliente} para entregarle su compra. Ayuda manual requerida.")
                    return {"status": "error", "message": "Fallo al registrar cliente"}
                
                credenciales_entregadas = []
                servicios_con_problemas = []

                # 3. Iterar sobre cada item comprado para asignarlo
                for detalle in detalles_compra.detalles:
                    print(f"ANFITRIÓN: Procesando... {detalle.cantidad}x {detalle.servicio} por {detalle.tiempo_contratado}")
                    # A. Buscar perfiles disponibles
                    perfiles_encontrados = mcp_call_tool(DB_MCP_SERVER_URL, "buscar_perfil_disponible", {
                        "servicio": detalle.servicio,
                        "duracion": detalle.tiempo_contratado,
                        "cantidad": detalle.cantidad
                    })

                    if perfiles_encontrados and len(perfiles_encontrados) >= detalle.cantidad:
                        for i in range(detalle.cantidad):
                            perfil = perfiles_encontrados[i]
                            id_perfil = perfil.get('id_perfil')
                            
                            # B. Finalizar la venta y obtener credenciales
                            mcp_call_tool(DB_MCP_SERVER_URL, "finalizar_venta", {"id_cliente": id_cliente, "id_perfil": id_perfil})
                            credenciales = mcp_call_tool(DB_MCP_SERVER_URL, "obtener_credenciales_perfil", {"id_perfil": id_perfil})
                            
                            if credenciales:
                                credenciales['nombre_servicio_display'] = detalle.servicio.replace('_', ' ').title()
                                credenciales_entregadas.append(credenciales)
                                print(f"ANFITRIÓN: Perfil {id_perfil} ({detalle.servicio}) asignado al cliente {id_cliente}.")
                    else:
                        print(f"ANFITRIÓN: ¡ALERTA! No hay suficientes perfiles para '{detalle.servicio}' ({detalle.tiempo_contratado}). Solicitado: {detalle.cantidad}, Disponible: {len(perfiles_encontrados) if perfiles_encontrados else 0}.")
                        servicios_con_problemas.append(f"{detalle.cantidad}x {detalle.servicio} ({detalle.tiempo_contratado})")

                # 4. Construir y enviar el mensaje final al cliente
                if credenciales_entregadas:
                    mensaje_final = f"¡Muchas gracias por tu compra, {mensaje.nombre_cliente}! 🎉\n\nAquí tienes los datos de acceso a tus servicios:\n"
                    for cred in credenciales_entregadas:
                        mensaje_final += (
                            f"\n--- *{cred['nombre_servicio_display']}* ---\n"
                            f"**Correo:** `{cred.get('correo_asociado')}`\n"
                            f"**Contraseña:** `{cred.get('contraseña')}`\n"
                            f"**Perfil:** `{cred.get('nombre_perfil')}`\n"
                            f"**PIN:** `{cred.get('pin_perfil', 'No aplica')}`\n"
                        )
                    mensaje_final += "\n¡Disfruta de tus cuentas! Si tienes alguna duda, aquí estoy para ayudarte."
                    enviar_mensaje_whatsapp(mensaje.telefono_cliente, mensaje_final)

                # 5. Notificar al admin y al cliente si hubo problemas
                if servicios_con_problemas:
                    problemas_str = ", ".join(servicios_con_problemas)
                    enviar_mensaje_whatsapp(telefono_admin, f"¡ALERTA DE INVENTARIO! No se pudieron entregar los siguientes servicios al cliente {mensaje.telefono_cliente} por falta de perfiles: {problemas_str}. Por favor, resuélvelo manualmente.")
                    enviar_mensaje_whatsapp(mensaje.telefono_cliente, f"Tuvimos un inconveniente para generar el acceso a los siguientes servicios: {problemas_str}. Un agente se pondrá en contacto contigo muy pronto para solucionarlo. ¡Disculpa las molestias!")
                
                # 6. Actualizar el estado de la compra a 'entregado'
                mcp_call_tool(DB_MCP_SERVER_URL, "modificar_estatus_chat", {
                    "numero_del_chat": mensaje.telefono_cliente,
                    "nuevo_estatus": "entregado",
                    "nueva_informacion": "Las credenciales fueron enviadas al cliente."
                })
                respuesta_final_para_enviar = "" # Ya enviamos los mensajes relevantes

            elif estatus == 'esperando_confirmacion_de_pago':
                print("ANFITRIÓN: El pago está pendiente de confirmación por un administrador.")
                respuesta_final_para_enviar = "¡Gracias por avisar! Déjame revisar si ya se reflejó tu pago. En cuanto lo confirme, te enviaré los datos de acceso (correo, contraseña, perfil y PIN). ¡No tardo!"
                # Re-notificar al admin por si se le pasó
                info_para_admin = f"RECORDATORIO: El cliente {mensaje.nombre_cliente} ({mensaje.telefono_cliente}) está esperando la confirmación de su pago. Por favor, revisa y confirma con 'confirmo-{mensaje.telefono_cliente}'."
                enviar_mensaje_whatsapp(telefono_admin, info_para_admin)
            
            elif estatus == 'entregado':
                print("ANFITRIÓN: Este pedido ya fue entregado.")
                respuesta_final_para_enviar = "Hola, veo que tu pedido ya fue entregado anteriormente. ¿Buscas tus credenciales? Puedo pedirlas de nuevo si quieres. ¿O te puedo ayudar en algo más?"

            else: # Otros estados
                print(f"ANFITRIÓN: El pedido tiene un estatus desconocido: {estatus}")
                respuesta_final_para_enviar = "Estoy revisando el estado de tu pedido, dame un momento por favor."
    except Exception as e:
        print(f"Error en procesar_mensaje_de_chat: {e}")
        traceback.print_exc()
        respuesta_final_para_enviar = "Ocurrió un error procesando tu mensaje. Por favor, intenta de nuevo más tarde."

    # Solo enviar mensajes si la intención NO es "no_contestar"
    if resultado_llm.intencion != "no_contestar":
        print(f"ANFITRIÓN: Respuesta final a enviar:\n{respuesta_final_para_enviar}")
        enviar_mensaje_whatsapp(mensaje.telefono_cliente, respuesta_final_para_enviar)
        if resultado_llm.intencion == "esperando_detalles_de_pago":
            enviar_mensaje_whatsapp(mensaje.telefono_cliente, "Quedo a tus ordenes cualquier cosa ,y en cuento me mandes el comprobante de pago te comparto los datos de accesso : correo,contraseña,perfil y pin de tu cuenta de streaming muchas gracias .")
    return {"status": "respuesta enviada a WhatsApp", "respuesta_generada": respuesta_final_para_enviar}

@app.post("/webhook/mercadopago")
async def webhook_mercadopago(request: Request): 
    print(f"ANFITRIÓN WEBHOOK: Notificación de MercadoPago recibida.")
    print(f"ANFITRIÓN WEBHOOK (al inicio): app.state.clientes_pendientes actual es: {getattr(app.state, 'clientes_pendientes', {})}")
    body = await request.json()
    print(f"ANFITRIÓN WEBHOOK: Cuerpo de la notificación: {body}")
    
    tipo_evento = body.get("type")
    id_perfil_pagado_str = body.get("external_reference") 
    status_pago = body.get("status")

    if tipo_evento == "payment" and status_pago == "approved" and id_perfil_pagado_str:
        try:
            id_perfil_pagado = int(id_perfil_pagado_str)
            print(f"ANFITRIÓN WEBHOOK: ¡PAGO APROBADO (simulado) para el perfil {id_perfil_pagado}!")
            
            clientes_guardados = getattr(app.state, 'clientes_pendientes', {})
            cliente_pendiente = clientes_guardados.get(str(id_perfil_pagado))

            if not cliente_pendiente:
                print(f"ANFITRIÓN WEBHOOK ERROR: No se encontraron datos del cliente para el perfil {id_perfil_pagado} en {clientes_guardados}.")
                return {"status": "error, cliente no encontrado para ese perfil"}

            args_cliente = {"nombre": cliente_pendiente['nombre'], "telefono": cliente_pendiente['telefono']}
            id_cliente = mcp_call_tool(DB_MCP_SERVER_URL, "registrar_cliente", args_cliente)
            if not id_cliente:
                 print(f"ANFITRIÓN WEBHOOK ERROR: No se pudo registrar al cliente.")
                 enviar_mensaje_whatsapp(cliente_pendiente['telefono'], "Tuvimos un problema al procesar tu información de cliente. Por favor, contacta a soporte.")
                 return {"status": "error, registro cliente fallido"}
            print(f"ANFITRIÓN WEBHOOK: Cliente {cliente_pendiente['nombre']} registrado/actualizado con ID {id_cliente}")

            args_finalizar = {"id_cliente": id_cliente, "id_perfil": id_perfil_pagado}
            mcp_call_tool(DB_MCP_SERVER_URL, "finalizar_venta", args_finalizar)
            print(f"ANFITRIÓN WEBHOOK: Venta finalizada en la DB para perfil {id_perfil_pagado}.")

            args_credenciales = {"id_perfil": id_perfil_pagado}
            credenciales = mcp_call_tool(DB_MCP_SERVER_URL, "obtener_credenciales_perfil", args_credenciales)

            if credenciales:
                mensaje_whatsapp_final = (
                    f"¡Gracias por tu compra, {cliente_pendiente['nombre']}!\n"
                    f"Aquí están los datos de tu perfil para {cliente_pendiente.get('descripcion_compra', 'tu servicio')}:\n"
                    f"Correo: {credenciales.get('correo_asociado')}\n"
                    f"Contraseña: {credenciales.get('contraseña')}\n"
                    f"Perfil: {credenciales.get('nombre_perfil')}\n"
                    f"PIN: {credenciales.get('pin_perfil', 'No aplica')}\n\n"
                    f"¡Disfruta tu cuenta!"
                )
                enviar_mensaje_whatsapp(cliente_pendiente['telefono'], mensaje_whatsapp_final)
            else:
                print(f"ANFITRIÓN WEBHOOK ERROR: No se pudieron obtener las credenciales para el perfil {id_perfil_pagado}.")
                enviar_mensaje_whatsapp(cliente_pendiente['telefono'], "Hubo un problema al obtener tus credenciales después del pago. Por favor contacta a soporte.")
        except Exception as e_webhook:
            print(f"ANFITRIÓN WEBHOOK ERROR CRÍTICO: {e_webhook}")
            traceback.print_exc()
            id_perfil_str_temp = body.get("external_reference", "desconocido")
            cliente_info_temp = getattr(app.state, 'clientes_pendientes', {}).get(str(id_perfil_str_temp))
            if cliente_info_temp and cliente_info_temp.get('telefono'):
                enviar_mensaje_whatsapp(cliente_info_temp['telefono'], "Tuvimos un problema procesando el final de tu compra. Por favor, contacta a soporte.")
            return {"status": "error procesando webhook"}
    else:
        print(f"ANFITRIÓN WEBHOOK: Notificación no relevante o pago no aprobado. Tipo: {tipo_evento}, Estado: {status_pago}")
            
    return {"status": "webhook procesado"}