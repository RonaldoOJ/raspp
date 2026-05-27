import serial
import customtkinter as ctk
from tkinter import messagebox
import threading
import time

# =========================================
# CONFIGURACION GENERAL
# =========================================

# CORREGIDO: Ajustado al primer puerto USB serial por defecto en Linux y velocidad de STM32
PUERTO = "/dev/ttyUSB0" 
BAUDIOS = 115200

PELIGRO = "PELIGRO"
ADVERTENCIAS = {"Precaución", "Riesgo"}

ultima_severidad = None

# =========================================
# APARIENCIA MODERNA
# =========================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# =========================================
# VENTANA PRINCIPAL
# =========================================

root = ctk.CTk()
root.title("Sistema Inteligente Ambiental")
root.geometry("1000x700")
root.minsize(900, 650)

# =========================================
# VARIABLES ANIMACION
# =========================================

animando_peligro = False
estado_parpadeo = False

# =========================================
# TITULO Y SUBTITULO
# =========================================

titulo = ctk.CTkLabel(root, text="SISTEMA INTELIGENTE DE MONITOREO", font=("Arial", 32, "bold"))
titulo.pack(pady=20)

subtitulo = ctk.CTkLabel(root, text="Monitoreo en tiempo real de temperatura, humedad y nivel de agua", font=("Arial", 16))
subtitulo.pack(pady=5)

# =========================================
# FRAME PRINCIPAL Y VARIABLES
# =========================================

frame_principal = ctk.CTkFrame(root, corner_radius=20)
frame_principal.pack(padx=20, pady=20, fill="both", expand=True)

temp_var = ctk.StringVar(value="-- °C")
hum_var = ctk.StringVar(value="-- %")
nivel_var = ctk.StringVar(value="-- m")
estado_general_var = ctk.StringVar(value="Esperando datos...")
conexion_var = ctk.StringVar(value="DESCONECTADO")

# =========================================
# TARJETAS UI
# =========================================

def crear_tarjeta(parent, titulo_texto, variable, emoji):
    tarjeta = ctk.CTkFrame(parent, corner_radius=20, height=180)
    tarjeta.pack(pady=15, padx=20, fill="x")

    titulo = ctk.CTkLabel(tarjeta, text=f"{emoji}  {titulo_texto}", font=("Arial", 22, "bold"))
    titulo.pack(pady=15)

    valor = ctk.CTkLabel(tarjeta, textvariable=variable, font=("Arial", 30))
    valor.pack(pady=10)

    return tarjeta

temp_card = crear_tarjeta(frame_principal, "TEMPERATURA", temp_var, "🌡️")
hum_card = crear_tarjeta(frame_principal, "HUMEDAD", hum_var, "💧")
nivel_card = crear_tarjeta(frame_principal, "NIVEL DE AGUA", nivel_var, "🌊")

# Estado general abajo
estado_frame = ctk.CTkFrame(root, corner_radius=20)
estado_frame.pack(padx=20, pady=10, fill="x")

estado_label = ctk.CTkLabel(estado_frame, textvariable=estado_general_var, font=("Arial", 24, "bold"))
estado_label.pack(pady=15)

conexion_label = ctk.CTkLabel(root, textvariable=conexion_var, font=("Arial", 16, "bold"))
conexion_label.pack(pady=10)

# =========================================
# LOGICA DE ALERTAS Y EVALUACIONES
# =========================================

def animar_peligro():
    global estado_parpadeo
    if animando_peligro:
        if estado_parpadeo:
            estado_frame.configure(fg_color="#8B0000")
            estado_label.configure(text_color="white")
        else:
            estado_frame.configure(fg_color="red")
            estado_label.configure(text_color="yellow")
        estado_parpadeo = not estado_parpadeo
        root.after(500, animar_peligro)

def evaluar_temperatura(temp):
    if temp < 0: return ("CONGELACION", "PELIGRO", "Riesgo de hipotermia severa.")
    elif temp < 15: return ("FRIO EXTREMO", "Riesgo", "Usar ropa térmica.")
    elif temp < 25: return ("NORMAL", "Seguro", "Condiciones adecuadas.")
    elif temp < 35: return ("CALIDO", "Estable", "Mantener hidratación.")
    elif temp < 40: return ("CALOR ALTO", "Precaución", "Evitar exposición prolongada.")
    else: return ("CALOR EXTREMO", "PELIGRO", "Posible golpe de calor.")

def evaluar_humedad(hum):
    if hum < 20: return ("AIRE MUY SECO", "Riesgo", "Posible irritación respiratoria.")
    elif hum < 40: return ("SECO", "Estable", "Baja humedad ambiental.")
    elif hum < 70: return ("NORMAL", "Seguro", "Condiciones óptimas.")
    elif hum < 85: return ("HUMEDO", "Estable", "Posible lluvia.")
    elif hum < 95: return ("HUMEDAD ALTA", "Precaución", "Ambiente muy húmedo.")
    else: return ("HUMEDAD CRITICA", "PELIGRO", "Alta probabilidad de tormenta.")

def evaluar_nivel(nivel):
    if nivel < 0.05: return ("SIN RIESGO", "Seguro", "Nivel normal.")
    elif nivel < 0.15: return ("AGUA BAJA", "Estable", "Acumulación ligera.")
    elif nivel < 0.30: return ("ENCHARCAMIENTO", "Precaución", "Transitar con cuidado.")
    elif nivel < 0.60: return ("RIESGO DE INUNDACION", "Riesgo", "Evitar zonas bajas.")
    else: return ("INUNDACION CRITICA", "PELIGRO", "Evacuación recomendada.")

def obtener_severidad(riesgos):
    if PELIGRO in riesgos: return ("PELIGRO AMBIENTAL", "red", "PELIGRO")
    if any(riesgo in ADVERTENCIAS for riesgo in riesgos): return ("ALERTA AMBIENTAL", "orange", "ADVERTENCIA")
    return ("ESTADO NORMAL", "green", "NORMAL")

def mostrar_popup(titulo, mensaje, severidad):
    if severidad == "PELIGRO": messagebox.showerror(titulo, mensaje)
    elif severidad == "ADVERTENCIA": messagebox.showwarning(titulo, mensaje)

# =========================================
# ACTUALIZAR INTERFAZ Y PROCESAR
# =========================================

def actualizar_interfaz(temp, hum, nivel):
    global ultima_severidad, animando_peligro

    estado_temp, riesgo_temp, rec_temp = evaluar_temperatura(temp)
    estado_hum, riesgo_hum, rec_hum = evaluar_humedad(hum)
    estado_niv, riesgo_niv, rec_niv = evaluar_nivel(nivel)

    titulo_estado, color_estado, severidad = obtener_severidad((riesgo_temp, riesgo_hum, riesgo_niv))

    temp_var.set(f"{temp:.3f} °C\n{estado_temp}")
    hum_var.set(f"{hum:.3f} %\n{estado_hum}")
    nivel_var.set(f"{nivel:.3f} m\n{estado_niv}")
    estado_general_var.set(titulo_estado)

    if severidad == "PELIGRO":
        if not animando_peligro:
            animando_peligro = True
            animar_peligro()
    else:
        animando_peligro = False
        estado_frame.configure(fg_color=color_estado)
        estado_label.configure(text_color="white")

    mensaje = f"\nTEMPERATURA\n{temp:.3f} °C\n{estado_temp}\n\nRecomendación:\n{rec_temp}\n\n----------------------------\n\nHUMEDAD\n{hum:.3f} %\n{estado_hum}\n\nRecomendación:\n{rec_hum}\n\n----------------------------\n\nNIVEL DE AGUA\n{nivel:.3f} m\n{estado_niv}\n\nRecomendación:\n{rec_niv}\n"

    if severidad != ultima_severidad:
        ultima_severidad = severidad
        if severidad != "NORMAL":
            mostrar_popup(titulo_estado, mensaje, severidad)

# CORREGIDO: Añadido el bucle por comprensión interno que faltaba para procesar las llaves de datos
def extraer_valores(linea):
    partes = linea[1:-1].split(",")
    return tuple(float(parte.split(":", 1)[1]) for parte in partes)

# =========================================
# LECTURA SERIAL (UART)
# =========================================

def leer_datos():
    try:
        with serial.Serial(PUERTO, BAUDIOS, timeout=1) as ser:
            ser.reset_input_buffer()
            conexion_var.set("⚡ CONEXIÓN UART ACTIVA")

            while True:
                linea = ser.readline().decode('utf-8', errors='ignore').strip()
                if linea:
                    print("RECIBIDO (UART):", linea)
                    if linea.startswith("<") and linea.endswith(">"):
                        try:
                            temp, hum, nivel = extraer_valores(linea)
                            root.after(0, actualizar_interfaz, temp, hum, nivel)
                        except Exception as e:
                            print("ERROR PARSEANDO DATOS UART:", e)
                time.sleep(0.1)

    except Exception as e:
        conexion_var.set("❌ UART DESCONECTADO / ERROR DE PUERTO")
        error_msg = str(e)
        root.after(
            0,
            lambda msg=error_msg: messagebox.showerror(
                "ERROR CONEXIÓN UART",
                f"No se pudo abrir el puerto serie.\n\nVerifica que no esté en uso y tengas permisos.\n\nDetalle: {msg}"
            )
        )

# Hilo secundario
hilo = threading.Thread(target=leer_datos)
hilo.daemon = True
hilo.start()

if __name__ == "__main__":
    root.mainloop()