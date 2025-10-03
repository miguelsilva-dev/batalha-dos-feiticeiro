import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import random
import os
import sys

# --- VERIFICADOR DE ARQUIVOS ---
def verificar_arquivos(lista_de_arquivos):
    arquivos_faltando = []
    diretorio_base = os.path.dirname(os.path.abspath(__file__))
    for caminho_relativo in lista_de_arquivos:
        caminho_corrigido = os.path.join(*caminho_relativo.split('/'))
        caminho_absoluto = os.path.join(diretorio_base, caminho_corrigido)
        if not os.path.exists(caminho_absoluto):
            arquivos_faltando.append(caminho_absoluto)
    return arquivos_faltando

# --- LISTA CENTRAL DE TODOS OS RECURSOS ---
ARQUIVOS_NECESSARIOS = [
    "assets/sprites/player/feiticeiro.png", "assets/sprites/enemies/goblin.png",
    "assets/sprites/enemies/esqueleto.png", "assets/sprites/enemies/dragao.png",
    "assets/sprites/enemies/lobo.png", "assets/sprites/enemies/lich.png",
    "assets/sprites/effects/fogo.png", "assets/sprites/effects/gelo.png",
    "assets/sprites/effects/veneno.png", "assets/sprites/effects/escudo.png",
    "assets/sprites/effects/hit.png",
]

# --- CONSTANTES GERAIS E DE CONFIGURAÇÃO DO JOGO ---
ASSETS_PATH = 'assets'
FEITICOS = {
    1: {"nome": "Bola de Fogo", "dano": 35, "mana": 15, "efeito": "queimadura", "sprite": "fogo.png"},
    2: {"nome": "Raio Congelante", "dano": 25, "mana": 12, "efeito": "congelamento", "sprite": "gelo.png"},
    3: {"nome": "Chuva de Meteoros", "dano": 55, "mana": 25, "efeito": None, "sprite": "fogo.png"},
    4: {"nome": "Lança de Gelo", "dano": 30, "mana": 18, "efeito": None, "sprite": "gelo.png"},
    6: {"nome": "Drenar Vida", "dano": 20, "mana": 22, "efeito": "drenar", "sprite": "veneno.png"},
    7: {"nome": "Escudo Mágico", "dano": 0, "mana": 15, "efeito": "escudo", "sprite": "escudo.png"},
    8: {"nome": "Veneno Arcano", "dano": 15, "mana": 10, "efeito": "veneno", "sprite": "veneno.png"}
}

# --- CLASSES DE LÓGICA DO JOGO (MODEL) ---
class Personagem:
    def __init__(self):
        self.vida = 100; self.vida_max = 100; self.escudo = 0; self.veneno = 0
    def receber_dano(self, dano):
        dano_sofrido = dano; dano_absorvido = 0
        if self.escudo > 0:
            dano_absorvido = min(self.escudo, dano); dano_sofrido = dano - dano_absorvido
            self.escudo -= dano_absorvido
        self.vida = max(0, self.vida - dano_sofrido)
        return dano_sofrido, dano_absorvido

class Jogador(Personagem):
    def __init__(self, nome="Jogador"):
        super().__init__(); self.nome = nome; self.sprite_path = "player/feiticeiro.png"
        self.vida_max = 120; self.vida = 120; self.mana_max = 100; self.mana = 100
        self.nivel = 1; self.exp = 0; self.pocoes_vida = 4; self.pocoes_mana = 4
        self.queimadura = 0; self.congelado = 0; self.critico_bonus = 0; self.resistencia_magica = 0; self.ouro = 50
    def curar(self, q): self.vida = min(self.vida + q, self.vida_max)
    def recuperar_mana(self, q): self.mana = min(self.mana + q, self.mana_max)
    def ganhar_exp(self, q): self.exp += q; return self.subir_nivel() if self.exp >= self.nivel * 50 else False
    def subir_nivel(self):
        exp_overflow = self.exp - (self.nivel * 50); self.nivel += 1; self.vida_max += 20; self.mana_max += 15
        self.vida = self.vida_max; self.mana = self.mana_max; self.exp = exp_overflow; self.ouro += 30
        return True

class Inimigo(Personagem):
    def __init__(self, nome, vida, tipo="normal", sprite_path="enemies/goblin.png"):
        super().__init__(); self.nome = nome; self.vida_max = vida; self.vida = vida; self.tipo = tipo; self.sprite_path = sprite_path
        self.queimadura = 0; self.congelado = 0
        if tipo == "boss": self.vida_max = int(vida * 1.5); self.vida = self.vida_max

# --- CLASSE DE GERENCIAMENTO DE RECURSOS (COM REDIMENSIONAMENTO) ---
class SpriteManager:
    _cache = {}
    @classmethod
    def carregar_sprite(cls, path, width=None, height=None):
        cache_key = (path, width, height)
        if cache_key in cls._cache: return cls._cache[cache_key]
        
        full_path = os.path.join(ASSETS_PATH, 'sprites', path)
        try:
            image = tk.PhotoImage(file=full_path)
            
            if width and height:
                original_width = image.width()
                original_height = image.height()
                
                factor_x = max(1, original_width // width)
                factor_y = max(1, original_height // height)
                
                image = image.subsample(factor_x, factor_y)

            cls._cache[cache_key] = image
            return image
        except Exception as e:
            print(f"ERRO: Não foi possível carregar o sprite '{full_path}'. Sprite ficará invisível. Detalhe: {e}")
            return cls._criar_placeholder()
    
    @classmethod
    def _criar_placeholder(cls):
        return tk.PhotoImage(width=1, height=1)

# --- CLASSE DE LÓGICA PRINCIPAL (CONTROLLER) ---
class GameLogic:
    def __init__(self, jogador):
        self.jogador = jogador; self.inimigo = None; self.batalhas_vencidas = 0
    def iniciar_nova_batalha(self):
        inimigos_normais = [("Goblin Sombrio", 60, "enemies/goblin.png"), ("Esqueleto Arcano", 70, "enemies/esqueleto.png"), ("Lobo Espectral", 65, "enemies/lobo.png")]
        inimigos_boss = [("Dragão Ancião", 200, "enemies/dragao.png"), ("Lich Supremo", 240, "enemies/lich.png")]
        
        if (self.batalhas_vencidas) % 3 == 0 and self.batalhas_vencidas > 0:
            boss_escolhido = random.choices(inimigos_boss, weights=[60, 40], k=1)[0]
            nome, vida, sprite = boss_escolhido
            
            self.inimigo = Inimigo(nome, vida + (self.jogador.nivel * 10), "boss", sprite)
            return f"🔥 UM PODEROSO BOSS APARECEU! 🔥\n⚔️ {self.inimigo.nome} apareceu!", "boss"
        else:
            nome, vida, sprite = random.choice(inimigos_normais)
            self.inimigo = Inimigo(nome, vida + (self.jogador.nivel * 5), "normal", sprite)
            return f"⚔️ {self.inimigo.nome} apareceu para a batalha!", None

    def processar_vitoria(self):
        self.batalhas_vencidas += 1
        exp_base = 25 + self.inimigo.vida_max // 10; ouro_base = 15 + self.inimigo.vida_max // 15
        if self.inimigo.tipo == "boss": exp_base = int(exp_base * 2.5); ouro_base = int(ouro_base * 3)
        self.jogador.ouro += ouro_base; subiu_nivel = self.jogador.ganhar_exp(exp_base)
        logs = [(f"🏆 Vitória! {self.inimigo.nome} foi derrotado!", "vitoria"), (f"💰 Ganhou {ouro_base} de ouro e {exp_base} de EXP!", "ouro")]
        if subiu_nivel: logs.extend([(f"🌟 NÍVEL SUPERIOR! {self.jogador.nome} subiu para o nível {self.jogador.nivel}!", "nivel"), ("💎 Vida e mana restauradas!", "cura")])
        
        # Lógica de encontrar poções de vida
        chance_vida = random.choices([0, 1, 2, 3], weights=[60, 25, 10, 5], k=1)[0]
        if chance_vida > 0:
            self.jogador.pocoes_vida += chance_vida
            if chance_vida == 1:
                logs.append(("🧪 Você encontrou uma Poção de Vida!", "cura"))
            else:
                logs.append((f"🧪 Você encontrou {chance_vida} Poções de Vida!", "cura"))

        # Lógica de encontrar poções de mana (com maior probabilidade)
        chance_mana = random.choices([0, 1, 2, 3], weights=[50, 30, 15, 5], k=1)[0]
        if chance_mana > 0:
            self.jogador.pocoes_mana += chance_mana
            if chance_mana == 1:
                logs.append(("💧 Você encontrou uma Poção de Mana!", "cura"))
            else:
                logs.append((f"💧 Você encontrou {chance_mana} Poções de Mana!", "cura"))
        
        return logs

# --- INTERFACE GRÁFICA (VIEW) ---
class BatalhaGUI:
    def __init__(self, root):
        self.root = root; self.root.title("🔮 Batalha dos Feiticeiros")
        self.root.attributes('-fullscreen', True); self.fullscreen_state = True
        self.root.bind("<F11>", self.toggle_fullscreen); self.root.bind("<Escape>", self.toggle_fullscreen)
        self.root.configure(bg='#0a0a1a')
        self.style = ttk.Style(); self.style.theme_use('clam')
        self.style.configure("Vida.Horizontal.TProgressbar", background='#2ecc71', troughcolor='#333')
        self.style.configure("VidaBaixa.Horizontal.TProgressbar", background='#e74c3c', troughcolor='#333')
        self.style.configure("Mana.Horizontal.TProgressbar", background='#3498db', troughcolor='#333')
        self.jogador = None; self.game_logic = None; self.em_batalha = False; self.processando_turno = False; self.turno_jogador = True
        self.sprite_ref_jogador = None; self.sprite_ref_inimigo = None; self.sprite_ref_efeito = []
        self.initial_positioning_done = False
        self.criar_tela_inicial()

    def toggle_fullscreen(self, event=None):
        self.fullscreen_state = not self.fullscreen_state
        self.root.attributes("-fullscreen", self.fullscreen_state)
        return "break"

    def criar_tela_inicial(self):
        self.frame_inicial = tk.Frame(self.root, bg='#0a0a1a'); self.frame_inicial.pack(fill='both', expand=True, padx=20, pady=20)
        tk.Label(self.frame_inicial, text="Batalha dos Feiticeiros", font=('Arial', 32, 'bold'), bg='#0a0a1a', fg='#ffd700').pack(pady=20)
        tk.Label(self.frame_inicial, text="Digite seu nome, nobre feiticeiro:", font=('Arial', 16), bg='#0a0a1a', fg='white').pack(pady=10)
        self.entry_nome = tk.Entry(self.frame_inicial, font=('Arial', 16), width=25, justify='center', bg='#333', fg='white', insertbackground='white'); self.entry_nome.pack(pady=10)
        self.entry_nome.focus()
        frame_ajuda = tk.LabelFrame(self.frame_inicial, text="📜 Como Jogar 📜", font=('Arial', 12, 'bold'), bg='#16213e', fg='white', bd=2, relief='ridge')
        frame_ajuda.pack(pady=20, padx=10, fill='x')
        texto_ajuda = """
        • O objetivo é derrotar os inimigos em batalhas de turno.
        • Use os feitiços para atacar. Feitiços mais fortes têm menor chance de acerto.
        • Use as poções para recuperar vida (❤️) ou mana (💧).
        • A cada 3 vitórias, um chefe (Boss) poderoso aparecerá.
        • Pressione F11 para alternar tela cheia e ESC para sair da tela cheia.
        """
        tk.Label(frame_ajuda, text=texto_ajuda, font=('Arial', 10), bg='#16213e', fg='white', justify='left').pack(padx=10, pady=5)
        tk.Button(self.frame_inicial, text="⚔️ Iniciar Aventura ⚔️", font=('Arial', 18, 'bold'), bg='#667eea', fg='white', command=self.iniciar_jogo, relief='raised', bd=3, padx=10, pady=5).pack(pady=20)
        self.entry_nome.bind('<Return>', lambda e: self.iniciar_jogo())
    
    def iniciar_jogo(self):
        nome = self.entry_nome.get().strip() or "Mago Misterioso"; self.jogador = Jogador(nome); self.game_logic = GameLogic(self.jogador)
        self.frame_inicial.destroy(); self.criar_interface_principal(); self.nova_batalha()
    
    def criar_interface_principal(self):
        self.frame_principal = tk.Frame(self.root, bg='#0a0a1a'); self.frame_principal.pack(fill='both', expand=True, padx=10, pady=10)
        self.criar_frame_status()
        self.criar_arena_batalha()
        self.criar_log_batalha()
        self.criar_frame_acoes()
    
    def criar_arena_batalha(self):
        self.frame_arena = tk.LabelFrame(self.frame_principal, text="⚔️ ARENA DE BATALHA ⚔️", font=('Arial', 14, 'bold'), bg='#0f0f23', fg='#ffd700', bd=2, relief='ridge')
        self.frame_arena.pack(fill='both', expand=True, pady=5, side=tk.TOP)
        self.canvas_batalha = tk.Canvas(self.frame_arena, bg='white', highlightthickness=0)
        self.canvas_batalha.pack(fill='both', expand=True, pady=10)
        self.pos_jogador = (200, 150); self.pos_inimigo = (600, 150)
        self.canvas_batalha.bind("<Configure>", self.on_canvas_configure)

    def on_canvas_configure(self, event=None):
        if not self.initial_positioning_done:
            self.posicionar_personagens()
            self.initial_positioning_done = True
    
    def criar_frame_status(self):
        frame_status = tk.Frame(self.frame_principal, bg='#0a0a1a')
        frame_status.pack(fill='x', pady=5, side=tk.TOP)
        self.frame_jogador = tk.LabelFrame(frame_status, text="Seus Atributos", font=('Arial', 12), bg='#16213e', fg='#4facfe'); self.frame_jogador.pack(side='left', fill='x', expand=True, padx=5, pady=5)
        self.label_vida_jogador = tk.Label(self.frame_jogador, text="Vida:", bg='#16213e', fg='white', font=('Consolas', 10)); self.label_vida_jogador.pack(anchor='w', padx=5, pady=(5,0))
        self.barra_vida_jogador = ttk.Progressbar(self.frame_jogador, length=100, style="Vida.Horizontal.TProgressbar"); self.barra_vida_jogador.pack(fill='x', padx=5, pady=(0,5))
        self.label_mana_jogador = tk.Label(self.frame_jogador, text="Mana:", bg='#16213e', fg='white', font=('Consolas', 10)); self.label_mana_jogador.pack(anchor='w', padx=5)
        self.barra_mana_jogador = ttk.Progressbar(self.frame_jogador, length=100, style="Mana.Horizontal.TProgressbar"); self.barra_mana_jogador.pack(fill='x', padx=5, pady=(0,5))
        self.label_status_jogador = tk.Label(self.frame_jogador, text="", bg='#16213e', fg='yellow', font=('Consolas', 10)); self.label_status_jogador.pack(anchor='w', padx=5)
        self.frame_inimigo = tk.LabelFrame(frame_status, text="Inimigo", font=('Arial', 12), bg='#16213e', fg='#fc466b'); self.frame_inimigo.pack(side='right', fill='x', expand=True, padx=5, pady=5)
        self.label_vida_inimigo = tk.Label(self.frame_inimigo, text="Vida:", bg='#16213e', fg='white', font=('Consolas', 10)); self.label_vida_inimigo.pack(anchor='w', padx=5, pady=(5,0))
        self.barra_vida_inimigo = ttk.Progressbar(self.frame_inimigo, length=100, style="Vida.Horizontal.TProgressbar"); self.barra_vida_inimigo.pack(fill='x', padx=5, pady=(0,5))
        self.label_status_inimigo = tk.Label(self.frame_inimigo, text="", bg='#16213e', fg='orange', font=('Consolas', 10)); self.label_status_inimigo.pack(anchor='w', padx=5)
    
    def criar_log_batalha(self):
        frame_log = tk.LabelFrame(self.frame_principal, text="📜 Crônicas da Batalha 📜", font=('Arial', 12, 'bold'), bg='#16213e', fg='white')
        frame_log.pack(fill='x', pady=5, side=tk.BOTTOM)
        self.log_batalha = scrolledtext.ScrolledText(frame_log, height=6, bg='#0f0f23', fg='white', font=('Consolas', 10), state='disabled', wrap=tk.WORD, bd=0); self.log_batalha.pack(fill='both', expand=True, padx=5, pady=5)
        tags = {"vitoria": "#2ecc71", "erro": "#e74c3c", "ouro": "#f1c40f", "nivel": "#3498db", "boss": "#9b59b6", "turno": "#1abc9c", "cura": "#27ae60", "veneno":"#27ae60", "escudo":"#3498db"}; [self.log_batalha.tag_config(t, foreground=c, font=('Consolas',10,'bold')) for t,c in tags.items()]
    
    def criar_frame_acoes(self):
        frame_acoes = tk.LabelFrame(self.frame_principal, text="✨ Ações ✨", font=('Arial', 12, 'bold'), bg='#16213e', fg='white')
        frame_acoes.pack(fill='x', pady=5, side=tk.BOTTOM)
        frame_feiticos_container = tk.Frame(frame_acoes, bg='#16213e'); frame_feiticos_container.pack(side='left', fill='x', expand=True, padx=5)
        tk.Label(frame_feiticos_container, text="Arsenal Mágico", font=('Arial', 10, 'bold'), bg='#16213e', fg='white').pack()
        self.botoes_feiticos = {}; frame_feiticos = tk.Frame(frame_feiticos_container, bg='#16213e'); frame_feiticos.pack(pady=5)
        max_cols = 4; col, row = 0, 0
        for i, feitico in FEITICOS.items():
            btn = tk.Button(frame_feiticos, text=f"{feitico['nome']} [{i}]", command=lambda num=i: self.usar_feitico(num), bg='#444', fg='white', relief='raised', bd=2); btn.grid(row=row, column=col, padx=5, pady=3, sticky='ew')
            self.botoes_feiticos[i] = btn; col += 1
            if col >= max_cols: col = 0; row += 1
        frame_itens_container = tk.Frame(frame_acoes, bg='#16213e'); frame_itens_container.pack(side='right', fill='x', expand=True, padx=5)
        tk.Label(frame_itens_container, text="Bolsa de Itens", font=('Arial', 10, 'bold'), bg='#16213e', fg='white').pack()
        frame_itens = tk.Frame(frame_itens_container, bg='#16213e'); frame_itens.pack(pady=5)
        self.btn_pocao_vida = tk.Button(frame_itens, text=f"❤️ Poção de Vida", command=lambda: self.usar_pocao('vida'), bg='#27ae60', fg='white', relief='raised', bd=2); self.btn_pocao_vida.pack(pady=3, fill='x')
        self.btn_pocao_mana = tk.Button(frame_itens, text=f"💧 Poção de Mana", command=lambda: self.usar_pocao('mana'), bg='#2980b9', fg='white', relief='raised', bd=2); self.btn_pocao_mana.pack(pady=3, fill='x')
    
    def log(self, m, t=None): self.log_batalha.config(state='normal'); self.log_batalha.insert('end', f"{m}\n", t); self.log_batalha.see('end'); self.log_batalha.config(state='disabled')
    
    def posicionar_personagens(self):
        canvas_w = self.canvas_batalha.winfo_width(); canvas_h = self.canvas_batalha.winfo_height()
        if canvas_w <= 1 or canvas_h <= 1: return
        self.pos_jogador = (canvas_w * 0.25, canvas_h * 0.6); self.pos_inimigo = (canvas_w * 0.75, canvas_h * 0.6)
        self.canvas_batalha.delete("sprites")
        
        player_w, player_h = 80, 80
        
        if self.jogador: 
            self.sprite_ref_jogador = SpriteManager.carregar_sprite(self.jogador.sprite_path, width=player_w, height=player_h)
            self.canvas_batalha.create_image(*self.pos_jogador, image=self.sprite_ref_jogador, tags=("sprites", "jogador_sprite"))
        
        if self.game_logic and self.game_logic.inimigo: 
            inimigo = self.game_logic.inimigo
            
            if inimigo.tipo == 'boss':
                enemy_w, enemy_h = 110, 110 
            else:
                enemy_w, enemy_h = player_w, player_h

            self.sprite_ref_inimigo = SpriteManager.carregar_sprite(inimigo.sprite_path, width=enemy_w, height=enemy_h)
            self.canvas_batalha.create_image(*self.pos_inimigo, image=self.sprite_ref_inimigo, tags=("sprites", "inimigo_sprite"))

    def animar_chuva_de_meteoros(self, callback, alvo='inimigo'):
        num_meteoros = 4
        self.sprite_ref_efeito.clear()
        
        if alvo == 'inimigo':
            alvo_x, alvo_y = self.pos_inimigo
        else: 
            alvo_x, alvo_y = self.pos_jogador

        for i in range(num_meteoros):
            sprite_efeito = SpriteManager.carregar_sprite('effects/fogo.png', width=35, height=35)
            self.sprite_ref_efeito.append(sprite_efeito)
            x_inicial = alvo_x + random.randint(-150, 150); y_inicial = -30
            x_final = alvo_x + random.randint(-40, 40)
            meteoro_id = self.canvas_batalha.create_image(x_inicial, y_inicial, image=sprite_efeito, tags=f"meteoro_{i}")
            is_last_meteor = (i == num_meteoros - 1)
            self.root.after(i * 200, self._animar_um_meteoro, meteoro_id, x_final, alvo_y, is_last_meteor, callback)

    def _animar_um_meteoro(self, meteoro_id, x_final, y_final, is_last, callback, frame=0, total_frames=15):
        if frame <= total_frames:
            try:
                coords_atuais = self.canvas_batalha.coords(meteoro_id)
                if not coords_atuais: return
                x1, y1 = coords_atuais; t = frame / total_frames
                novo_x = x1 + (x_final - x1) * t; novo_y = y1 + (y_final - y1) * t
                self.canvas_batalha.coords(meteoro_id, novo_x, novo_y)
                self.root.after(16, self._animar_um_meteoro, meteoro_id, x_final, y_final, is_last, callback, frame + 1)
            except tk.TclError: return
        else:
            alvo_tag = "inimigo" if (x_final, y_final) == self.pos_inimigo else "jogador"
            self.canvas_batalha.delete(meteoro_id); self.animar_impacto((x_final, y_final), alvo_tag)
            if is_last and callback: self.root.after(200, callback)

    def animar_projetil(self, n, o, d, cb):
        fi = FEITICOS.get(n); sp = os.path.join('effects', fi['sprite'])
        sprite_efeito = SpriteManager.carregar_sprite(sp, width=40, height=40)
        self.sprite_ref_efeito = [sprite_efeito]
        x1, y1 = o; x2, y2 = d; tf = 15
        def _a(f=0):
            if f <= tf: t = f / tf; x = x1 + (x2 - x1) * t; y = y1 + (y2 - y1) * t; self.canvas_batalha.delete("efeito_temp"); self.canvas_batalha.create_image(x, y, image=self.sprite_ref_efeito[0], tags="efeito_temp"); self.root.after(16, lambda: _a(f + 1))
            else: self.canvas_batalha.delete("efeito_temp"); self.animar_impacto(d, "inimigo" if d == self.pos_inimigo else "jogador"); self.root.after(200, cb) if cb else None
        _a()
        
    def animar_impacto(self, p, ta):
        x, y = p
        sprite_hit = SpriteManager.carregar_sprite('effects/hit.png', width=60, height=60)
        self.sprite_ref_efeito.append(sprite_hit)
        id_hit = self.canvas_batalha.create_image(x, y, image=sprite_hit, tags="impacto")
        self.root.after(300, lambda: self.canvas_batalha.delete(id_hit))

        ai = self.canvas_batalha.find_withtag(f"{ta}_sprite")
        if not ai: return
        def _t(f=0):
            if f < 6: 
                try:
                    o = random.choice([-3, 3]); self.canvas_batalha.move(ai[0], o, 0)
                    self.root.after(40, lambda: _t(f + 1))
                except tk.TclError:
                    return
        _t()

    def nova_batalha(self):
        self.em_batalha = True; self.turno_jogador = True; self.processando_turno = False
        m, t = self.game_logic.iniciar_nova_batalha(); self.log(m, t); self.log("É o seu turno! Escolha uma magia.", "turno"); self.atualizar_interface()
    
    def usar_feitico(self, n):
        if self.processando_turno or not self.turno_jogador: return
        f = FEITICOS[n]
        if self.jogador.mana < f["mana"]: self.log("Mana insuficiente!", "erro"); return
        self.processando_turno = True; self.desabilitar_acoes(); self.jogador.mana -= f["mana"]
        
        chance_acerto = (100 - f['dano']) + self.jogador.nivel * 1
        chance_acerto = min(100, chance_acerto)
        acertou = random.randint(1, 100) <= chance_acerto
        
        def cb():
            if acertou:
                d = f['dano'] + random.randint(-5, 5) + self.jogador.nivel * 2
                self.game_logic.inimigo.receber_dano(d)
                self.log(f"Você usou {f['nome']} e causou {d} de dano! ({chance_acerto}% de chance)")
                if f['efeito'] == 'escudo':
                    valor_escudo = 40 + self.jogador.nivel * 5; self.jogador.escudo += valor_escudo
                    self.log(f"🛡️ Você conjurou um escudo que absorverá {valor_escudo} de dano!", "escudo")
                elif f['efeito'] == 'veneno':
                    self.game_logic.inimigo.veneno = 3
                    self.log(f"🐍 O inimigo foi envenenado!", "veneno")
            else: self.log(f"Você usou {f['nome']} mas errou o alvo! ({chance_acerto}% de chance)", "erro")
            self.atualizar_interface(); self.root.after(1500, self.verificar_fim_batalha)
        
        if n == 3: self.animar_chuva_de_meteoros(cb, alvo='inimigo')
        else: self.animar_projetil(n, self.pos_jogador, self.pos_inimigo if f['efeito'] != 'escudo' else self.pos_jogador, cb)

    def usar_pocao(self, tipo):
        if self.processando_turno or not self.turno_jogador: return
        if tipo == 'vida':
            if self.jogador.pocoes_vida <= 0: self.log("Você não tem mais poções de vida!", "erro"); return
            if self.jogador.vida == self.jogador.vida_max: self.log("Sua vida já está cheia!", "erro"); return
            self.jogador.pocoes_vida -= 1; cura = 50 + self.jogador.nivel * 5; self.jogador.curar(cura)
            self.log(f"🧪 Você usou uma poção e recuperou {cura} de vida!", "cura")
        elif tipo == 'mana':
            if self.jogador.pocoes_mana <= 0: self.log("Você não tem mais poções de mana!", "erro"); return
            if self.jogador.mana == self.jogador.mana_max: self.log("Sua mana já está cheia!", "erro"); return
            self.jogador.pocoes_mana -= 1; recuperacao = 40 + self.jogador.nivel * 3; self.jogador.recuperar_mana(recuperacao)
            self.log(f"💧 Você usou uma poção e recuperou {recuperacao} de mana!", "cura")
        self.processando_turno = True; self.desabilitar_acoes(); self.atualizar_interface()
        self.root.after(1500, self.finalizar_turno_jogador)
    
    def processar_efeitos_de_status(self, personagem, nome_personagem, e_jogador):
        if personagem.veneno > 0:
            dano_veneno = 10 + self.jogador.nivel * 2
            dano_sofrido, _ = personagem.receber_dano(dano_veneno)
            self.log(f"🐍 {nome_personagem} sofreu {dano_sofrido} de dano de veneno!", "veneno" if not e_jogador else "erro")
            personagem.veneno -= 1
    
    def verificar_fim_batalha(self):
        if self.game_logic.inimigo.vida <= 0: self.vitoria()
        elif self.jogador.vida <= 0: self.derrota()
        else: self.finalizar_turno_jogador()
        
    def finalizar_turno_jogador(self):
        self.processar_efeitos_de_status(self.jogador, self.jogador.nome, True)
        self.atualizar_interface()
        if self.jogador.vida <= 0: self.derrota(); return
        self.turno_jogador = False
        self.log(f"Turno de {self.game_logic.inimigo.nome}...", "turno")
        self.root.after(1200, self.processar_turno_inimigo)
        
    def processar_turno_inimigo(self):
        inimigo = self.game_logic.inimigo
        if random.randint(1, 100) > 80:
            self.log(f"{inimigo.nome} atacou mas errou!", "vitoria")
            self.root.after(1500, self.finalizar_turno_inimigo); return
        
        ataques_normais = [1, 2, 4]; ataques_boss = [1, 3, 8]
        ataque_visual = random.choice(ataques_boss if inimigo.tipo == 'boss' else ataques_normais)

        def cb():
            if inimigo.tipo == 'boss':
                dano_base = 20 + random.randint(self.jogador.nivel * 2, self.jogador.nivel * 4)
                if 'Lich' in inimigo.nome:
                    dano_base *= 1.2
            else:
                dano_base = 10 + random.randint(0, self.jogador.nivel * 2)
            
            dano_final = int(dano_base)
            dano_sofrido, dano_absorvido = self.jogador.receber_dano(dano_final)
            
            if dano_absorvido > 0: self.log(f"🛡️ Seu escudo absorveu {dano_absorvido} de dano!", "escudo")
            self.log(f"{inimigo.nome} ataca e causa {dano_sofrido} de dano!", "erro")
            self.atualizar_interface(); self.root.after(1000, self.finalizar_turno_inimigo)

        if ataque_visual == 3 and inimigo.tipo == 'boss':
            self.animar_chuva_de_meteoros(cb, alvo='jogador')
        else:
            self.animar_projetil(ataque_visual, self.pos_inimigo, self.pos_jogador, cb)

    def finalizar_turno_inimigo(self):
        self.processar_efeitos_de_status(self.game_logic.inimigo, self.game_logic.inimigo.nome, False)
        self.atualizar_interface()
        if self.game_logic.inimigo.vida <= 0: self.vitoria(); return
        if self.jogador.vida <= 0: self.derrota(); return
        self.turno_jogador = True; self.processando_turno = False; self.log("Seu turno novamente!", "turno"); self.atualizar_interface()
        
    def vitoria(self):
        self.em_batalha = False; logs = self.game_logic.processar_vitoria(); [self.log(m, t) for m,t in logs]
        self.atualizar_interface(); self.root.after(6000, self.nova_batalha)
        
    def derrota(self):
        self.em_batalha = False; self.log("💀 Você foi derrotado... 💀", "erro")
        if messagebox.askyesno("Fim de Jogo", "Você foi derrotado!\nDeseja tentar novamente?"):
            self.jogador.vida = self.jogador.vida_max; self.jogador.ouro = max(0, self.jogador.ouro - 50); self.nova_batalha()
        else: self.root.quit()
        
    def desabilitar_acoes(self):
        for btn in self.botoes_feiticos.values(): btn.config(state='disabled')
        self.btn_pocao_vida.config(state='disabled'); self.btn_pocao_mana.config(state='disabled')
        
    def habilitar_acoes(self):
        for btn in self.botoes_feiticos.values(): btn.config(state='normal')
        self.btn_pocao_vida.config(state='normal'); self.btn_pocao_mana.config(state='normal')
        
    def atualizar_interface(self):
        if not self.jogador: return
        if self.turno_jogador and not self.processando_turno: self.habilitar_acoes()
        else: self.desabilitar_acoes()
        self.frame_jogador.config(text=f"🧙‍♂️ {self.jogador.nome} (Nível {self.jogador.nivel})")
        vida_pct = (self.jogador.vida / self.jogador.vida_max) * 100
        self.label_vida_jogador.config(text=f"❤️ Vida: {self.jogador.vida} / {self.jogador.vida_max}"); self.barra_vida_jogador['value'] = vida_pct
        if vida_pct <= 30: self.barra_vida_jogador.config(style="VidaBaixa.Horizontal.TProgressbar")
        else: self.barra_vida_jogador.config(style="Vida.Horizontal.TProgressbar")
        self.label_mana_jogador.config(text=f"💙 Mana: {self.jogador.mana} / {self.jogador.mana_max}"); self.barra_mana_jogador['value'] = (self.jogador.mana / self.jogador.mana_max) * 100
        status_jogador_txt = f"🛡️ Escudo: {self.jogador.escudo}" if self.jogador.escudo > 0 else ""
        if self.jogador.veneno > 0: status_jogador_txt += f" 🐍 Veneno ({self.jogador.veneno}t)"
        self.label_status_jogador.config(text=status_jogador_txt)
        if self.game_logic.inimigo:
            i = self.game_logic.inimigo; ts = f" (BOSS)" if i.tipo == 'boss' else ""
            self.frame_inimigo.config(text=f"👹 {i.nome}{ts}"); self.label_vida_inimigo.config(text=f"❤️ Vida: {i.vida} / {i.vida_max}")
            self.barra_vida_inimigo['value'] = (i.vida / i.vida_max) * 100
            status_inimigo_txt = f"🛡️ Escudo: {i.escudo}" if i.escudo > 0 else ""
            if i.veneno > 0: status_inimigo_txt += f" 🐍 Veneno ({i.veneno}t)"
            self.label_status_inimigo.config(text=status_inimigo_txt)
        self.btn_pocao_vida.config(text=f"❤️ Poção de Vida ({self.jogador.pocoes_vida})")
        self.btn_pocao_mana.config(text=f"💧 Poção de Mana ({self.jogador.pocoes_mana})")
        self.posicionar_personagens(); self.root.update_idletasks()

# --- PONTO DE ENTRADA PRINCIPAL ---
if __name__ == "__main__":
    arquivos_problematicos = verificar_arquivos(ARQUIVOS_NECESSARIOS)
    if arquivos_problematicos:
        root_erro = tk.Tk(); root_erro.withdraw()
        mensagem_erro = "O jogo não pode iniciar porque um ou mais arquivos de imagem não foram encontrados no local esperado.\n\nVerifique os seguintes caminhos:\n\n"
        for caminho in arquivos_problematicos: mensagem_erro += f"- {caminho}\n"
        messagebox.showerror("Erro Crítico - Arquivos Não Encontrados", mensagem_erro)
        sys.exit()
    root = tk.Tk()
    app = BatalhaGUI(root)
    root.mainloop()