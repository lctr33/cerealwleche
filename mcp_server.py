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

def buscar_perfil_disponible(servicio: str, duracion: str):
    print(f"MCP_DB_SERVER DEBUG: Dentro de buscar_perfil_disponible. Servicio='{servicio}', Duracion='{duracion}'", flush=True)
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
            LIMIT 1;
        """
        cursor.execute(query, (servicio, duracion))
        perfil = cursor.fetchone()
        print(f"MCP_DB_SERVER DEBUG: Resultado de la consulta SQL para buscar_perfil_disponible: {perfil}", flush=True)
        return perfil
    except Exception as e:
        print(f"Error en buscar_perfil_disponible: {e}", flush=True)
        traceback.print_exc()
        return None
    finally:
        if conn and conn.is_connected():
            conn.close()

def listar_opciones_de_servicio(servicio: str):
    print(f"MCP_DB_SERVER DEBUG: Dentro de listar_opciones_de_servicio. Servicio='{servicio}'", flush=True)
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT p.tiempo_contratado, p.precio_mxn 
            FROM Precios p
            JOIN (SELECT DISTINCT nombre_servicio FROM Servicios_Streaming) AS s_ref
            ON p.nombre_servicio = s_ref.nombre_servicio
            WHERE p.nombre_servicio = %s
            ORDER BY p.precio_mxn;
        """
        cursor.execute(query, (servicio,))
        opciones = cursor.fetchall()
        print(f"MCP_DB_SERVER DEBUG: Opciones para '{servicio}': {opciones}", flush=True)
        return opciones
    except Exception as e:
        print(f"Error en listar_opciones_de_servicio: {e}", flush=True)
        traceback.print_exc()
        return []
    finally:
        if conn and conn.is_connected():
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

print("--- MCP_DB_SERVER: Funciones de herramientas cargadas. ---", flush=True)

# --- DEFINICIÓN DE HERRAMIENTAS MCP ---
tools_definition = {
    "tools": [
        {"name": "listar_servicios_disponibles", "description": "Obtiene una lista de todos los servicios de streaming que tienen perfiles disponibles para la venta.", "inputSchema": {"type": "object", "properties": {}}},
        {"name": "buscar_perfil_disponible", "description": "Busca un perfil disponible para un servicio y duración específicos, y devuelve su precio y ID.", "inputSchema": {"type": "object", "properties": {"servicio": {"type": "string"}, "duracion": {"type": "string"}}, "required": ["servicio", "duracion"]}},
        {"name": "listar_opciones_de_servicio", "description": "Obtiene una lista de todos los planes (duraciones y precios) disponibles para un servicio específico.", "inputSchema": {"type": "object", "properties": {"servicio": {"type": "string"}}, "required": ["servicio"]}},
        {"name": "registrar_cliente", "description": "Guarda o actualiza un cliente en la BD y devuelve su ID.", "inputSchema": {"type": "object", "properties": {"nombre": {"type": "string"}, "telefono": {"type": "string"}}, "required": ["nombre", "telefono"]}},
        {"name": "finalizar_venta", "description": "Marca un perfil como vendido y lo asocia a un cliente.", "inputSchema": {"type": "object", "properties": {"id_cliente": {"type": "integer"}, "id_perfil": {"type": "integer"}}, "required": ["id_cliente", "id_perfil"]}},
        {"name": "obtener_credenciales_perfil", "description": "Obtiene el correo, contraseña, nombre de perfil y pin de un perfil vendido.", "inputSchema": {"type": "object", "properties": {"id_perfil": {"type": "integer"}}, "required": ["id_perfil"]}}
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
                result = buscar_perfil_disponible(servicio=args.get("servicio"), duracion=args.get("duracion"))
            elif tool_name == "listar_opciones_de_servicio":
                result = listar_opciones_de_servicio(servicio=args.get("servicio"))
            elif tool_name == "registrar_cliente":
                result = registrar_cliente(nombre=args.get("nombre"), telefono=args.get("telefono"))
            elif tool_name == "finalizar_venta":
                result = finalizar_venta(id_cliente=args.get("id_cliente"), id_perfil=args.get("id_perfil"))
            elif tool_name == "obtener_credenciales_perfil":
                result = obtener_credenciales_perfil(id_perfil=args.get("id_perfil"))
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