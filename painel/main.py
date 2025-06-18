import customtkinter as ctk
from PIL import Image
import requests
import tkinter as tk

SERVER_URL = "http://127.0.0.1:5000"

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

class CyberManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Carb0n Cyber Manager")
        self.geometry("750x650")

        self.status_atual = []
        self.tempo_restante_local = []  # tempo em segundos por PC
        self.monitores = []
        self.monitor_widgets = []
        self.pc_nomes = []

        self.label_title = ctk.CTkLabel(self, text="Carb0n Cyber Manager", font=("Arial", 24))
        self.label_title.pack(pady=10)

        self.grid_frame = ctk.CTkFrame(self)
        self.grid_frame.pack(pady=10)

        self.carregar_imagens()
        self.criar_grade()
        self.atualizar_status()
        self.relogio_local()  # inicia contagem local

    def carregar_imagens(self):
        self.imagens = {
            "livre": ctk.CTkImage(Image.open("icons/monitor_livre.png"), size=(128, 128)),
            "ocupado": ctk.CTkImage(Image.open("icons/monitor_ocupado.png"), size=(128, 128)),
            "admin": ctk.CTkImage(Image.open("icons/monitor_admin.png"), size=(128, 128)),
            "offline": ctk.CTkImage(Image.open("icons/monitor_offline.png"), size=(128, 128)),
        }

    def criar_grade(self):
        for i in range(3):
            for j in range(2):
                index = i * 2 + j
                frame = ctk.CTkFrame(self.grid_frame)
                frame.grid(row=i, column=j, padx=20, pady=20)

                image_label = ctk.CTkLabel(frame, text="", image=None)
                text_label = ctk.CTkLabel(frame, text="Carregando...", font=("Arial", 14))

                image_label.pack()
                text_label.pack()

                self.monitores.append((image_label, text_label))
                self.monitor_widgets.append(frame)
                nome_pc = f"PC0{index+1}" if index + 1 < 10 else f"PC{index+1}"
                self.pc_nomes.append(nome_pc)
                self.tempo_restante_local.append(0)

                for widget in (frame, image_label, text_label):
                    widget.bind("<Button-3>", lambda e, idx=index: self.abrir_menu_monitor(e, idx))

    def abrir_menu_monitor(self, event, idx):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Iniciar", command=lambda: self.abrir_tela_tempo(self.pc_nomes[idx]))
        menu.add_command(label="Encerrar", command=lambda: self.encerrar_pc(self.pc_nomes[idx]))
        menu.tk_popup(event.x_root, event.y_root)
    def encerrar_pc(self, nome_pc):
        try:
            r = requests.post(f"{SERVER_URL}/encerrar", json={"pc": nome_pc})
            self.atualizar_status()
        except Exception as e:
            print(f"Erro ao encerrar {nome_pc}: {e}")



    def abrir_tela_tempo(self, nome_pc):
        janela = ctk.CTkToplevel(self)
        janela.title(f"Iniciar {nome_pc}")
        janela.geometry("300x300")

        ctk.CTkLabel(janela, text=f"Definir tempo para {nome_pc}", font=("Arial", 16)).pack(pady=10)

        frame_botoes = ctk.CTkFrame(janela)
        frame_botoes.pack(pady=10)

        tempos = [30, 60, 90, 120, 180]
        for t in tempos:
            ctk.CTkButton(frame_botoes, text=f"{t} min", command=lambda t=t: self.iniciar_pc_com_tempo(nome_pc, t, janela)).pack(pady=2)

        ctk.CTkLabel(janela, text="Tempo personalizado (min):").pack(pady=10)
        entry_tempo = ctk.CTkEntry(janela)
        entry_tempo.pack(pady=5)

        def confirmar_personalizado():
            try:
                tempo = int(entry_tempo.get())
                self.iniciar_pc_com_tempo(nome_pc, tempo, janela)
            except:
                entry_tempo.delete(0, "end")
                entry_tempo.insert(0, "Inválido")

        ctk.CTkButton(janela, text="Confirmar", command=confirmar_personalizado).pack(pady=10)

    def iniciar_pc_com_tempo(self, nome_pc, tempo, janela=None):
        try:
            r = requests.post(f"{SERVER_URL}/iniciar", json={"pc": nome_pc, "tempo_minutos": tempo})
            if janela:
                janela.destroy()
            self.atualizar_status()
        except Exception as e:
            print(f"Erro ao iniciar {nome_pc}: {e}")

    def atualizar_status(self):
        try:
            r = requests.get(f"{SERVER_URL}/status")
            pcs = r.json()
            self.status_atual = pcs
        except:
            self.status_atual = []

        for i in range(len(self.monitores)):
            image_label, text_label = self.monitores[i]
            if i < len(self.status_atual):
                pc = self.status_atual[i]
                nome = pc['pc']
                status = pc['status']
                tempo_segundos = pc['tempo_restante']  # já vem em segundos

                self.tempo_restante_local[i] = tempo_segundos  # atualiza contador local

                if status == "livre":
                    image_label.configure(image=self.imagens["livre"])
                    text_label.configure(text=f"{nome}\nLivre")
                elif status == "ocupado":
                    image_label.configure(image=self.imagens["ocupado"])
                    text_label.configure(text=f"{nome}\n{self.formatar_tempo(tempo_segundos)}")
                elif status == "admin":
                    image_label.configure(image=self.imagens["admin"])
                    text_label.configure(text=f"{nome}\nAdmin")
                elif status == "offline":
                    image_label.configure(image=self.imagens["offline"])
                    text_label.configure(text=f"{nome}\nSem conexão")
                else:
                    image_label.configure(image=self.imagens["offline"])
                    text_label.configure(text=f"{nome}\nDesconhecido")
            else:
                image_label.configure(image=None)
                text_label.configure(text="")

        self.after(5000, self.atualizar_status)  # sincroniza com servidor a cada 5s

    def relogio_local(self):
        for i in range(len(self.status_atual)):
            pc = self.status_atual[i]
            nome = pc['pc']
            status = pc['status']

            if status == "ocupado" and self.tempo_restante_local[i] > 0:
                self.tempo_restante_local[i] -= 1
                tempo_formatado = self.formatar_tempo(self.tempo_restante_local[i])
                _, text_label = self.monitores[i]
                text_label.configure(text=f"{nome}\n{tempo_formatado}")
        self.after(1000, self.relogio_local)  # atualiza a cada segundo

    def formatar_tempo(self, total_segundos):
        h = total_segundos // 3600
        m = (total_segundos % 3600) // 60
        s = total_segundos % 60
        return f"{h:02d}:{m:02d}:{s:02d}"


if __name__ == "__main__":
    app = CyberManagerApp()
    app.mainloop()
