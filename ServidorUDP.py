import socket
import threading
import time
import os
import platform

clientes = {} 
servidor = None  
server_running = True  

def limpiar_pantalla():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def broadcast(mensaje, remitente=None, is_system=False):
    """Envía un mensaje a todos los clientes excepto al remitente"""
    global servidor, server_running
    

    if not server_running:
        return
        
    mensaje_bytes = mensaje.encode('utf-8')
    

    expirados = []
    
    for direccion, info in list(clientes.items()):  

        if direccion != remitente or is_system:
            try:
                servidor.sendto(mensaje_bytes, direccion)
            except Exception as e:
                print(f"[ERROR] Error al enviar a {info['alias']}: {e}")
                expirados.append(direccion)
    

    for direccion in expirados:
        if direccion in clientes:
            alias = clientes[direccion]['alias']
            print(f"[TIMEOUT] {alias} ha expirado por inactividad desde {direccion}")
            del clientes[direccion]

            if len(clientes) > 0 and server_running:
                mensaje_sistema = f"[SYSTEM] {alias} ha salido (timeout)"
                broadcast(mensaje_sistema, None, True) 

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
            
    
            for direccion, info in list(clientes.items()):

                if tiempo_actual - info['last_seen'] > 30:  
                    expirados.append(direccion)
            
            if expirados:
                for direccion in expirados:
                    if direccion in clientes:
                        alias = clientes[direccion]['alias']
                        print(f"[TIMEOUT] {alias} ha expirado por inactividad desde {direccion}")
                        del clientes[direccion]
            
                        if server_running:
                            mensaje_sistema = f"[SYSTEM] {alias} ha salido (timeout)"
                            broadcast(mensaje_sistema, None, True) 
                
                mostrar_usuarios_conectados()
                
            time.sleep(5) 
        except Exception as e:
            if server_running:  
                print(f"[ERROR] Error en limpieza de clientes: {e}")
            time.sleep(5)  
def iniciar_servidor():
    global servidor, server_running
    limpiar_pantalla()
    server_running = True
    

    direccion_host = ''
    puerto = 65535  # Cambiado a un puerto menos restrictivo (por debajo de 1024 requiere permisos)
    
    try:
        # Crear socket UDP
        servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        

        try:
            servidor.bind((direccion_host, puerto))
            print(f"[SERVER STARTED] Servidor UDP en {direccion_host if direccion_host else '*'}:{puerto}")
        except OSError as e:
            # Si falla, probar con otro puerto
            print(f"[ERROR] No se pudo usar el puerto {puerto}: {e}")
            puerto = 12345  # Puerto alternativo
            servidor.bind((direccion_host, puerto))
            print(f"[SERVER STARTED] Servidor UDP en {direccion_host if direccion_host else '*'}:{puerto}")
        
        hilo_limpieza = threading.Thread(target=limpiar_clientes_inactivos)
        hilo_limpieza.daemon = True
        hilo_limpieza.start()
        

        while server_running:
            try:

                servidor.settimeout(1.0)
                try:
      
                    datos, direccion = servidor.recvfrom(1024)
                    mensaje = datos.decode('utf-8')
        
                    if not mensaje.startswith("PING:"):
                        print(f"[RECIBIDO] {mensaje} de {direccion}")
                    procesar_mensaje(mensaje, direccion)
                except socket.timeout:

                    continue
                except socket.error as e:
                    if server_running:  
                        print(f"[ERROR] Error de socket: {e}")
            except Exception as e:
                if server_running:  
                    print(f"[ERROR] Error al recibir datos: {e}")
    
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Servidor detenido por el usuario.")
    except Exception as e:
        print(f"[ERROR] Error al iniciar el servidor: {e}")
    finally:
        # Cambiar el estado del servidor
        server_running = False
        print("[SHUTDOWN] Notificando a los clientes...")
        

        if servidor:
            for direccion in list(clientes.keys()):
                try:
                    servidor.sendto("SERVER_CLOSED".encode('utf-8'), direccion)
                except:
                    pass
            time.sleep(1)  
            servidor.close()
            print("[CLOSED] Socket del servidor cerrado")

def procesar_mensaje(mensaje, direccion):
    """Procesa los mensajes recibidos de los clientes"""
    global servidor, server_running
    
    if not server_running:
        try:
            servidor.sendto("SERVER_CLOSED".encode('utf-8'), direccion)
        except:
            pass
        return
        
    tiempo_actual = time.time()
    
    try:

        mensaje = mensaje.strip()
        

        if mensaje.startswith("ALIAS:"):
            alias = mensaje[6:].strip()


            for dir_cliente, info in list(clientes.items()):
                if info['alias'] == alias and dir_cliente != direccion:
                    
                    
   
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
            
            else:
                for dir_cliente, info in list(clientes.items()):
                    if info['alias'] == alias and dir_cliente != direccion:
                     
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
            else:

                duplicado = False
                for dir_cliente, info in list(clientes.items()):
                    if info['alias'] == alias and dir_cliente != direccion:
                        duplicado = True
                        break
                        
                if not duplicado:
                    clientes[direccion] = {"alias": alias, "last_seen": tiempo_actual}
                    print(f"[RECONEXIÓN] {alias} se ha reconectado desde {direccion}")
                    broadcast(f"[SYSTEM] {alias} se ha reconectado", direccion, is_system=True)
                    mostrar_usuarios_conectados()
        
        elif mensaje.startswith("MSG:"):

            if direccion in clientes:
                clientes[direccion]["last_seen"] = tiempo_actual
                contenido = mensaje[4:].strip()
                alias = clientes[direccion]["alias"]
                mensaje_formateado = f"[{alias}] {contenido}"
                print(f"[MENSAJE] {mensaje_formateado}")
                broadcast(mensaje_formateado, direccion)
        
        else:

            print(f"[DESCONOCIDO] Mensaje sin formato recibido de {direccion}: {mensaje}")
            
    except Exception as e:
        print(f"[ERROR] Error al procesar mensaje '{mensaje}' de {direccion}: {e}")

if __name__ == "__main__":
    print("[STARTING] Server starting...")
    iniciar_servidor()