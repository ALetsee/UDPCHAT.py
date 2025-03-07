# Funcionamiento del Sistema de Chat UDP

## Descripción General

El sistema consta de dos componentes principales: un servidor y un cliente que se comunican mediante el protocolo UDP. Esta aplicación de chat permite que múltiples usuarios se conecten al servidor y envíen mensajes que serán distribuidos a todos los demás participantes.

## Servidor

El servidor actúa como el punto central que gestiona las conexiones y distribuye los mensajes. Sus principales funciones son:

### Inicio y configuración

- El servidor inicia en todas las interfaces disponibles, intentando primero usar el puerto 65535. Si este puerto está ocupado, automáticamente cambiará al puerto 11111.

### Gestión de usuarios

- Mantiene un registro de todos los clientes conectados, incluyendo su alias y la última vez que enviaron algún tipo de actividad.

### Procesamiento de mensajes

- Recibe y procesa diferentes tipos de mensajes:
  - **ALIAS:** Registra un nuevo usuario.
  - **JOIN:** Confirma que un usuario se ha unido al chat.
  - **EXIT:** Procesa la desconexión de un usuario.
  - **PING:** Actualiza el tiempo de actividad para evitar desconexiones por inactividad.
  - **MSG:** Redistribuye los mensajes de texto a todos los demás usuarios.

### Limpieza automática

- Un proceso en segundo plano elimina los clientes inactivos después de 30 segundos sin recibir señales.

## Cliente

El cliente permite a los usuarios conectarse al servidor y participar en el chat. Sus características incluyen:

### Configuración inicial

- Solicita al usuario que ingrese:
  - Dirección IP del servidor.
  - Puerto del servidor.
  - Nombre de usuario (alias).
  - Color preferido para sus mensajes.

### Gestión de conexión

- Mantiene la conexión con el servidor mediante el envío periódico de mensajes "PING".

### Interfaz de usuario

- Proporciona una interfaz colorida que muestra los mensajes recibidos y permite enviar nuevos mensajes.

### Manejo de desconexiones

- Detecta cuando el servidor cierra y termina ordenadamente la aplicación.

## Protocolo de Comunicación

La comunicación entre el cliente y el servidor sigue un formato simple basado en etiquetas:

- **ALIAS:nombre** - Registra un nuevo usuario.
- **JOIN:nombre** - Notifica que un usuario se ha unido.
- **EXIT:nombre** - Notifica que un usuario se ha desconectado.
- **PING:nombre** - Mantiene la conexión activa.
- **MSG:nombre: mensaje** - Envía un mensaje de texto al chat.

## Solución de Problemas

**Importante:** Si experimentas problemas de conexión, es posible que necesites modificar los puertos usados:

### En el servidor

- Si el puerto por defecto (65535) está ocupado, el servidor intentará automáticamente usar el puerto 11111. Si necesitas usar otro puerto, deberás modificar la variable puerto en el archivo del servidor.

### En el cliente

- Asegúrate de ingresar el mismo puerto que está utilizando el servidor. El cliente te pedirá esta información al iniciar.

Si sigues teniendo problemas de conexión, verifica:

- Que no haya firewalls bloqueando la comunicación UDP.
- Que estés usando la dirección IP correcta del servidor.
- Que tanto el cliente como el servidor estén en la misma red o tengan conectividad entre sí.

El sistema está diseñado para ser robusto, manejando desconexiones inesperadas y manteniendo a los usuarios informados sobre quién entra y sale del chat.

Resultados:

https://github.com/user-attachments/assets/e4beae1b-b5c3-43b3-92d5-1c23e68697d9
