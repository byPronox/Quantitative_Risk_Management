# 🌐 Estrategia de Resolución de Nombres (DNS) en Sistemas Distribuidos

Este documento detalla la implementación, justificación y verificación de la estrategia de **"Servicio de nombres local con fallback a servidor público"** en nuestro sistema distribuido.

---

## 1. 📂 ¿Dónde está configurado?

Toda la magia ocurre en el archivo `docker-compose.yml`. No se requiere código adicional en la aplicación porque utilizamos la infraestructura de red subyacente de Docker.

### A. Configuración del Servicio Local (Service Discovery)
No hay una línea explícita de "configuración" porque es una **característica nativa** de las redes definidas por software de Docker.

*   **En `docker-compose.yml`:**
    ```yaml
    services:
      nvd-service:  # <--- ESTE NOMBRE es la clave
        build: ...
    ```
*   **Explicación:** Al definir un servicio con el nombre `nvd-service`, Docker registra automáticamente este nombre en su servidor DNS interno (`127.0.0.11`). Cualquier otro contenedor en la misma red puede encontrarlo simplemente llamándolo por su nombre.

### B. Configuración del Fallback Público
Esta parte sí es explícita y se encuentra en la definición de cada servicio.

*   **En `docker-compose.yml`:**
    ```yaml
    services:
      backend:
        dns:
          - 8.8.8.8  # <--- Configuración EXPLÍCITA
    ```
*   **Explicación:** Esta línea instruye al contenedor: *"Si no encuentras el nombre en el DNS interno de Docker, pregúntale a este servidor (Google DNS) en internet"*.

---

## 2. 🚀 ¿Por qué esto hace al sistema "Distribuido"?

Esta estrategia es fundamental para la arquitectura de microservicios y sistemas distribuidos por tres razones:

1.  **Desacoplamiento de Ubicación (Location Transparency):**
    *   El servicio `backend` no necesita saber la IP de `nvd-service` (que cambia cada vez que se reinicia el contenedor).
    *   Solo necesita saber su **nombre lógico**. Esto permite que los servicios se muevan, escalen o reinicien sin romper la comunicación.

2.  **Independencia de la Red:**
    *   El sistema funciona igual en tu laptop, en un servidor de pruebas o en la nube. La resolución de nombres abstrae la complejidad de la red física.

3.  **Resiliencia y Disponibilidad:**
    *   Si el servicio local falla, el sistema de nombres sigue funcionando.
    *   Si necesitamos acceder a recursos externos (como `google.com` o APIs externas), el sistema tiene una ruta clara (fallback) para salir a buscarlos, sin mezclar el tráfico interno con el externo.

---

## 3. 🧪 Análisis de los Resultados de Verificación

A continuación, analizamos los resultados que obtuviste al ejecutar las pruebas de verificación.

### Prueba A: Resolución Interna
**Comando:**
```bash
docker exec ... python -c "import socket; print(socket.gethostbyname('nvd-service'))"
```

**Resultado Obtenido:**
> `172.19.0.2`

**Interpretación:**
*   **¿Qué es esa IP?** Es una dirección IP privada dentro del rango de la red virtual de Docker.
*   **¿Qué significa?** El DNS interno funcionó. El `backend` preguntó "¿Quién es `nvd-service`?" y Docker respondió "Es mi vecino en la red local, aquí tienes su IP privada".
*   **Veredicto:** ✅ El tráfico se mantuvo **100% local**.

### Prueba B: Resolución Externa (Fallback)
**Comando:**
```bash
docker exec ... python -c "import socket; print(socket.gethostbyname('google.com'))"
```

**Resultado Obtenido:**
> `172.217.162.110` (o similar)

**Interpretación:**
*   **¿Qué es esa IP?** Es una dirección IP pública perteneciente a los servidores de Google en Internet.
*   **¿Qué significa?** El DNS interno dijo "No conozco a `google.com`". Entonces, se activó el **fallback** configurado (`dns: 8.8.8.8`). La petición salió a internet, resolvió el dominio y devolvió la IP real.
*   **Veredicto:** ✅ El sistema tiene capacidad de **salida a internet** cuando el recurso no es local.

---

## 4. ✅ Conclusión Final

El sistema cumple rigurosamente con el requisito:

> *"Servicio de nombres local, configurado si no puede resolver ahí, sí a servidor público"*

1.  **Local:** Garantizado por el Service Discovery de Docker (demostrado con la IP `172.x.x.x`).
2.  **Público:** Garantizado por la directiva `dns: 8.8.8.8` (demostrado con la IP pública de Google).
