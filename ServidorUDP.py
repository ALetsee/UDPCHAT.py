import socket
import threading
import time
import os
import platform

# Lista de clientes (en UDP guardamos direcciones en lugar de conexiones)
clientes = {}  # {(ip, puerto): {"alias": alias, "last_seen": timestamp}}
servidor = None  # Declaración global del socket

def limpiar_pantalla():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def broadcast(mensaje, remitente=None, is_system=False):
    """Envía un mensaje a todos los clientes excepto al remitente"""
    global servidor
    mensaje_bytes = mensaje.encode('utf-8')
    
    # Clientes a eliminar (expirados)
    expirados = []
    tiempo_actual = time.time()
    
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
            if len(clientes) > 0:
                mensaje_sistema = f"[SYSTEM] {alias} ha salido (timeout)"
                broadcast(mensaje_sistema, None, True)  # Llamada con is_system=True
    
    mostrar_usuarios_conectados()

def mostrar_usuarios_conectados():
    """Muestra la lista de usuarios conectados"""
    usuarios = [info['alias'] for info in clientes.values()]
    if usuarios:
        print(f"[USERS] Total: {len(usuarios)} - {', '.join(usuarios)}")
    else:
        print("[USERS] No hay usuarios conectados")

def limpiar_clientes_inactivos():
    """Elimina periódicamente los clientes inactivos"""
    global servidor
    while True:
        try:
            tiempo_actual = time.time()
            expirados = []
            
            # Usar una copia del diccionario para evitar errores de modificación durante iteración
            for direccion, info in list(clientes.items()):
                # Aumentado a 30 segundos para ser más tolerante con la red
                if tiempo_actual - info['last_seen'] > 30:  # 30 segundos sin actividad
                    expirados.append(direccion)
            
            for direccion in expirados:
                if direccion in clientes:
                    alias = clientes[direccion]['alias']
                    print(f"[TIMEOUT] {alias} ha expirado por inactividad desde {direccion}")
                    del clientes[direccion]
                    # Notificar a los demás clientes
                    mensaje_sistema = f"[SYSTEM] {alias} ha salido (timeout)"
                    broadcast(mensaje_sistema, None, True)  # Usar broadcast con is_system=True
            
            if expirados:
                mostrar_usuarios_conectados()
                
            time.sleep(5)  # Verificar cada 5 segundos
        except Exception as e:
            print(f"[ERROR] Error en limpieza de clientes: {e}")
            time.sleep(5)  # Seguir intentando

def iniciar_servidor():
    global servidor
    limpiar_pantalla()
    
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
        while True:
            try:
                # En UDP no hay conexión, solo recibimos datos
                datos, direccion = servidor.recvfrom(1024)
                mensaje = datos.decode('utf-8')
                print(f"[RECIBIDO] {mensaje} de {direccion}")
                procesar_mensaje(mensaje, direccion)
            except socket.error as e:
                print(f"[ERROR] Error de socket: {e}")
            except Exception as e:
                print(f"[ERROR] Error al recibir datos: {e}")
    
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Servidor detenido.")
    except Exception as e:
        print(f"[ERROR] Error al iniciar el servidor: {e}")
    finally:
        # Notificar a todos los clientes que el servidor está cerrando
        if servidor:
            for direccion in list(clientes.keys()):
                try:
                    servidor.sendto("SERVER_CLOSED".encode('utf-8'), direccion)
                except:
                    pass
            servidor.close()
            print("[CLOSED] Socket del servidor cerrado")

def procesar_mensaje(mensaje, direccion):
    """Procesa los mensajes recibidos de los clientes"""
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
                    # No hacer nada, ya está registrado ese alias
                    print(f"[DUPLICADO] Intento de registro duplicado para {alias} desde {direccion}")
                    return
                    
            clientes[direccion] = {"alias": alias, "last_seen": tiempo_actual}
            print(f"[NEW USER] {alias} se ha registrado desde {direccion}")
            broadcast(f"[SYSTEM] {alias} ha entrado al chat", direccion, is_system=True)
        
        elif mensaje.startswith("JOIN:"):
            alias = mensaje[5:].strip()
            if direccion in clientes:
                clientes[direccion]["last_seen"] = tiempo_actual
                # No enviamos mensaje de entrada si ya está registrado
            else:
                # Verificar si ya existe ese alias para evitar duplicados
                for dir_cliente, info in list(clientes.items()):
                    if info['alias'] == alias and dir_cliente != direccion:
                        # No hacer nada, ya está registrado ese alias
                        print(f"[DUPLICADO] Intento de JOIN duplicado para {alias} desde {direccion}")
                        return
                        
                clientes[direccion] = {"alias": alias, "last_seen": tiempo_actual}
                print(f"[JOINED] {alias} se ha unido desde {direccion}")
                broadcast(f"[SYSTEM] {alias} ha entrado al chat", direccion, is_system=True)
        
        elif mensaje.startswith("EXIT:"):
            alias = mensaje[5:].strip()
            if direccion in clientes:
                print(f"[DESCONEXIÓN] {alias} ha salido desde {direccion}")
                broadcast(f"[SYSTEM] {alias} ha salido", direccion, is_system=True)
                del clientes[direccion]
        
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
        
        elif mensaje.startswith("MSG:"):
            # Mensaje normal de chat
            if direccion in clientes:
                clientes[direccion]["last_seen"] = tiempo_actual
                contenido = mensaje[4:].strip()  # Quitar el prefijo MSG: y espacios
                print(f"[MENSAJE] {contenido}")
                broadcast(contenido, direccion)
        
        else:
            # Mensaje desconocido
            print(f"[DESCONOCIDO] Mensaje sin formato recibido de {direccion}: {mensaje}")
            
        # Mostrar la lista actualizada después de cada mensaje procesado
        mostrar_usuarios_conectados()
            
    except Exception as e:
        print(f"[ERROR] Error al procesar mensaje '{mensaje}' de {direccion}: {e}")

if __name__ == "__main__":
    print("[STARTING] Server starting...")
    iniciar_servidor()