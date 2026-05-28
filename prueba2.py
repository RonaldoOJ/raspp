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
        self.root.title("Sistema de Monitoreo Ambiental")
        
        # --- Configuración de Pantalla Completa y Estética ---
        self.root.attributes("-fullscreen", True) # Pantalla completa
        self.root.configure(bg="#0f172a")         # Azul muy oscuro y moderno (Slate 900)
        
        # Atajo para salir de la pantalla completa (Tecla ESC)
        self.root.bind("<Escape>", lambda e: self.cerrar_aplicacion())

        # --- Título y Subtítulo ---
        self.lbl_titulo = tk.Label(root, text="SISTEMA DE MONITOREO AMBIENTAL", 
                                   font=("Segoe UI", 36, "bold"), fg="#38bdf8", bg="#0f172a")
        self.lbl_titulo.pack(pady=(40, 10))

        self.lbl_autores = tk.Label(root, text="Hecho por: Ignacio Hernández Hernández, Brandon Javier Lara Cruz, Ronaldo Olvera Jiménez", 
                                    font=("Segoe UI", 16, "italic"), fg="#94a3b8", bg="#0f172a")
        self.lbl_autores.pack(pady=(0, 50))

        # --- Contenedor de Mediciones ---
        self.frame_mediciones = tk.Frame(root, bg="#0f172a")
        self.frame_mediciones.pack(expand=True)

        # Labels con valores y símbolos grandes
        self.lbl_temp = tk.Label(self.frame_mediciones, text="Temperatura: -- °C", 
                                 font=("Segoe UI", 48, "bold"), fg="#f87171", bg="#0f172a")
        self.lbl_temp.pack(pady=20)

        self.lbl_hum = tk.Label(self.frame_mediciones, text="Humedad: -- %", 
                                font=("Segoe UI", 48, "bold"), fg="#34d399", bg="#0f172a")
        self.lbl_hum.pack(pady=20)

        self.lbl_nivel = tk.Label(self.frame_mediciones, text="Nivel de Agua: -- m", 
                                  font=("Segoe UI", 48, "bold"), fg="#60a5fa", bg="#0f172a")
        self.lbl_nivel.pack(pady=20)

        # --- Estado de conexión ---
        self.lbl_estado = tk.Label(root, text="Iniciando conexión... (Presiona ESC para salir)", 
                                   font=("Segoe UI", 14), fg="#facc15", bg="#0f172a")
        self.lbl_estado.pack(side="bottom", pady=20)

        # Variables para controlar el Pop-Up
        self.alerta_abierta = False
        self.ventana_alerta = None
        self.lbl_texto_alerta = None

        # Control del hilo
        self.ejecutando = True
        
        # Iniciar la lectura serial en un hilo separado
        self.hilo_serial = threading.Thread(target=self.leer_puerto_serial, daemon=True)
        self.hilo_serial.start()

        # Asegurar un cierre limpio
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)

    def leer_puerto_serial(self):
        while self.ejecutando:
            try:
                ser = serial.Serial(PUERTO, BAUDIOS, timeout=1)
                self.lbl_estado.config(text=f"Conectado a pines 8 y 10 ({PUERTO}) - Presiona ESC para salir", fg="#34d399")
                
                while self.ejecutando:
                    if ser.in_waiting > 0:
                        linea = ser.readline().decode('utf-8', errors='ignore').strip()
                        if linea:
                            self.analizar_trama(linea)
                            
                ser.close()
            except (serial.SerialException, FileNotFoundError):
                self.lbl_estado.config(text="Error: Revisa si el UART está activo en tu Raspberry Pi", fg="#f87171")
                time.sleep(2)

    def analizar_trama(self, cadena):
        patron = r"<T:(.*?);H:(.*?);N:(.*?)>" if ';' in cadena else r"<T:(.*?),H:(.*?),N:(.*?)>"
        match = re.search(patron, cadena)
        
        if match:
            try:
                temp = float(match.group(1))
                hum = float(match.group(2))
                nivel = float(match.group(3))
                
                # Actualizar GUI en el hilo principal
                self.root.after(0, self.actualizar_pantalla, temp, hum, nivel)
                self.root.after(0, self.gestionar_alerta, temp, hum, nivel)
            except ValueError:
                pass 

    def actualizar_pantalla(self, t, h, n):
        # Símbolos más grandes visualmente
        self.lbl_temp.config(text=f"Temperatura: {t:.2f} °C")
        self.lbl_hum.config(text=f"Humedad: {h:.1f} %")
        self.lbl_nivel.config(text=f"Nivel de Agua: {n:.3f} m")

    def evaluar_estados(self, t, h, n):
        # Lógica básica para clasificar estados (puedes ajustar los números)
        estado_t = "PELIGRO" if t > 30.0 else "ESTABLE"
        estado_h = "PELIGRO" if h > 80.0 else "ESTABLE"
        estado_n = "RIESGO" if n < 0.50 else "ESTABLE" # Menos distancia = Nivel de agua más alto

        reco = "Monitoreo en parámetros normales."
        if estado_t == "PELIGRO" or estado_h == "PELIGRO" or estado_n == "RIESGO":
            reco = "Alerta, el nivel de agua está subiendo. Evite zonas inundadas. Riesgo detectado."

        return estado_t, estado_h, estado_n, reco

    def gestionar_alerta(self, t, h, n):
        estado_t, estado_h, estado_n, reco = self.evaluar_estados(t, h, n)
        
        texto_alerta = (
            "----------------------------------\n"
            "ALERTA AMBIENTAL\n\n"
            f"Temperatura: {t:.2f} °C -> {estado_t}\n"
            f"Humedad: {h:.1f} % -> {estado_h}\n"
            f"Nivel Agua: {n:.3f} m -> {estado_n}\n\n"
            "Recomendación:\n"
            f"{reco}\n"
            "----------------------------------"
        )

        # Si no hay alerta abierta, crearla
        if not self.ventana_alerta or not self.ventana_alerta.winfo_exists():
            self.ventana_alerta = tk.Toplevel(self.root)
            self.ventana_alerta.title("Alerta")
            self.ventana_alerta.geometry("450x350")
            self.ventana_alerta.configure(bg="#1e293b")
            self.ventana_alerta.attributes("-topmost", True) # Siempre al frente

            self.lbl_texto_alerta = tk.Label(self.ventana_alerta, text=texto_alerta, 
                                             font=("Consolas", 14), fg="#f87171", bg="#1e293b", justify="left")
            self.lbl_texto_alerta.pack(expand=True, pady=20, padx=20)
            
            # Botón para cerrar la alerta manualmente
            btn_cerrar = tk.Button(self.ventana_alerta, text="ENTENDIDO", command=self.ventana_alerta.destroy, 
                                   font=("Segoe UI", 12, "bold"), bg="#334155", fg="white", relief="flat")
            btn_cerrar.pack(pady=10, ipadx=20, ipady=5)
        else:
            # Si ya está abierta, solo actualizar el texto para no trabar el programa
            self.lbl_texto_alerta.config(text=texto_alerta)

    def cerrar_aplicacion(self):
        self.ejecutando = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AppMonitoreoAZTECH(root)
    root.mainloop()