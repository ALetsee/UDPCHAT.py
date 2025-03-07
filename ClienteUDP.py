import socket
import threading
from colorama import Fore, Style, init
import time
import sys
import os
import platform

init(autoreset=True)

cliente = None
alias = None
conectado = False
color_usuario = Fore.WHITE  
host = None
port = None
server_address = None

def limpiar_pantalla():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

limpiar_pantalla()

def mostrar_menu_configuracion():
    global host, port
    limpiar_pantalla()
    print(f"{Fore.BLUE}{Style.BRIGHT}" + 
      "_________   ___ ___    ________________\n" + 
      "\\_   ___ \\ /   |   \\  /  _  \\\__    ___/\n" + 
      "/    \\  \\/    ~    \\/  /_\\  \\|    |   \n" + 
      "\\     \\___\\    Y    /    |    \\    |   \n" + 
      " \\______  /\\___|_  /\\____|__  /____|   \n" + 
      "        \/       \/         \/          ")

    host = input(f"{Fore.BLUE}{Style.BRIGHT}► Ingresa la IP: {Fore.WHITE}").strip()
    while not host:
        print(f"{Fore.RED}[ERROR] IP inválida.{Style.RESET_ALL}")
        host = input(f"{Fore.BLUE}{Style.BRIGHT}► Ingresa la IP: {Fore.WHITE}").strip()
    limpiar_pantalla()

    while not port:
        try:
            port = int(input(f"{Fore.BLUE}{Style.BRIGHT}► Ingresa el puerto: {Fore.WHITE}"))
            if port <= 0 or port > 65535:
                print(f"{Fore.RED}[ERROR] Puerto inválido.{Style.RESET_ALL}")
                port = None
        except ValueError:
            print(f"{Fore.RED}[ERROR] Debe ser un número.{Style.RESET_ALL}")
    limpiar_pantalla()

def _menu_colores():
    print(f"{Fore.BLUE}╔════════════════════╗")
    print(f"{Fore.BLUE}║         COLORES    ║")
    print(f"{Fore.BLUE}╚════════════════════╝")
    colores = [Fore.RED,Fore.GREEN, Fore.MAGENTA, Fore.BLUE]
    nombres = ["Rojo", "Verde", "Magenta", "Azul"]
    for i, nombre in enumerate(nombres, start=1):
        print(f"{colores[i-1]}{i}. {nombre}{Style.RESET_ALL}")

    while True:
        try:
            opcion = int(input(f"{Fore.WHITE}> Elige un color (1-4): {Style.RESET_ALL}"))
            if 1 <= opcion <= 4:
                limpiar_pantalla()
                return colores[opcion-1]
            else:
                print(f"{Fore.RED}[ERROR]{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}[ERROR]  Introduce un número.{Style.RESET_ALL}")

def enviar_latido():
    """Envía mensajes periódicos para mantener la 'conexión' con el servidor"""
    global conectado, cliente, server_address, alias
    while conectado:
        try:
        
            if cliente and conectado:
                cliente.sendto(f"PING:{alias}".encode('utf-8'), server_address)
            time.sleep(5)
        except Exception as e:
            if conectado:
                print(f"\r{Fore.RED}[ERROR] Error al enviar latido: {e}{Style.RESET_ALL}")
        except:
            pass

def recibir_mensajes():
    global conectado, cliente, alias, color_usuario
    while conectado:
        try:
            cliente.settimeout(30)  
            datos, _ = cliente.recvfrom(1024)
            mensaje = datos.decode('utf-8')
            
            if not mensaje:
                continue

            if mensaje.startswith("SERVER_CLOSED"):
                print(f"\r{Fore.RED}[INFO] El servidor ha cerrado la conexión.{Style.RESET_ALL}")
                conectado = False
                break
                
            sys.stdout.write("\r" + " " * 80 + "\r")
            sys.stdout.write(f"{mensaje}\n")
            sys.stdout.flush()
            
            sys.stdout.write(f"{color_usuario}{alias} > {Style.RESET_ALL}")
            sys.stdout.flush()
            
        except socket.timeout:
            try:
                if conectado and cliente:
                    cliente.sendto(f"PING:{alias}".encode('utf-8'), server_address)
            except:
                pass
            continue
        except Exception as e:
            if conectado:
                print(f"\r{Fore.RED}[ERROR] Problema al recibir: {e}{Style.RESET_ALL}")
                try:
                    if conectado and cliente:
                        cliente.sendto(f"PING:{alias}".encode('utf-8'), server_address)
                except:
                    pass
            else:
                break

    if not conectado:
        time.sleep(1)  
        limpiar_pantalla()

def start_client():
    global cliente, alias, conectado, color_usuario, host, port, server_address
    mostrar_menu_configuracion()
    alias = input(f"{Fore.BLUE}Usuario > {Style.RESET_ALL}").strip()
    while not alias:
        print(f"{Fore.RED}[ERROR] El nombre de usuario no puede estar vacío.{Style.RESET_ALL}")
        alias = input(f"{Fore.BLUE}Usuario >{Style.RESET_ALL}").strip()
    limpiar_pantalla()

    color_usuario = _menu_colores()
    
    cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (host, port)
    
    try:
        cliente.settimeout(2)

        cliente.sendto(f"ALIAS:{alias}".encode('utf-8'), server_address)
        conectado = True

        try:
            datos, _ = cliente.recvfrom(1024)
        except socket.timeout:
            pass
        except Exception as e:
            print(f"{Fore.YELLOW}[AVISO] No se recibió confirmación pero continuando...{Style.RESET_ALL}")
        
        cliente.settimeout(None)
        hilo_recepcion = threading.Thread(target=recibir_mensajes)
        hilo_recepcion.daemon = True
        hilo_recepcion.start()
        
        hilo_latido = threading.Thread(target=enviar_latido)
        hilo_latido.daemon = True
        hilo_latido.start()
        print(f"{Fore.BLUE}╔══════════════════════════════════════╗{Style.RESET_ALL}")
        print(f"{Fore.BLUE}║                  CHAT                ║{Style.RESET_ALL}")
        print(f"{Fore.BLUE}╚══════════════════════════════════════╝{Style.RESET_ALL}")
        print(f"{Fore.BLUE}[CONECTADO] Server: {Fore.WHITE}{host}:{port}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}[CONECTADO] Welcome, {color_usuario}{alias}{Style.RESET_ALL}!")
        print(f"{Fore.BLUE}[INFO] Escribe 'exit' o 'salir' para salir.{Style.RESET_ALL}")
        
        time.sleep(0.5) 
        
        for _ in range(3):
            cliente.sendto(f"JOIN:{alias}".encode('utf-8'), server_address)
            time.sleep(0.2) 

        while conectado:
            try:
                mensaje = input(f"{color_usuario}{alias} > {Style.RESET_ALL}")
                if not conectado: 
                    break
                    
                if mensaje.lower() in ["exit", "salir"]:
                    cliente.sendto(f"EXIT:{alias}".encode('utf-8'), server_address)
                    for _ in range(3):
                        cliente.sendto(f"EXIT:{alias}".encode('utf-8'), server_address)
                        time.sleep(0.1)
                    conectado = False
                    break
                
                if mensaje.strip() and conectado:
                    cliente.sendto(f"MSG:{alias}: {mensaje}".encode('utf-8'), server_address)
            except Exception as e:
                if conectado:
                    print(f"{Fore.RED}[ERROR] Error al enviar mensaje: {e}{Style.RESET_ALL}")
                else:
                    break
                    
    except Exception as e:
        print(f"{Fore.RED}[ERROR] {e}{Style.RESET_ALL}")
    finally:
        conectado = False
        if cliente:
            try:
                cliente.close()
            except:
                pass
        print(f"{Fore.RED}[OFFLINE]{Style.RESET_ALL}")

if __name__ == "__main__":
    print(f"{Fore.BLUE}[INICIANDO] Cliente UDP{Style.RESET_ALL}")
    try:
        start_client()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[CANCELED] Programa terminado.{Style.RESET_ALL}")
        conectado = False 
        sys.exit(0)