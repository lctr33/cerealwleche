# main.py (con prints de depuración para app.state)

import os
import requests
import json
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Literal
import traceback # Para imprimir el traceback completo en caso de error

# --- Arquitectura LangChain ---
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

# --- URLs de los Servidores MCP (leídas de variables de entorno) ---
DB_MCP_SERVER_URL = os.getenv("DB_MCP_SERVER_URL", "http://localhost:8001")
WHATSAPP_MCP_SERVER_URL = os.getenv("WHATSAPP_MCP_SERVER_URL", "http://localhost:8002/mcp/") # Con /mcp/

# --- Modelo Pydantic para la salida del LLM ---
class SolicitudUsuario(BaseModel):
    intencion: Literal[
        "comprar_servicio", 
        "consultar_disponibilidad", 
        "consultar_opciones_de_servicio",
        "desconocido"
    ] = Field(description="La intención clasificada del usuario.")
    servicio: str | None = Field(description="El servicio de streaming que el usuario quiere.")
    tiempo_contratado: str | None = Field(description="La duración del contrato, si se especifica.")

pydantic_parser = PydanticOutputParser(pydantic_object=SolicitudUsuario)

# --- Prompt para el LLM ---
# (Asegúrate de que este prompt_template_text sea el que tiene los {{ }} para los ejemplos JSON)
prompt_template_text = """
    Eres un asistente experto en procesar pedidos para un servicio de venta de cuentas de streaming.
    Tu unica tarea es analizar el texto del usuario para clasificar su 'intencion' y extraer los datos 'servicio' y 'tiempo_contratado' si aplican.

    Reglas estrictas que debes seguir:
    1.  Intenciones Validas: 'comprar_servicio', 'consultar_disponibilidad', 'consultar_opciones_de_servicio'.
    2.  Clasificacion:
        - Si el usuario pide un servicio Y duracion, la intencion es 'comprar_servicio'.
        - Si pregunta de forma general ('que tienes', 'lista de servicios'), la intencion es 'consultar_disponibilidad'.
        - Si pregunta por un servicio especifico pero SIN duracion ('tienes netflix?', 'info de max'), la intencion es 'consultar_opciones_de_servicio'.
    3.  Servicios Validos: {lista_servicios_validos}. Si se menciona otro, usa 'desconocido'.
    4.  Duracion por Defecto: Si la intencion es 'comprar_servicio' y no se especifica duracion, asume '1_mes'.
    5.  Formato de Salida: Tu respuesta DEBE SER UNICAMENTE un objeto JSON valido, usando exactamente las claves 'intencion', 'servicio' y 'tiempo_contratado' (SIN TILDES).

    Ejemplo 1 (Compra):
    Texto del usuario: "hola, me interesa una cuenta de crunchyroll por un año porfa"
    Tu respuesta:
    {{{{ "intencion": "comprar_servicio", "servicio": "crunchyroll", "tiempo_contratado": "1_año" }}}}

    Ejemplo 2 (Consulta General):
    Texto del usuario: "hola, que cuentas manejas?"
    Tu respuesta:
    {{{{ "intencion": "consultar_disponibilidad", "servicio": null, "tiempo_contratado": null }}}}
    
    Ejemplo 3 (Consulta de Opciones):
    Texto del usuario: "hola, que planes tienes para max?"
    Tu respuesta:
    {{{{ "intencion": "consultar_opciones_de_servicio", "servicio": "max", "tiempo_contratado": null }}}}
    
    ---
    Texto del usuario:
    {texto_usuario}
    """

# --- Funciones de Ayuda ---
json_rpc_request_id_counter = 0

def get_llm(provider: str = "ollama"):
    ollama_base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY no encontrada en variables de entorno.")
        return ChatOpenAI(model="gpt-3.5-turbo", openai_api_key=api_key)
    return ChatOllama(model="llama3:8b", base_url=ollama_base_url)

def mcp_call_tool(server_url: str, mcp_protocol_method: str, params_or_arguments: dict = {}, is_json_rpc_server: bool = False):
    global json_rpc_request_id_counter
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    try:
        if is_json_rpc_server:
            json_rpc_request_id_counter += 1
            payload = {"jsonrpc": "2.0", "method": mcp_protocol_method, "id": f"mcp-{mcp_protocol_method.replace('/', '-')}-{json_rpc_request_id_counter}"}
            if mcp_protocol_method == "tools/call" and params_or_arguments:
                payload["params"] = params_or_arguments
            effective_url = server_url
        else:
            payload = {"toolName": mcp_protocol_method, "arguments": params_or_arguments}
            effective_url = f"{server_url}/tools/call"
        print(f"ANFITRIÓN DEBUG (mcp_call_tool): Enviando a {effective_url}, Payload: {json.dumps(payload)}")
        response = requests.post(effective_url, json=payload, headers=headers)
        response.raise_for_status()
        json_response = response.json()
        print(f"ANFITRIÓN DEBUG (mcp_call_tool): Respuesta JSON de {effective_url}: {json.dumps(json_response)}")
        if is_json_rpc_server:
            if "error" in json_response:
                print(f"Error JSON-RPC del servidor: {json_response['error']}")
                return None
            result = json_response.get("result")
            if mcp_protocol_method == "tools/call": return result.get("content") if result else None
            return result
        else:
            return json_response.get("content")
    except requests.RequestException as e:
        print(f"Error en requests llamando a MCP en {server_url} con método/herramienta {mcp_protocol_method}: {e}")
        if 'response' in locals() and response is not None: print(f"Respuesta del servidor: {response.text}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decodificando JSON de MCP en {server_url} para {mcp_protocol_method}: {e}")
        if 'response' in locals() and response is not None: print(f"Respuesta cruda del servidor: {response.text}")
        return None
    except Exception as e:
        print(f"Error inesperado en mcp_call_tool para {mcp_protocol_method}: {e}")
        traceback.print_exc()
        return None

# --- Función de ayuda para enviar mensajes de WhatsApp ---
# En main.py

def enviar_mensaje_whatsapp(telefono_destinatario: str, texto_mensaje: str):
    """Envía un mensaje de WhatsApp usando el servidor MCP de WhatsApp."""
    print(f"ANFITRIÓN: Preparando para enviar WhatsApp a {telefono_destinatario}: '{texto_mensaje}'")
    if not telefono_destinatario or not texto_mensaje:
        print("ANFITRIÓN ERROR: Teléfono o mensaje vacío para WhatsApp.")
        return False

    destinatario_jid_wa = f"{telefono_destinatario.replace('+', '')}@s.whatsapp.net"
    params_para_wa_send_message = {
        "name": "send_message", 
        "arguments": {"recipient": destinatario_jid_wa, "message": texto_mensaje}
    }

    print(f"ANFITRIÓN: Llamando a WHATSAPP MCP 'tools/call' con payload para 'params': {params_para_wa_send_message}")
    resultado_wa = mcp_call_tool(
        server_url=WHATSAPP_MCP_SERVER_URL, 
        mcp_protocol_method="tools/call",
        params_or_arguments=params_para_wa_send_message, 
        is_json_rpc_server=True
    )

    # --- LÓGICA DE VERIFICACIÓN CORREGIDA ---
    try:
        # La respuesta es una lista, tomamos el primer elemento
        if isinstance(resultado_wa, list) and len(resultado_wa) > 0:
            primer_elemento = resultado_wa[0]
            # El contenido real es un string JSON dentro de la clave 'text'
            if isinstance(primer_elemento, dict) and 'text' in primer_elemento:
                respuesta_interna_str = primer_elemento['text']
                # Parseamos ese string JSON para obtener el estado final
                respuesta_interna_json = json.loads(respuesta_interna_str)
                if respuesta_interna_json.get("success"):
                    print(f"ANFITRIÓN: Mensaje de WhatsApp enviado exitosamente a {destinatario_jid_wa}. Respuesta del servidor: {respuesta_interna_json.get('message')}")
                    return True
    except Exception as e:
        print(f"ANFITRIÓN: Error parseando la respuesta del servidor de WhatsApp: {e}")

    print(f"ANFITRIÓN: Falló el envío del mensaje de WhatsApp a {destinatario_jid_wa}. Respuesta cruda: {resultado_wa}")
    return False

# --- FastAPI App ---
app = FastAPI(title="Agente de Ventas vFINAL - Con WhatsApp y MCP")
# --- INICIALIZACIÓN DE app.state.clientes_pendientes ---
app.state.clientes_pendientes = {} 

class MensajeChat(BaseModel):
    texto: str
    telefono_cliente: str 
    nombre_cliente: str = "Cliente Test"

@app.post("/chat")
def procesar_mensaje_de_chat(mensaje: MensajeChat, llm_provider: str = "ollama"):
    print(f"\n--- ANFITRIÓN: Petición a /chat por '{mensaje.telefono_cliente}' con '{mensaje.texto}' ---")
    # --- DEBUG: Imprimir estado de clientes_pendientes AL INICIO de /chat ---
    print(f"ANFITRIÓN CHAT (antes de procesar): app.state.clientes_pendientes actual es: {getattr(app.state, 'clientes_pendientes', {})}")
    
    respuesta_texto_para_cliente = "Lo siento, no pude procesar tu solicitud en este momento."
    try:
        servicios_activos_db_response = mcp_call_tool(DB_MCP_SERVER_URL, "listar_servicios_disponibles")
        if not servicios_activos_db_response:
            print("ANFITRIÓN ERROR: No se pudieron obtener los servicios válidos de la DB MCP.")
            respuesta_texto_para_cliente = "Lo siento, no puedo determinar los servicios disponibles en este momento."
            enviar_mensaje_whatsapp(mensaje.telefono_cliente, respuesta_texto_para_cliente)
            return {"status": "error", "detalle": "No se pudieron obtener servicios de DB"}
        
        lista_servicios_para_prompt = ', '.join([f"'{s}'" for s in servicios_activos_db_response])
        formatted_prompt_text = prompt_template_text.format(
            lista_servicios_validos=lista_servicios_para_prompt,
            texto_usuario=mensaje.texto,
            format_instructions=pydantic_parser.get_format_instructions()
        )
        final_prompt = PromptTemplate(template=formatted_prompt_text, input_variables=[])

        llm = get_llm(provider=llm_provider)
        chain = final_prompt | llm | pydantic_parser
        resultado_llm = chain.invoke({})
        
        intencion = resultado_llm.intencion
        servicio_extraido = resultado_llm.servicio
        tiempo_contratado_extraido = resultado_llm.tiempo_contratado
        print(f"ANFITRIÓN: LangChain extrajo -> Intención: {intencion}, Servicio: {servicio_extraido}, Duración: {tiempo_contratado_extraido}")

        if intencion == "comprar_servicio":
            if not servicio_extraido or servicio_extraido == "desconocido" or servicio_extraido not in servicios_activos_db_response:
                 respuesta_texto_para_cliente = f"No entendí qué servicio deseas o no lo manejo. Servicios disponibles: {', '.join([s.capitalize() for s in servicios_activos_db_response])}."
            else:
                args_busqueda = {"servicio": servicio_extraido, "duracion": tiempo_contratado_extraido}
                perfil = mcp_call_tool(DB_MCP_SERVER_URL, "buscar_perfil_disponible", args_busqueda)
                if not perfil:
                    respuesta_texto_para_cliente = f"Lo siento, no tengo perfiles de {servicio_extraido.capitalize()} por {tiempo_contratado_extraido.replace('_',' ')}."
                else:
                    precio_mxn = float(perfil['precio_mxn'])
                    link_pago_simulado = f"http://mercadopago.simulado.com/pagar?item={perfil['nombre_servicio']}&precio={precio_mxn}&id_perfil={perfil['id_perfil']}"
                    
                    # Asegurarse de que app.state.clientes_pendientes exista
                    if not hasattr(app.state, 'clientes_pendientes') or app.state.clientes_pendientes is None:
                        app.state.clientes_pendientes = {}
                    
                    app.state.clientes_pendientes[str(perfil['id_perfil'])] = {
                        "nombre": mensaje.nombre_cliente,
                        "telefono": mensaje.telefono_cliente,
                        "servicio_comprado": perfil['nombre_servicio'],
                        "descripcion_compra": f"Perfil {perfil['nombre_servicio'].capitalize()} - {tiempo_contratado_extraido.replace('_', ' ')}"
                    }
                    # --- DEBUG: Imprimir estado de clientes_pendientes DESPUÉS de guardar ---
                    print(f"ANFITRIÓN CHAT (después de guardar): app.state.clientes_pendientes ahora es: {app.state.clientes_pendientes}")
                    respuesta_texto_para_cliente = f"¡Perfecto! Para pagar tu {perfil['nombre_servicio'].capitalize()} (${precio_mxn:.2f} MXN), usa este enlace: {link_pago_simulado}"

        elif intencion == "consultar_disponibilidad":
            lista_formateada = ", ".join([s.capitalize() for s in servicios_activos_db_response])
            respuesta_texto_para_cliente = f"¡Claro! Vía MCP, tengo perfiles para: {lista_formateada}."
        
        elif intencion == "consultar_opciones_de_servicio":
            if not servicio_extraido or servicio_extraido == "desconocido" or servicio_extraido not in servicios_activos_db_response:
                respuesta_texto_para_cliente = "Claro, dime de qué servicio te gustaría saber los precios. Ofrezco: " + ", ".join([s.capitalize() for s in servicios_activos_db_response])
            else:
                args_opciones = {"servicio": servicio_extraido}
                opciones = mcp_call_tool(DB_MCP_SERVER_URL, "listar_opciones_de_servicio", args_opciones)
                if not opciones:
                    respuesta_texto_para_cliente = f"Lo siento, no encontré planes de precios para {servicio_extraido.capitalize()}."
                else:
                    respuesta_formateada_planes = f"¡Sí, claro! Para {servicio_extraido.capitalize()} tengo los siguientes planes:\n"
                    for opcion in opciones:
                        precio_como_numero = float(opcion['precio_mxn'])
                        plan = f" - {opcion['tiempo_contratado'].replace('_', ' ')} por ${precio_como_numero:.2f} MXN\n"
                        respuesta_formateada_planes += plan
                    respuesta_texto_para_cliente = respuesta_formateada_planes.strip()
        else: 
            respuesta_texto_para_cliente = "No estoy seguro de cómo ayudarte con eso. Puedo buscarte una cuenta o decirte cuáles tengo disponibles."

        enviar_mensaje_whatsapp(mensaje.telefono_cliente, respuesta_texto_para_cliente)
        return {"status": "respuesta enviada a WhatsApp", "respuesta_generada": respuesta_texto_para_cliente}

    except Exception as e:
        print(f"Ha ocurrido un error crítico en el Anfitrión: {e}")
        traceback.print_exc()
        if hasattr(mensaje, 'telefono_cliente') and mensaje.telefono_cliente:
             enviar_mensaje_whatsapp(mensaje.telefono_cliente, "Lo siento, ocurrió un error interno y no puedo procesar tu solicitud en este momento.")
        raise HTTPException(status_code=500, detail=f"Error procesando la solicitud: {str(e)}")

# Webhook para Mercado Pago
@app.post("/webhook/mercadopago")
async def webhook_mercadopago(request: Request): 
    print(f"ANFITRIÓN WEBHOOK: Notificación de MercadoPago recibida.")
    # --- DEBUG: Imprimir estado de clientes_pendientes AL INICIO del webhook ---
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
            
            # Asegurarse de que app.state.clientes_pendientes exista antes de acceder
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