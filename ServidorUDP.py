import socket
import threading
import time
import os
import platform

# Lista de clientes (en UDP guardamos direcciones en lugar de conexiones)
clientes = {}  # {(ip, puerto): {"alias": alias, "last_seen": timestamp}}
servidor = None  # Declaración global del socket
server_running = True  # Flag para controlar si el servidor está activo

def limpiar_pantalla():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def broadcast(mensaje, remitente=None, is_system=False):
    """Envía un mensaje a todos los clientes excepto al remitente"""
    global servidor, server_running
    
    # No hacer broadcast si el servidor está cerrando
    if not server_running:
        return
        
    mensaje_bytes = mensaje.encode('utf-8')
    
    # Clientes a eliminar (expirados)
    expirados = []
    
    for direccion, info in list(clientes.items()):  # Usamos list() para evitar modificar durante iteración
        # No enviar al remitente a menos que sea un mensaje del sistema
        if direccion != remitente or is_system:
            try:
                servidor.sendto(mensaje_bytes, direccion)
            except Exception as e:
                print(f"[ERROR] Error al enviar a {info['alias']}: {e}")
                expirados.append(direccion)
    
    # Eliminar clientes expirados
    for direccion in expirados:
        if direccion in clientes:
            alias = clientes[direccion]['alias']
            print(f"[TIMEOUT] {alias} ha expirado por inactividad desde {direccion}")
            del clientes[direccion]
            # Evitamos llamadas recursivas infinitas
            if len(clientes) > 0 and server_running:
                mensaje_sistema = f"[SYSTEM] {alias} ha salido (timeout)"
                broadcast(mensaje_sistema, None, True)  # Llamada con is_system=True

def mostrar_usuarios_conectados():
    """Muestra la lista de usuarios conectados"""
    usuarios = [info['alias'] for info in clientes.values()]
    if usuarios:
        print(f"[USERS] Total: {len(usuarios)} - {', '.join(usuarios)}")
    else:
        print("[USERS] No hay usuarios conectados")

def limpiar_clientes_inactivos():
    """Elimina periódicamente los clientes inactivos"""
    global server_running
    while server_running:
        try:
            tiempo_actual = time.time()
            expirados = []
            
            # Usar una copia del diccionario para evitar errores de modificación durante iteración
            for direccion, info in list(clientes.items()):
                # Aumentado a 30 segundos para ser más tolerante con la red
                if tiempo_actual - info['last_seen'] > 30:  # 30 segundos sin actividad
                    expirados.append(direccion)
            
            if expirados:
                for direccion in expirados:
                    if direccion in clientes:
                        alias = clientes[direccion]['alias']
                        print(f"[TIMEOUT] {alias} ha expirado por inactividad desde {direccion}")
                        del clientes[direccion]
                        # Notificar a los demás clientes
                        if server_running:
                            mensaje_sistema = f"[SYSTEM] {alias} ha salido (timeout)"
                            broadcast(mensaje_sistema, None, True)  # Usar broadcast con is_system=True
                
                mostrar_usuarios_conectados()
                
            time.sleep(5)  # Verificar cada 5 segundos
        except Exception as e:
            if server_running:  # Solo mostrar errores si el servidor sigue en ejecución
                print(f"[ERROR] Error en limpieza de clientes: {e}")
            time.sleep(5)  # Seguir intentando

def iniciar_servidor():
    global servidor, server_running
    limpiar_pantalla()
    server_running = True
    
    # Configuración del servidor
    direccion_host = ''  # Todas las interfaces
    puerto = 65535  # Cambiado a un puerto menos restrictivo (por debajo de 1024 requiere permisos)
    
    try:
        # Crear socket UDP
        servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Intentar enlazar el socket
        try:
            servidor.bind((direccion_host, puerto))
            print(f"[SERVER STARTED] Servidor UDP en {direccion_host if direccion_host else '*'}:{puerto}")
        except OSError as e:
            # Si falla, probar con otro puerto
            print(f"[ERROR] No se pudo usar el puerto {puerto}: {e}")
            puerto = 12345  # Puerto alternativo
            servidor.bind((direccion_host, puerto))
            print(f"[SERVER STARTED] Servidor UDP en {direccion_host if direccion_host else '*'}:{puerto}")
        
        # Iniciar hilo para limpiar clientes inactivos
        hilo_limpieza = threading.Thread(target=limpiar_clientes_inactivos)
        hilo_limpieza.daemon = True
        hilo_limpieza.start()
        
        # Ciclo principal del servidor
        while server_running:
            try:
                # Configurar timeout para poder verificar server_running
                servidor.settimeout(1.0)
                try:
                    # En UDP no hay conexión, solo recibimos datos
                    datos, direccion = servidor.recvfrom(1024)
                    mensaje = datos.decode('utf-8')
                    # Evitamos duplicación en la consola mostrando solo los mensajes necesarios
                    if not mensaje.startswith("PING:"):
                        print(f"[RECIBIDO] {mensaje} de {direccion}")
                    procesar_mensaje(mensaje, direccion)
                except socket.timeout:
                    # Timeout normal, continuar el bucle para verificar server_running
                    continue
                except socket.error as e:
                    if server_running:  # Solo mostrar errores si el servidor sigue en ejecución
                        print(f"[ERROR] Error de socket: {e}")
            except Exception as e:
                if server_running:  # Solo mostrar errores si el servidor sigue en ejecución
                    print(f"[ERROR] Error al recibir datos: {e}")
    
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Servidor detenido por el usuario.")
    except Exception as e:
        print(f"[ERROR] Error al iniciar el servidor: {e}")
    finally:
        # Cambiar el estado del servidor
        server_running = False
        print("[SHUTDOWN] Notificando a los clientes...")
        
        # Notificar a todos los clientes que el servidor está cerrando
        if servidor:
            for direccion in list(clientes.keys()):
                try:
                    servidor.sendto("SERVER_CLOSED".encode('utf-8'), direccion)
                except:
                    pass
            time.sleep(1)  # Dar tiempo para que los mensajes lleguen
            servidor.close()
            print("[CLOSED] Socket del servidor cerrado")

def procesar_mensaje(mensaje, direccion):
    """Procesa los mensajes recibidos de los clientes"""
    global servidor, server_running
    
    # Si el servidor está cerrando, no procesar más mensajes
    if not server_running:
        try:
            servidor.sendto("SERVER_CLOSED".encode('utf-8'), direccion)
        except:
            pass
        return
        
    tiempo_actual = time.time()
    
    try:
        # Aseguramos que el mensaje esté limpio de espacios antes de procesar
        mensaje = mensaje.strip()
        
        # Mensajes que comienzan con prefijos específicos
        if mensaje.startswith("ALIAS:"):
            alias = mensaje[6:].strip()
            # Verificar si ya existe ese alias para evitar duplicados
            for dir_cliente, info in list(clientes.items()):
                if info['alias'] == alias and dir_cliente != direccion:
                    # Notificar al cliente que el alias ya está en uso
                    servidor.sendto("ERROR:ALIAS_IN_USE".encode('utf-8'), direccion)
                    print(f"[DUPLICADO] Intento de registro duplicado para {alias} desde {direccion}")
                    return
                    
            clientes[direccion] = {"alias": alias, "last_seen": tiempo_actual}
            print(f"[NEW USER] {alias} se ha registrado desde {direccion}")
            broadcast(f"[SYSTEM] {alias} ha entrado al chat", direccion, is_system=True)
            mostrar_usuarios_conectados()
        
        elif mensaje.startswith("JOIN:"):
            alias = mensaje[5:].strip()
            if direccion in clientes:
                clientes[direccion]["last_seen"] = tiempo_actual
                # No enviamos mensaje de entrada si ya está registrado
            else:
                # Verificar si ya existe ese alias para evitar duplicados
                for dir_cliente, info in list(clientes.items()):
                    if info['alias'] == alias and dir_cliente != direccion:
                        # Notificar al cliente que el alias ya está en uso
                        servidor.sendto("ERROR:ALIAS_IN_USE".encode('utf-8'), direccion)
                        print(f"[DUPLICADO] Intento de JOIN duplicado para {alias} desde {direccion}")
                        return
                        
                clientes[direccion] = {"alias": alias, "last_seen": tiempo_actual}
                print(f"[JOINED] {alias} se ha unido desde {direccion}")
                broadcast(f"[SYSTEM] {alias} ha entrado al chat", direccion, is_system=True)
                mostrar_usuarios_conectados()
        
        elif mensaje.startswith("EXIT:"):
            alias = mensaje[5:].strip()
            if direccion in clientes:
                print(f"[DESCONEXIÓN] {alias} ha salido desde {direccion}")
                broadcast(f"[SYSTEM] {alias} ha salido", direccion, is_system=True)
                del clientes[direccion]
                mostrar_usuarios_conectados()
        
        elif mensaje.startswith("PING:"):
            alias = mensaje[5:].strip()
            if direccion in clientes:
                clientes[direccion]["last_seen"] = tiempo_actual
                # Simplemente actualizamos el timestamp sin generar tráfico extra
            else:
                # Verificar si ya existe ese alias para evitar duplicados
                duplicado = False
                for dir_cliente, info in list(clientes.items()):
                    if info['alias'] == alias and dir_cliente != direccion:
                        duplicado = True
                        break
                        
                if not duplicado:
                    # Si recibimos un ping de un cliente desconocido, lo registramos
                    clientes[direccion] = {"alias": alias, "last_seen": tiempo_actual}
                    print(f"[RECONEXIÓN] {alias} se ha reconectado desde {direccion}")
                    broadcast(f"[SYSTEM] {alias} se ha reconectado", direccion, is_system=True)
                    mostrar_usuarios_conectados()
        
        elif mensaje.startswith("MSG:"):
            # Mensaje normal de chat
            if direccion in clientes:
                clientes[direccion]["last_seen"] = tiempo_actual
                contenido = mensaje[4:].strip()  # Quitar el prefijo MSG: y espacios
                alias = clientes[direccion]["alias"]
                mensaje_formateado = f"[{alias}] {contenido}"
                print(f"[MENSAJE] {mensaje_formateado}")
                broadcast(mensaje_formateado, direccion)
        
        else:
            # Mensaje desconocido
            print(f"[DESCONOCIDO] Mensaje sin formato recibido de {direccion}: {mensaje}")
            
    except Exception as e:
        print(f"[ERROR] Error al procesar mensaje '{mensaje}' de {direccion}: {e}")

if __name__ == "__main__":
    print("[STARTING] Server starting...")
    iniciar_servidor()