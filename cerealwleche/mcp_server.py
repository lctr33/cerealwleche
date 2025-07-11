# mcp_server.py

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import mysql.connector
import os
import sys # Para sys.stdout.flush()
import traceback # Para imprimir tracebacks completos
# --- CONFIGURACIÓN DE BASE DE DATOS ---
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'cereal-with-leche'),
    'password': os.getenv('DB_PASSWORD', 'bryanesgei'),
    'database': os.getenv('DB_NAME', 'streaming_profiles')
}

print("--- MCP_DB_SERVER: Cargando funciones de herramientas... ---", flush=True)

# --- LÓGICA DE HERRAMIENTAS (FUNCIONES DE BASE DE DATOS) ---

def listar_servicios_disponibles():
    print("MCP_DB_SERVER DEBUG: Dentro de listar_servicios_disponibles", flush=True)
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = "SELECT DISTINCT s.nombre_servicio FROM Perfiles_Streaming p JOIN Servicios_Streaming s ON p.id_servicio = s.id_servicio WHERE p.libre = 1 ORDER BY s.nombre_servicio;"
        cursor.execute(query)
        servicios = [item[0] for item in cursor.fetchall()]
        print(f"MCP_DB_SERVER DEBUG: Servicios disponibles encontrados: {servicios}", flush=True)
        return servicios
    except Exception as e:
        print(f"Error en listar_servicios_disponibles: {e}", flush=True)
        traceback.print_exc()
        return []
    finally:
        if conn and conn.is_connected():
            conn.close()

def buscar_perfil_disponible(servicio: str, duracion: str, cantidad: int = 1):
    print(f"MCP_DB_SERVER DEBUG: Dentro de buscar_perfil_disponible. Servicio='{servicio}', Duracion='{duracion}', Cantidad={cantidad}", flush=True)
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT p.id_perfil, s.nombre_servicio, pr.precio_mxn 
            FROM Perfiles_Streaming p
            JOIN Servicios_Streaming s ON p.id_servicio = s.id_servicio 
            JOIN Precios pr ON s.nombre_servicio = pr.nombre_servicio 
            WHERE s.nombre_servicio = %s AND pr.tiempo_contratado = %s AND p.libre = 1 
            LIMIT %s;
        """
        cursor.execute(query, (servicio, duracion, cantidad))
        perfiles = cursor.fetchall()
        print(f"MCP_DB_SERVER DEBUG: Resultado de la consulta SQL para buscar_perfil_disponible: {perfiles}", flush=True)
        return perfiles
    except Exception as e:
        print(f"Error en buscar_perfil_disponible: {e}", flush=True)
        traceback.print_exc()
        return None
    finally:
        if conn and conn.is_connected():
            conn.close()

def listar_precios_de_servicio(servicio=None):
    """
    Obtiene los precios para uno, varios, o todos los servicios.
    - Si 'servicio' es None, devuelve los precios de todos los servicios.
    - Si 'servicio' es un string (ej: 'netflix'), devuelve los precios para ese servicio.
    - Si 'servicio' es una lista (ej: ['netflix', 'max']), devuelve los precios para esos servicios.
    """
    print(f"MCP_DB_SERVER DEBUG: Dentro de listar_precios_de_servicio. Servicio='{servicio}'", flush=True)
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # 1. Preparamos la consulta SQL base
        query = "SELECT idNombreServicio, precio1Mes, precio2Meses, precio3Meses, precio6Meses, precio1Anio FROM Precios"
        params = []

        # 2. Añadimos el filtro WHERE dinámicamente si es necesario
        if servicio is not None:
            # Nos aseguramos de que siempre trabajemos con una lista
            servicios_a_consultar = servicio if isinstance(servicio, list) else [servicio]
            
            if len(servicios_a_consultar) > 0:
                # Creamos los placeholders (%s) necesarios para la cláusula IN
                placeholders = ', '.join(['%s'] * len(servicios_a_consultar))
                query += f" WHERE idNombreServicio IN ({placeholders})"
                params.extend(servicios_a_consultar)

        # 3. Ejecutamos una ÚNICA consulta a la base de datos
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        
        # 4. Procesamos los resultados en Python
        resultados = {}
        for row in rows:
            nombre_servicio = row['idNombreServicio']
            opciones = []
            
            # Mapeamos los nombres de las columnas a un formato legible
            mapa_precios = {
                "1 Mes": row.get('precio1Mes'),
                "2 Meses": row.get('precio2Meses'),
                "3 Meses": row.get('precio3Meses'),
                "6 Meses": row.get('precio6Meses'),
                "1 Año": row.get('precio1Anio')
            }
            
            # Añadimos solo las opciones que tienen un precio definido
            for tiempo, precio in mapa_precios.items():
                if precio is not None:
                    opciones.append({"tiempo_contratado": tiempo, "precio_mxn": precio})
            
            resultados[nombre_servicio] = opciones
            
        print(f"MCP_DB_SERVER DEBUG: Precios consultados: {resultados}", flush=True)
        return resultados

    except Exception as e:
        print(f"Error en listar_precios_de_servicio: {e}", flush=True)
        traceback.print_exc()
        return {}
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def registrar_cliente(nombre: str, telefono: str):
    print(f"MCP_DB_SERVER DEBUG: Iniciando registrar_cliente. Nombre='{nombre}', Telefono='{telefono}'", flush=True)
    conn = None
    id_cliente_final = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        placeholders_telefono = ['messenger', 'ninguno', None, '']
        cliente_existente = None

        if telefono and telefono.strip().lower() not in placeholders_telefono:
            print(f"MCP_DB_SERVER DEBUG: Buscando cliente por telefono='{telefono}'", flush=True)
            cursor.execute("SELECT id_cliente, nombre FROM Clientes WHERE numero_tel = %s LIMIT 1", (telefono,))
            cliente_existente = cursor.fetchone()

        if cliente_existente:
            id_cliente_final = cliente_existente['id_cliente']
            print(f"MCP_DB_SERVER DEBUG: Cliente encontrado por telefono. ID: {id_cliente_final}, Nombre DB: '{cliente_existente['nombre']}', Nombre Nuevo: '{nombre}'", flush=True)
            if cliente_existente['nombre'] != nombre:
                cursor.execute("UPDATE Clientes SET nombre = %s WHERE id_cliente = %s", (nombre, id_cliente_final))
                conn.commit()
                print(f"MCP_DB_SERVER DEBUG: Nombre del cliente ID {id_cliente_final} actualizado a '{nombre}'.", flush=True)
        else:
            print(f"MCP_DB_SERVER DEBUG: No se encontró cliente con telefono '{telefono}' (o es placeholder). Insertando nuevo.", flush=True)
            cursor.execute("INSERT INTO Clientes (nombre, numero_tel) VALUES (%s, %s)", (nombre, telefono))
            conn.commit()
            id_cliente_final = cursor.lastrowid
            print(f"MCP_DB_SERVER DEBUG: Nuevo cliente insertado. ID: {id_cliente_final}", flush=True)
        
        if id_cliente_final == 0 and cliente_existente:
             id_cliente_final = cliente_existente['id_cliente']
        
        if not id_cliente_final or id_cliente_final == 0:
             print(f"MCP_DB_SERVER DEBUG: No se pudo obtener un ID de cliente válido para '{nombre}', '{telefono}'", flush=True)
             return None
        
        print(f"MCP_DB_SERVER DEBUG: registrar_cliente devuelve: {id_cliente_final}", flush=True)
        return id_cliente_final
    except Exception as e:
        print(f"Error GRAVE en registrar_cliente: {e}", flush=True)
        traceback.print_exc()
        return None
    finally:
        if conn and conn.is_connected():
            conn.close()

def finalizar_venta(id_cliente: int, id_perfil: int):
    print(f"MCP_DB_SERVER DEBUG: Iniciando finalizar_venta. id_cliente={id_cliente}, id_perfil={id_perfil}", flush=True)
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = "UPDATE Perfiles_Streaming SET libre = 0, id_cliente = %s WHERE id_perfil = %s;"
        cursor.execute(query, (id_cliente, id_perfil))
        conn.commit()
        print(f"MCP_DB_SERVER DEBUG: Perfil {id_perfil} marcado como vendido al cliente {id_cliente}.", flush=True)
        return True
    except Exception as e:
        print(f"Error en finalizar_venta: {e}", flush=True)
        traceback.print_exc()
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()

def obtener_credenciales_perfil(id_perfil: int):
    print(f"MCP_DB_SERVER DEBUG: Iniciando obtener_credenciales_perfil para id_perfil={id_perfil}", flush=True)
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                ss.correo_asociado, 
                ss.contraseña, 
                ps.nombre_perfil, 
                ps.pin_perfil 
            FROM Perfiles_Streaming ps
            JOIN Servicios_Streaming ss ON ps.id_servicio = ss.id_servicio 
            WHERE ps.id_perfil = %s;
        """
        cursor.execute(query, (id_perfil,))
        credenciales = cursor.fetchone()
        print(f"MCP_DB_SERVER DEBUG: Credenciales encontradas para perfil {id_perfil}: {credenciales is not None}", flush=True)
        return credenciales
    except Exception as e:
        print(f"Error en obtener_credenciales_perfil: {e}", flush=True)
        traceback.print_exc()
        return None
    finally:
        if conn and conn.is_connected():
            conn.close()

def buscar_estatus_chat(numero_del_chat: str):
    """
    Busca el estado de un chat en la tabla de compras pendientes.
    """
    print(f"MCP_DB_SERVER DEBUG: Iniciando buscar_estatus_chat para numero_del_chat='{numero_del_chat}'", flush=True)
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        # La tabla se llama 'Compras_pendientes' y la columna de teléfono 'numero_tel'
        query = "SELECT estatus, informacion_de_la_compra FROM Compras_pendientes WHERE numero_tel = %s;"
        cursor.execute(query, (numero_del_chat,))
        resultado = cursor.fetchone() # Usamos fetchone porque el numero_tel es PK
        print(f"MCP_DB_SERVER DEBUG: Estatus encontrado para '{numero_del_chat}': {resultado}", flush=True)
        return resultado # Será el diccionario con los datos o None si no se encuentra
    except Exception as e:
        print(f"Error en buscar_estatus_chat: {e}", flush=True)
        traceback.print_exc()
        return None # Devolvemos None en caso de error
    finally:
        if conn and conn.is_connected():
            conn.close()

def ingresar_estatus_chat(numero_del_chat: str, estatus: str, informacion: str):
                print(f"MCP_DB_SERVER DEBUG: Iniciando ingresar_estatus_chat para numero_del_chat='{numero_del_chat}', estatus='{estatus}', informacion='{informacion}'", flush=True)
                conn = None
                try:
                    conn = mysql.connector.connect(**db_config)
                    cursor = conn.cursor()

                    query = """
                        INSERT INTO Compras_pendientes (numero_tel, estatus, informacion_de_la_compra)
                        VALUES (%s, %s, %s);
                    """
                    cursor.execute(query, (numero_del_chat, estatus, informacion))
                    conn.commit()

                    print(f"MCP_DB_SERVER DEBUG: Ingreso exitoso del chat '{numero_del_chat}' con estatus='{estatus}'.", flush=True)
                    return True

                except Exception as e:
                    print(f"Error en ingresar_estatus_chat: {e}", flush=True)
                    if conn:
                        conn.rollback()
                    traceback.print_exc()
                    return False

                finally:
                    if conn and conn.is_connected():
                        conn.close()           

def modificar_estatus_chat(numero_del_chat: str, nuevo_estatus: str, nueva_informacion: str):
    """
    Modifica el estatus y la información de la compra para un chat pendiente.

    Args:
        numero_del_chat (str): El número de teléfono que actúa como PK.
        nuevo_estatus (str): El nuevo valor para la columna 'estatus'.
        nueva_informacion (str): El nuevo valor para la columna 'informacion_de_la_compra'.

    Returns:
        bool: True si la actualización fue exitosa, False en caso de error.
    """
    print(f"MCP_DB_SERVER DEBUG: Modificando chat '{numero_del_chat}' a estatus='{nuevo_estatus}' e info='{nueva_informacion}'", flush=True)
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        query = """
            UPDATE Compras_pendientes 
            SET estatus = %s, informacion_de_la_compra = %s 
            WHERE numero_tel = %s;
        """
        
        cursor.execute(query, (nuevo_estatus, nueva_informacion, numero_del_chat))
        conn.commit()
        
        # cursor.rowcount devuelve el número de filas afectadas. Si es > 0, la actualización funcionó.
        if cursor.rowcount > 0:
            print(f"MCP_DB_SERVER DEBUG: Chat '{numero_del_chat}' actualizado correctamente.", flush=True)
            return True
        else:
            print(f"MCP_DB_SERVER WARNING: No se encontró el chat '{numero_del_chat}' para actualizar.", flush=True)
            # También podría ser que los valores nuevo_estatus y nueva_informacion sean idénticos a los existentes.
            # En muchos casos, esto no se considera un fallo. Devolvemos True porque el estado final es el deseado.
            return True

    except Exception as e:
        print(f"Error en modificar_estatus_chat: {e}", flush=True)
        if conn:
            conn.rollback() # Revertir cambios en caso de error
        traceback.print_exc()
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()

print("--- MCP_DB_SERVER: Funciones de herramientas cargadas. ---", flush=True)

# --- DEFINICIÓN DE HERRAMIENTAS MCP ---
tools_definition = {
    "tools": [
        {"name": "listar_servicios_disponibles", "description": "Obtiene una lista de todos los servicios de streaming que tienen perfiles disponibles para la venta.", "inputSchema": {"type": "object", "properties": {}}},
        {"name": "buscar_perfil_disponible", "description": "Busca uno o varios perfiles disponibles para un servicio y duración específicos, y devuelve su precio e ID.", "inputSchema": {"type": "object", "properties": {"servicio": {"type": "string"}, "duracion": {"type": "string"}, "cantidad": {"type": "integer", "default": 1}}, "required": ["servicio", "duracion"]}},
        {"name": "listar_precios_de_servicio", "description": "Obtiene una lista de todos los planes (duraciones y precios) disponibles para un servicio específico.", "inputSchema": {"type": "object", "properties": {"servicio": {"type": "string"}}, "required": ["servicio"]}},
        {"name": "registrar_cliente", "description": "Guarda o actualiza un cliente en la BD y devuelve su ID.", "inputSchema": {"type": "object", "properties": {"nombre": {"type": "string"}, "telefono": {"type": "string"}}, "required": ["nombre", "telefono"]}},
        {"name": "finalizar_venta", "description": "Marca un perfil como vendido y lo asocia a un cliente.", "inputSchema": {"type": "object", "properties": {"id_cliente": {"type": "integer"}, "id_perfil": {"type": "integer"}}, "required": ["id_cliente", "id_perfil"]}},
        {"name": "obtener_credenciales_perfil", "description": "Obtiene el correo, contraseña, nombre de perfil y pin de un perfil vendido.", "inputSchema": {"type": "object", "properties": {"id_perfil": {"type": "integer"}}, "required": ["id_perfil"]}},
        {"name": "buscar_estatus_chat", "description": "Busca el estado actual y la información de una compra pendiente asociada a un número de chat o teléfono.", "inputSchema": {"type": "object", "properties": {"numero_del_chat": {"type": "string"}}, "required": ["numero_del_chat"]}},
        {"name": "modificar_estatus_chat", "description": "Modifica el estatus y la información de una compra pendiente asociada a un número de chat o teléfono.", "inputSchema": {"type": "object", "properties": {"numero_del_chat": {"type": "string"}, "nuevo_estatus": {"type": "string"}, "nueva_informacion": {"type": "string"}}, "required": ["numero_del_chat", "nuevo_estatus", "nueva_informacion"]}},
        {"name": "ingresar_estatus_chat", "description": "Ingresa un nuevo chat pendiente con su estatus e información de compra.", "inputSchema": {"type": "object", "properties": {"numero_del_chat": {"type": "string"}, "estatus": {"type": "string"}, "informacion": {"type": "string"}}, "required": ["numero_del_chat", "estatus", "informacion"]}}
    ]

}
print("--- MCP_DB_SERVER: Definición de herramientas cargada. ---", flush=True)

# --- LÓGICA DEL SERVIDOR MCP ---
class MCPServerHandler(BaseHTTPRequestHandler):
    def _send_response(self, status_code, content):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(content, default=str).encode('utf-8')) # default=str para Decimals

    def do_POST(self):
        print(f"MCP_DB_SERVER: MCPServerHandler.do_POST FUE LLAMADO para path: {self.path}", flush=True)
        if self.path == '/tools/list':
            self._send_response(200, tools_definition)
        elif self.path == '/tools/call':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            payload = json.loads(post_data)
            tool_name = payload.get("toolName")
            args = payload.get("arguments", {})
            print(f"MCP_DB_SERVER: Petición 'tools/call' para '{tool_name}' con args {args}", flush=True)
            
            result = None
            if tool_name == "listar_servicios_disponibles":
                result = listar_servicios_disponibles()
            elif tool_name == "buscar_perfil_disponible":
                result = buscar_perfil_disponible(servicio=args.get("servicio"), duracion=args.get("duracion"), cantidad=args.get("cantidad", 1))
            elif tool_name == "listar_precios_de_servicio":
                result = listar_precios_de_servicio(servicio=args.get("servicio"))
            elif tool_name == "registrar_cliente":
                result = registrar_cliente(nombre=args.get("nombre"), telefono=args.get("telefono"))
            elif tool_name == "finalizar_venta":
                result = finalizar_venta(id_cliente=args.get("id_cliente"), id_perfil=args.get("id_perfil"))
            elif tool_name == "obtener_credenciales_perfil":
                result = obtener_credenciales_perfil(id_perfil=args.get("id_perfil"))
            elif tool_name == "buscar_estatus_chat":
                result = buscar_estatus_chat(numero_del_chat=args.get("numero_del_chat"))
            elif tool_name == "modificar_estatus_chat":
                result = modificar_estatus_chat(
                    numero_del_chat=args.get("numero_del_chat"),
                    nuevo_estatus=args.get("nuevo_estatus"),
                    nueva_informacion=args.get("nueva_informacion")
                )
            elif tool_name == "ingresar_estatus_chat":
                result = ingresar_estatus_chat(
                    numero_del_chat=args.get("numero_del_chat"),
                    estatus=args.get("estatus"),
                    informacion=args.get("informacion")
                )
            else:
                print(f"MCP_DB_SERVER: Herramienta desconocida '{tool_name}'", flush=True)
            
            self._send_response(200, {"content": result})
        else:
            self._send_response(404, {"error": "Path Not Found"})

def run_server(port=8001):
    server_address = ('', port)
    httpd = HTTPServer(server_address, MCPServerHandler)
    print(f"--- MCP_DB_SERVER: Servidor HTTP iniciado en el puerto {port} ---", flush=True)
    sys.stdout.flush() # Doble seguridad
    httpd.serve_forever()

if __name__ == '__main__':
    print("--- MCP_DB_SERVER: Bloque if __name__ == '__main__' ALCANZADO ---", flush=True)
    sys.stdout.flush()
    run_server()
    print("--- MCP_DB_SERVER: run_server() terminó (esto no debería pasar si serve_forever funciona). ---", flush=True)
    sys.stdout.flush()