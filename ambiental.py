import tkinter as tk
import serial
import threading
import re
import time

# ==============================================================================
# CONFIGURACIÓN PARA PINES 8 Y 10 EN RASPBERRY PI
# ==============================================================================
PUERTO = '/dev/serial0'  # Mapeo universal de los pines 8 y 10 en Raspbian
BAUDIOS = 115200

class AppMonitoreoAZTECH:
    def __init__(self, root):
        self.root = root
        self.root.title("Panel de Control - AZTECH")
        self.root.geometry("450x350")
        self.root.configure(bg="#1e272e")  # Fondo oscuro elegante

        # --- Componentes de la Interfaz ---
        self.lbl_titulo = tk.Label(root, text="MONITOREO DE VARIABLES", font=("Arial", 16, "bold"), fg="#ffffff", bg="#1e272e")
        self.lbl_titulo.pack(pady=15)

        self.lbl_temp = tk.Label(root, text="Temperatura: -- °C", font=("Arial", 14), fg="#ff5e57", bg="#1e272e")
        self.lbl_temp.pack(pady=10)

        self.lbl_hum = tk.Label(root, text="Humedad: -- %", font=("Arial", 14), fg="#0be881", bg="#1e272e")
        self.lbl_hum.pack(pady=10)

        self.lbl_nivel = tk.Label(root, text="Nivel de Agua: -- m", font=("Arial", 14), fg="#34e7e4", bg="#1e272e")
        self.lbl_nivel.pack(pady=10)

        self.lbl_estado = tk.Label(root, text="Iniciando conexión...", font=("Arial", 10, "italic"), fg="#ffd32a", bg="#1e272e")
        self.lbl_estado.pack(pady=25)

        # Control del hilo
        self.ejecutando = True
        
        # Iniciar la lectura serial en un hilo separado para evitar desfases
        self.hilo_serial = threading.Thread(target=self.leer_puerto_serial, daemon=True)
        self.hilo_serial.start()

        # Asegurar un cierre limpio de la app
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)

    def leer_puerto_serial(self):
        while self.ejecutando:
            try:
                # Intentar abrir el puerto serial
                ser = serial.Serial(PUERTO, BAUDIOS, timeout=1)
                self.lbl_estado.config(text=f"Conectado a pines 8 y 10 ({PUERTO})", fg="#0be881")
                
                while self.ejecutando:
                    if ser.in_waiting > 0:
                        # Leer línea entrante descodificando caracteres extraños
                        linea = ser.readline().decode('utf-8', errors='ignore').strip()
                        
                        if linea:
                            self.analizar_trama(linea)
                            
                ser.close()
            except (serial.SerialException, FileNotFoundError):
                self.lbl_estado.config(text="Error: Revisa si el UART está activo en tu Raspberry Pi", fg="#ff5e57")
                time.sleep(2)  # Reintentar conexión cada 2 segundos

    def analizar_trama(self, cadena):
        # Expresión regular para extraer los valores flotantes del STM32: <T:xx.xx,H:xx.xx,N:xx.xx>
        patron = r"<T:(.*?);H:(.*?);N:(.*?)>" if ';' in cadena else r"<T:(.*?),H:(.*?),N:(.*?)>"
        match = re.search(patron, cadena)
        
        if match:
            try:
                temp = float(match.group(1))
                hum = float(match.group(2))
                nivel = float(match.group(3))
                
                # Actualizar los datos de forma segura en el hilo principal
                self.root.after(0, self.actualizar_pantalla, temp, hum, nivel)
            except ValueError:
                pass  # Ignorar si la conversión de datos se corrompió a la mitad

    def actualizar_pantalla(self, t, h, n):
        self.lbl_temp.config(text=f"Temperatura: {t:.2f} °C")
        self.lbl_hum.config(text=f"Humedad: {h:.1f} %")
        self.lbl_nivel.config(text=f"Nivel de Agua: {n:.3f} m")
        self.lbl_estado.config(text="Datos actualizados en tiempo real", fg="#0be881")

    def cerrar_aplicacion(self):
        self.ejecutando = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AppMonitoreoAZTECH(root)
    root.mainloop()