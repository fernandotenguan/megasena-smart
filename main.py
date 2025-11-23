# main.py
from flask import Flask, render_template, g, request 
import sqlite3
import os
import time
import random
from collections import Counter, defaultdict

# Importações do seu projeto
from app.util.estatisticas import (
    carregar_todos_resultados, 
    analisar_basicos, 
    analisar_iniciais_finais, 
    analisar_sequenciais, 
    analisar_repetidas_anterior, 
    analisar_somas_distribuicao,
    analisar_frequencia_periodo_distribuicao,
    analisar_frequencia_geral, 
    analisar_pares_impares,
    analisar_distribuicao_maximas,
    analisar_distribuicao_quadrantes,
    analisar_ciclos,
    analisar_padrao_linhas_colunas,
    analisar_atrasos,
    analisar_deltas
)
from app.util.config_mega import DATABASE_NAME, LISTA_PRIMOS, LISTA_FIBONACCI, LISTA_MULTIPLOS_3
from app.util.analise_preditiva import gerar_perfil_preditivo_completo, extrair_perfil_alvo_completo
from app.util.gerador import gerar_universo_filtrado
from app.util.pontuacao import calcular_pontuacao_binaria
from app.util.simulation import simular_cenario_passado
from app.util.similarity import buscar_concursos_similares

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, DATABASE_NAME)

# --- CONFIGURAÇÃO DO BANCO ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- ROTA PRINCIPAL (DASHBOARD) ---
@app.route('/')
def index():
    df = carregar_todos_resultados(DB_PATH)
    if df.empty: return "Erro: Banco vazio."
    ultimo = df.iloc[-1].to_dict()
    
    freq_geral, top_10, bottom_10 = analisar_frequencia_geral(df)
    stats_pares = analisar_pares_impares(df)
    stats_soma_dist = analisar_somas_distribuicao(df)
    basicos = analisar_basicos(df)
    ini, fim = analisar_iniciais_finais(df)
    sequencias = analisar_sequenciais(df)
    rep_anterior = analisar_repetidas_anterior(df)
    stats_quadrantes = analisar_distribuicao_quadrantes(df)
    rep_39_dist = analisar_frequencia_periodo_distribuicao(df, 39)
    rep_21_dist = analisar_frequencia_periodo_distribuicao(df, 21)
    dist_max_39 = analisar_distribuicao_maximas(df, 39)
    dist_max_21 = analisar_distribuicao_maximas(df, 21)
    ciclo_atual = analisar_ciclos(df)
    padrao_linhas_cols = analisar_padrao_linhas_colunas(df)
    ranking_atrasos = analisar_atrasos(df)
    dist_deltas = analisar_deltas(df)

    return render_template('index.html', 
                           ultimo_sorteio=ultimo,
                           freq_geral=freq_geral,
                           top_10=top_10,
                           bottom_10=bottom_10,
                           stats_pares=stats_pares,
                           stats_soma_dist=stats_soma_dist,
                           stats_primos=basicos['primos'],
                           stats_fibo=basicos['fibo'],
                           stats_mult3=basicos['mult3'],
                           stats_ini=ini,
                           stats_fim=fim,
                           stats_seq=sequencias,
                           stats_rep_ant=rep_anterior,
                           stats_rep_39=rep_39_dist,
                           stats_rep_21=rep_21_dist,
                           dist_max_39=dist_max_39,
                           dist_max_21=dist_max_21,
                           stats_quadrantes=stats_quadrantes,
                           ciclo_atual=ciclo_atual,
                           stats_lin_col=padrao_linhas_cols,
                           ranking_atrasos=ranking_atrasos,
                           dist_deltas=dist_deltas
                           )

# ==============================================================================
#                        MÓDULO PREDITIVO VISUAL (CORRIGIDO)
# ==============================================================================

# 1. HELPER: Formatação de Tags HTML (Sidebar)
def html_tags(dados, sufixo='', classe='tag'):
    if not dados: return '<span style="color:#999">-</span>'
    
    if isinstance(dados, list):
        html = ''
        for item in dados:
            val = str(item)
            if 'tag-quad' in classe:
                val = val.replace('-', '')
            html += f'<span class="{classe}">{val}{sufixo}</span>'
        return html
    return str(dados)

# 2. HELPER: Estilo Visual da Célula
def estilo_celula(match):
    """
    Retorna o CSS para a célula da tabela.
    Verde = Match Positivo (Pontuou Score)
    Cinza = Não Pontuou
    """
    if match:
        # Verde Sucesso
        return 'background-color: #c8e6c9; color: #1b5e20; font-weight: bold; border-bottom: 1px solid #a5d6a7;' 
    else:
        # Cinza Neutro
        return 'color: #90a4ae;'

# 3. HELPER: Validação Lógica (Sincronizada com pontuacao.py)
def verificar_match(chave, valor, gabarito):
    """
    Verifica se o valor atende ao requisito do gabarito.
    Sincronizado com a lógica do arquivo pontuacao.py para garantir que a cor verde
    apareça exatamente quando o score é pontuado.
    """
    if chave not in gabarito: return False
    
    item = gabarito[chave]
    alvos = item.get('alvo', [])
    limites = item.get('limites') # Pode ser lista [mu, sigma] ou dict

    # A. Caso Quadrantes (String vs String formatada)
    if chave == 'quadrantes':
        alvos_limpos = [str(a).replace('-', '') for a in alvos]
        return str(valor) in alvos_limpos

    # B. Caso Faixas Estatísticas (Soma, Deltas, Temps)
    # A lógica aqui DEVE ser igual à do pontuacao.py -> classificar_faixa
    if limites and isinstance(limites, (list, tuple)) and len(limites) == 2:
        try:
            mu, sigma = limites
            v_float = float(valor)
            
            # Recria a lógica de classificação do pontuacao.py
            categoria = "Muito Alto"
            if v_float < mu - 1.5*sigma: categoria = "Muito Baixo"
            elif v_float < mu - 0.5*sigma: categoria = "Baixo"
            elif v_float <= mu + 0.5*sigma: categoria = "Média"
            elif v_float <= mu + 1.5*sigma: categoria = "Alto"
            
            # Verifica se a categoria calculada está na lista de alvos (ex: ['Média', 'Alto'])
            if categoria in alvos:
                return True
        except:
            pass

    # C. Caso Comparação Direta (Pares, Primos, Linhas, Colunas, MaxRep)
    if isinstance(alvos, list):
        # Tenta string exata
        if str(valor) in [str(x) for x in alvos]: return True
        
        # Tenta numérico
        try:
            if float(valor) in [float(x) for x in alvos]: return True
        except:
            pass

    return False

# 4. ROTA DO TESTE PREDITIVO (CORRIGIDO)
@app.route('/teste-preditivo')
def teste_preditivo():
    # Só executa o processamento pesado se o formulário for submetido com process=1
    process = request.args.get('process', default=0, type=int)

    if process != 1:
        # Renderiza a página com o formulário; o usuário clicará em "Processar" para executar
        # Valores padrão mostrados no formulário
        defaults = {
            'qtd': 100,
            'z': 2.0,
            's1': 12, 'p1': 20,
            's2': 11, 'p2': 30,
            's3': 10, 'p3': 30,
            's4': 9,  'p4': 20,
            'pressao': 60
        }
        return render_template('teste_preditivo.html', defaults=defaults)

    start_time = time.time()

    # --- Inputs (quando process==1) ---
    qtd_jogos = request.args.get('qtd', default=100, type=int)
    try:
        s1, p1 = int(request.args.get('s1', 12)), int(request.args.get('p1', 20))
        s2, p2 = int(request.args.get('s2', 11)), int(request.args.get('p2', 30))
        s3, p3 = int(request.args.get('s3', 10)), int(request.args.get('p3', 30))
        s4, p4 = int(request.args.get('s4', 9)), int(request.args.get('p4', 20))
        perc_pressao = int(request.args.get('pressao', 60))
    except:
        s1, p1, s2, p2, s3, p3, s4, p4, perc_pressao = 12, 20, 11, 30, 10, 30, 9, 20, 60

    corte_z = request.args.get('z', default=2.0, type=float)

    print(f"--- MOTOR PREDITIVO V5.4 (Fixed Colors) - Execução iniciada pelo usuário ---")

    # --- Dados ---
    df = carregar_todos_resultados(DB_PATH)
    predicao = gerar_perfil_preditivo_completo(df)
    perfil_alvo_raw = extrair_perfil_alvo_completo(predicao, top_n_quadrantes=15)
    ultimo_sorteio = list(predicao['ultimo_sorteio'])

    # Monta Gabarito com Limites
    gabarito = {}
    for k in perfil_alvo_raw:
        gabarito[k] = {'alvo': perfil_alvo_raw[k]}
        if k in predicao and 'limites' in predicao[k]:
            gabarito[k]['limites'] = predicao[k]['limites']

    # Geração
    qtd_candidatos_brutos = 300000
    pool = gerar_universo_filtrado(qtd_candidatos_brutos, ultimo_sorteio)
    
    # Pontuação
    baldes = defaultdict(list)
    mapa39 = predicao['mapa_39']
    mapa21 = predicao['mapa_21']
    scores_audit = []
    
    for jogo in pool:
        score = calcular_pontuacao_binaria(jogo, gabarito, mapa39, mapa21)
        baldes[score].append(jogo)
        scores_audit.append(score)
        
    max_score_found = max(scores_audit) if scores_audit else 0
    
    # Seleção
    finalistas = []
    dezenas_pressao = predicao['ciclo_faltantes'].union(predicao['atrasadas_criticas'])
    uso_global = Counter()

    def selecionar_com_diversificacao(nota_alvo, qtd_meta, lista_existente):
        candidatos = baldes[nota_alvo]
        if not candidatos: return []
        random.shuffle(candidatos)
        selecionados_agora = []
        
        for jogo in candidatos:
            if len(selecionados_agora) >= qtd_meta: break
            if jogo in lista_existente: continue
            
            tem_pressao = bool(set(jogo).intersection(dezenas_pressao))
            if perc_pressao > 0 and not tem_pressao:
                if random.random() < 0.6: continue

            pontos_repeticao = sum([uso_global[d] for d in jogo])
            if pontos_repeticao < 25: 
                selecionados_agora.append(jogo)
                for d in jogo: uso_global[d] += 1
        
        if len(selecionados_agora) < qtd_meta:
            for jogo in candidatos:
                if len(selecionados_agora) >= qtd_meta: break
                if jogo not in lista_existente and jogo not in selecionados_agora:
                    selecionados_agora.append(jogo)
                    for d in jogo: uso_global[d] += 1
        return selecionados_agora

    configs = [(s1, p1), (s2, p2), (s3, p3), (s4, p4)]
    for meta_score, perc in configs:
        falta = qtd_jogos - len(finalistas)
        if falta <= 0: break
        cota = int(qtd_jogos * (perc/100))
        finalistas.extend(selecionar_com_diversificacao(meta_score, cota, finalistas))

    if len(finalistas) < qtd_jogos:
        for sc in range(max_score_found, -1, -1):
            if len(finalistas) >= qtd_jogos: break
            if sc in [s1, s2, s3, s4]: continue
            falta = qtd_jogos - len(finalistas)
            finalistas.extend(selecionar_com_diversificacao(sc, falta, finalistas))

    jogos_finais = finalistas[:qtd_jogos]
    tempo_proc = time.time() - start_time

    # --- HTML VIEW ---
    ciclo_str = ', '.join([f'{d:02d}' for d in sorted(list(predicao['ciclo_faltantes']))]) or "Fechado"
    atrasos_filtrados = [d for d in predicao['lista_atrasos_completa'] if d['z_score'] >= corte_z]
    quadrantes_html = html_tags(perfil_alvo_raw['quadrantes'], classe='tag-quad')
    
    html_form = f"""
    <form action="/teste-preditivo" method="get" style="background:#e8f5e9; padding:15px; border-radius:8px; margin-bottom:20px; border: 1px solid #c8e6c9; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <div style="display:flex; gap:15px; flex-wrap:wrap; align-items:center;">
            <div style="text-align:center;">
                <label style="font-weight:bold; font-size:0.8em; color:#1b5e20;">Qtd</label><br>
                <input type="number" name="qtd" value="{qtd_jogos}" style="width:60px; padding:5px; text-align:center; border:1px solid #ccc; border-radius:4px;">
            </div>
            <div style="background:white; padding:5px 10px; border-radius:5px; border:1px solid #a5d6a7; text-align:center;">
                <label style="font-size:0.7em; font-weight:bold; color:#555;">Meta 1</label><br>
                Scr:<input type="number" name="s1" value="{s1}" style="width:45px;"> Vol:<input type="number" name="p1" value="{p1}" style="width:45px;">%
            </div>
            <div style="background:white; padding:5px 10px; border-radius:5px; border:1px solid #a5d6a7; text-align:center;">
                <label style="font-size:0.7em; font-weight:bold; color:#555;">Meta 2</label><br>
                Scr:<input type="number" name="s2" value="{s2}" style="width:45px;"> Vol:<input type="number" name="p2" value="{p2}" style="width:45px;">%
            </div>
             <div style="background:white; padding:5px 10px; border-radius:5px; border:1px solid #a5d6a7; text-align:center;">
                <label style="font-size:0.7em; font-weight:bold; color:#555;">Meta 3</label><br>
                Scr:<input type="number" name="s3" value="{s3}" style="width:45px;"> Vol:<input type="number" name="p3" value="{p3}" style="width:45px;">%
            </div>
            <div style="background:white; padding:5px 10px; border-radius:5px; border:1px solid #a5d6a7; text-align:center;">
                <label style="font-size:0.7em; font-weight:bold; color:#555;">Meta 4</label><br>
                Scr:<input type="number" name="s4" value="{s4}" style="width:45px;"> Vol:<input type="number" name="p4" value="{p4}" style="width:45px;">%
            </div>
            <div style="text-align:center;">
                <label style="font-size:0.8em; color:#d32f2f; font-weight:bold;">Pressão</label><br>
                <input type="number" name="pressao" value="{perc_pressao}" style="width:60px; padding:5px; text-align:center; border:1px solid #ccc; border-radius:4px;">
            </div>
            <button type="submit" style="background:#2e7d32; color:white; border:none; padding:0 25px; height:45px; border-radius:4px; cursor:pointer; font-weight:bold; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">PROCESSAR</button>
        </div>
        <div style="margin-top:8px; font-size:0.8em; color:#555;">Max Score: <strong>{max_score_found}</strong> | Tempo: {tempo_proc:.2f}s</div>
    </form>
    """

    html_jogos = """
    <div style="overflow-x: auto; max-height: 700px; border-radius:8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
    <table class="table-jogos">
        <thead>
            <tr>
                <th rowspan="2" style="border-right:1px solid #4caf50;">#</th>
                <th rowspan="2" style="border-right:1px solid #4caf50;">Score</th>
                <th rowspan="2" style="border-right:1px solid #4caf50;">Dezenas</th>
                <th colspan="12" style="background:#388e3c; border-bottom:1px solid #4caf50; border-right:1px solid #4caf50;">Predição Estatística (Score)</th>
                <th colspan="5" style="background:#455a64; border-bottom:1px solid #607d8b;">Filtros Rígidos</th>
            </tr>
            <tr>
                <th title="Soma">Soma</th>
                <th title="Pares">Par</th>
                <th title="Primos">Pri</th>
                <th title="Múltiplos de 3">M3</th>
                <th title="Deltas">Delt</th>
                <th title="Quadrantes">Quad</th>
                <th title="Linhas">Lin</th>
                <th title="Colunas">Col</th>
                <th title="Temp 39">T39</th>
                <th title="Temp 21">T21</th>
                <th title="Max Rep 39">MR39</th>
                <th title="Max Rep 21" style="border-right:1px solid #4caf50;">MR21</th>
                
                <th title="Repetidas do Anterior" style="background:#546e7a;">Rep</th>
                <th title="Sequenciais" style="background:#546e7a;">Seq</th>
                <th title="Iniciais" style="background:#546e7a;">Ini</th>
                <th title="Finais" style="background:#546e7a;">Fin</th>
                <th title="Fibonacci" style="background:#546e7a;">Fib</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for i, jogo in enumerate(jogos_finais):
        score = calcular_pontuacao_binaria(jogo, gabarito, mapa39, mapa21)
        
        soma = sum(jogo)
        pares = len([x for x in jogo if x % 2 == 0])
        primos = len([x for x in jogo if x in LISTA_PRIMOS])
        fibo = len([x for x in jogo if x in LISTA_FIBONACCI])
        mult3 = len([x for x in jogo if x in LISTA_MULTIPLOS_3])
        repetidas = len(set(jogo).intersection(set(ultimo_sorteio)))
        sb = sorted(jogo)
        sequenciais = sum([1 for k in range(len(sb)-1) if sb[k+1] == sb[k]+1])
        deltas = sum([sb[k+1]-sb[k] for k in range(len(sb)-1)])
        max_iniciais = max(Counter([d // 10 for d in jogo]).values() or [0])
        max_finais = max(Counter([d % 10 for d in jogo]).values() or [0])
        linhas = len(set([(d-1)//10 for d in jogo]))
        colunas = len(set([(d-1)%10 for d in jogo]))
        t39 = sum([mapa39.get(d, 0) for d in jogo])
        t21 = sum([mapa21.get(d, 0) for d in jogo])
        mr39 = max([mapa39.get(d, 0) for d in jogo]) if jogo else 0
        mr21 = max([mapa21.get(d, 0) for d in jogo]) if jogo else 0
        
        q1 = q2 = q3 = q4 = 0
        for n in jogo:
            col = (n - 1) % 10
            if n <= 30:
                if col < 5: q1 += 1
                else: q2 += 1
            else:
                if col < 5: q3 += 1
                else: q4 += 1
        quad_str = f"{q1}{q2}{q3}{q4}"
        
        st_soma = estilo_celula(verificar_match('soma', soma, gabarito))
        st_par = estilo_celula(verificar_match('pares', pares, gabarito))
        st_pri = estilo_celula(verificar_match('primos', primos, gabarito))
        st_m3 = estilo_celula(verificar_match('mult3', mult3, gabarito))
        st_delt = estilo_celula(verificar_match('deltas', deltas, gabarito))
        st_quad = estilo_celula(verificar_match('quadrantes', quad_str, gabarito))
        st_lin = estilo_celula(verificar_match('linhas', linhas, gabarito))
        st_col = estilo_celula(verificar_match('colunas', colunas, gabarito))
        st_t39 = estilo_celula(verificar_match('temp39', t39, gabarito))
        st_t21 = estilo_celula(verificar_match('temp21', t21, gabarito))
        st_mr39 = estilo_celula(verificar_match('max_rep_39', mr39, gabarito))
        st_mr21 = estilo_celula(verificar_match('max_rep_21', mr21, gabarito))
        st_neutro = "color: #78909c;"

        jogo_fmt = ' '.join([f'<span class="num-bola">{n:02d}</span>' for n in jogo])
        
        if score >= s1: badge_bg = "#2e7d32"
        elif score >= s2: badge_bg = "#43a047"
        elif score >= s3: badge_bg = "#fbc02d"
        else: badge_bg = "#ef6c00"
        
        html_jogos += f"""
        <tr>
            <td>{i+1}</td>
            <td><span class="score-badge" style="background:{badge_bg}">{score}</span></td>
            <td style="text-align:left; padding-left:8px;">{jogo_fmt}</td>
            <td style="{st_soma}">{soma}</td>
            <td style="{st_par}">{pares}</td>
            <td style="{st_pri}">{primos}</td>
            <td style="{st_m3}">{mult3}</td>
            <td style="{st_delt}">{deltas}</td>
            <td style="{st_quad}"><span class="tag-quad">{quad_str}</span></td>
            <td style="{st_lin}">{linhas}</td>
            <td style="{st_col}">{colunas}</td>
            <td style="{st_t39}">{t39}</td>
            <td style="{st_t21}">{t21}</td>
            <td style="{st_mr39}">{mr39}</td>
            <td style="{st_mr21}">{mr21}</td>
            <td style="{st_neutro}">{repetidas}</td>
            <td style="{st_neutro}">{sequenciais}</td>
            <td style="{st_neutro}">{max_iniciais}</td>
            <td style="{st_neutro}">{max_finais}</td>
            <td style="{st_neutro}">{fibo}</td>
        </tr>
        """
    html_jogos += "</tbody></table></div>"

    def gerar_html_mapa(jogos, ciclo, atrasadas):
        todas = [n for j in jogos for n in j]
        c = Counter(todas)
        h = '<div class="mapa-calor-container">'
        for d in range(1, 61):
            qtd = c.get(d, 0)
            mx = max(c.values()) if c else 1
            inte = min(qtd/mx, 1.0) if mx > 0 else 0
            bg = f"rgba(46, 125, 50, {0.1 + inte*0.9})" if inte > 0 else "#fff"
            color = "white" if inte > 0.6 else "#333"
            border = "3px solid #c62828" if d in ciclo else "3px solid #f9a825" if d in atrasadas else "1px solid #eee"
            h += f'<div class="bola-mapa" style="background:{bg}; color:{color}; border:{border};"><b style="font-size:1.8em;">{d:02d}</b><span style="font-size:1.2em">{qtd}</span></div>'
        return h + '</div>'
    
    # DEFINIÇÃO DO MENU PREDITIVO
    html_menu = """
        <style>
            body { margin:0; padding:0; box-sizing: border-box; } 
            .main-nav { background: linear-gradient(to right, #1b5e20, #2e7d32); box-shadow: 0 2px 10px rgba(0,0,0,0.15); margin-bottom: 25px; font-family: 'Segoe UI', sans-serif; }
            .nav-content { max-width: 1400px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; height: 60px; padding: 0 20px; }
            .nav-brand { color: white; font-weight: 800; font-size: 1.3em; text-decoration: none; }
            .nav-links { display: flex; gap: 10px; }
            .nav-btn { color: rgba(255,255,255,0.9); text-decoration: none; font-weight: 500; padding: 8px 16px; border-radius: 6px; transition: all 0.2s; }
            .nav-btn:hover { background: rgba(255,255,255,0.15); color: white; }
        </style>
        <nav class="main-nav">
            <div class="nav-content">
                <a href="/" class="nav-brand">🎱 MegaSmart AI</a>
                <div class="nav-links">
                    <a href="/" class="nav-btn">📊 Painel Indicadores</a>
                    <a href="/teste-preditivo" class="nav-btn" style="background:white; color:#1b5e20; font-weight:bold;">🎯 Radar Preditivo</a>
                    <a href="/analise-similaridade" class="nav-btn">🧬 Similaridade Genética</a>
                    <a href="/backtest" class="nav-btn">🧪 Backtest</a>
                </div>
            </div>
        </nav>
        """

    # MONTAGEM FINAL (Corrigido: Adiciona menu no início e ajusta CSS)
    full_html = f"""
    {html_menu}
    <style>
        body {{ font-family: 'Segoe UI', Roboto, Helvetica, sans-serif; background: #f0f2f5; color: #333; }}
        .container {{ max-width: 1600px; margin: auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 15px rgba(0,0,0,0.08); }}
        h1 {{ color: #2e7d32; margin-bottom: 15px; font-weight:800; letter-spacing: -0.5px; }}
        
        .mapa-calor-container {{ display: grid; grid-template-columns: repeat(10, 1fr); gap: 4px; padding: 10px; background: #fff; border: 1px solid #eee; border-radius: 8px; }}
        .bola-mapa {{ aspect-ratio: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; border-radius: 50%; font-size: 0.85em; transition: transform 0.1s; }}
        .bola-mapa:hover {{ transform: scale(1.1); z-index:2; box-shadow: 0 2px 5px rgba(0,0,0,0.15); }}
        
        .table-perfil {{ width: 100%; border-collapse: collapse; font-size: 0.85em; }}
        .table-perfil td {{ padding: 6px 8px; border-bottom: 1px solid #f1f1f1; }}
        
        .table-jogos {{ width: 100%; border-collapse: collapse; font-size: 0.75em; white-space: nowrap; }}
        .table-jogos th {{ 
            background-color: #2e7d32; 
            color: white; 
            padding: 8px 4px; 
            text-align: center; 
            position: sticky; 
            top: 0; 
            z-index:10; 
            border: 1px solid #43a047;
            box-shadow: 0 2px 2px rgba(0,0,0,0.1);
        }}
        .table-jogos td {{ border: 1px solid #e0e0e0; padding: 6px 2px; text-align: center; }}
        .table-jogos tr:nth-child(even) {{ background-color: #f9fbe7; }}
        .table-jogos tr:hover {{ background-color: #e8f5e9; }}
        
        .score-badge {{ color: white; padding: 3px 8px; border-radius: 12px; font-weight: bold; font-size: 1.1em; box-shadow: 1px 1px 2px rgba(0,0,0,0.2); }}
        .num-bola {{ display: inline-block; font-weight:bold; color:#263238; width: 20px; font-size:1.1em; }}
        
        .tag {{ display: inline-block; background: #e8f5e9; color: #2e7d32; padding: 1px 5px; border-radius: 4px; font-size: 0.9em; border: 1px solid #c8e6c9; margin-right:2px; }}
        .tag-quad {{ font-family: 'Consolas', monospace; font-size: 1.1em; color: #1565c0; font-weight:bold; background:#e3f2fd; padding:2px 4px; border-radius:4px; border:1px solid #90caf9; margin:2px; display:inline-block; }}
        .tag-fixa {{ background: #fff3e0; color: #e65100; border: 1px solid #ffe0b2; padding: 1px 6px; border-radius: 4px; font-weight: bold; font-size:0.9em; }}
        
        .layout-grid {{ display: grid; grid-template-columns: 360px 1fr; gap: 25px; margin-top: 15px; }}
    </style>
           
    <div class="container">
        <h1>🎯 Radar Preditivo V5.4 <span style="font-weight:normal; font-size:0.5em; color:#777;"></span></h1>
        {html_form}
        
        <div class="layout-grid">
            <div style="border-right: 1px solid #eee; padding-right: 20px;">
                <h3 style="color:#37474f; border-bottom:2px solid #2e7d32; padding-bottom:5px;">📋 Estrutura Alvo</h3>
                <div style="padding-right:5px;">
                    <h4 style="margin:10px 0 5px 0; color:#455a64; font-size:0.9em; background:#eceff1; padding:8px; border-radius:4px;">Filtros Rígidos (Constraints)</h4>
                    <table class="table-perfil">
                        <tr><td>Repetidas Ant.</td><td><span class="tag-fixa">0 ou 1</span></td></tr>
                        <tr><td>Sequenciais</td><td><span class="tag-fixa">Máx 1 par</span></td></tr>
                        <tr><td>Conc. Iniciais</td><td><span class="tag-fixa">Máx 3</span></td></tr>
                        <tr><td>Conc. Finais</td><td><span class="tag-fixa">Máx 3</span></td></tr>
                        <tr><td>Fibonacci</td><td><span class="tag-fixa">Máx 2</span></td></tr>
                    </table>
                    
                    <h4 style="margin:15px 0 5px 0; color:#2e7d32; font-size:0.9em; background:#e8f5e9; padding:8px; border-radius:4px;">Predição Estatística (Score)</h4>
                    <table class="table-perfil">
                        <tr><td>Soma</td><td>{html_tags(perfil_alvo_raw['soma'])}</td></tr>
                        <tr><td>Pares</td><td>{html_tags(perfil_alvo_raw['pares'], sufixo='P')}</td></tr>
                        <tr><td>Primos</td><td>{html_tags(perfil_alvo_raw['primos'])}</td></tr>
                        <tr><td>Mult. 3</td><td>{html_tags(perfil_alvo_raw['mult3'])}</td></tr>
                        <tr><td>Deltas</td><td>{html_tags(perfil_alvo_raw['deltas'])}</td></tr>
                        <tr><td>Quadrantes</td><td>{quadrantes_html}</td></tr>
                        <tr><td>Linhas</td><td>{html_tags(perfil_alvo_raw['linhas'])}</td></tr>
                        <tr><td>Colunas</td><td>{html_tags(perfil_alvo_raw['colunas'])}</td></tr>
                        <tr><td>Max Rep 39</td><td>{html_tags(perfil_alvo_raw['max_rep_39'])}</td></tr>
                        <tr><td>Max Rep 21</td><td>{html_tags(perfil_alvo_raw['max_rep_21'])}</td></tr>
                        <tr><td>Temp 39</td><td>{html_tags(perfil_alvo_raw['temp39'])}</td></tr>
                        <tr><td>Temp 21</td><td>{html_tags(perfil_alvo_raw['temp21'])}</td></tr>
                    </table>

                    <div style="margin-top:15px; border:1px solid #ef9a9a; background:#ffebee; padding:10px; border-radius:6px;">
                        <strong style="color:#c62828;">Pressão de Ciclo:</strong><br>{ciclo_str}
                    </div>
                    <div style="margin-top:10px; border:1px solid #ffe0b2; background:#fff8e1; padding:10px; border-radius:6px;">
                        <strong style="color:#f57f17;">Atraso Crítico (Z > {corte_z}):</strong><br>
                        {gerar_html_atrasos(atrasos_filtrados)}
                    </div>
                </div>
            </div>
            
            <div>
                <h3 style="color:#37474f; border-bottom:2px solid #2e7d32; padding-bottom:5px;">Distribuição das Dezenas</h3>
                {gerar_html_mapa(jogos_finais, predicao['ciclo_faltantes'], predicao['atrasadas_criticas'])}
                
                <h3 style="color:#37474f; border-bottom:2px solid #2e7d32; margin-top:25px; padding-bottom:5px;">Apostas Otimizadas</h3>
                {html_jogos}
            </div>
        </div>
    </div>
    """
    return full_html

def gerar_html_atrasos(lista_atrasos):
    if not lista_atrasos: return "Nenhuma dezena crítica."
    html = ""
    for item in lista_atrasos:
        html += f"<span class='tag tag-red' title='Média: {item['media']}'> {item['dezena']:02d} (Z={item['z_score']})</span>"
    return html

# Rota /backtest removida (funcionalidade descontinuada).
# Se precisar reativar, recupere o código de backtest em `app/util/archive/backtest.py` e reimplemente a rota aqui.

@app.route('/analise-similaridade')
def analise_similaridade():
    df = carregar_todos_resultados(DB_PATH)
    
    # ID base opcional (se não passar, pega o último)
    id_req = request.args.get('id', type=int)
    if id_req:
        try:
            idx_alvo = df[df['Concurso'] == id_req].index[0]
        except:
            return "Concurso não encontrado."
    else:
        idx_alvo = len(df) - 1
        
    similares, perfil_alvo = buscar_concursos_similares(df, idx_alvo, top_n=30)
    
    # Adiciona o resultado futuro para exibição na tabela
    for item in similares:
        idx_fut = item['indice_df'] + 1
        if idx_fut < len(df):
            row = df.iloc[idx_fut]
            cols = [f'Bola{i}' for i in range(1, 7)]
            item['concurso_futuro'] = int(row['Concurso'])
            item['res_futuro'] = row[cols].dropna().astype(int).tolist()
        else:
            item['concurso_futuro'] = "N/A"
            item['res_futuro'] = []

    return render_template('similaridade.html', alvo=perfil_alvo, similares=similares)

@app.route('/simular-cenario')
def simular_cenario_route():
    # Coleta parametros do request
    params = {
        'qtd': request.args.get('qtd', 100, type=int),
        's1': request.args.get('s1', 12, type=int), 'p1': request.args.get('p1', 20, type=int),
        's2': request.args.get('s2', 11, type=int), 'p2': request.args.get('p2', 30, type=int),
        's3': request.args.get('s3', 10, type=int), 'p3': request.args.get('p3', 30, type=int),
        's4': request.args.get('s4', 9, type=int),  'p4': request.args.get('p4', 20, type=int),
        'pressao': request.args.get('pressao', 60, type=int)
    }
    cid = request.args.get('cid', type=int)
    
    if not cid: return "ID do concurso obrigatório"
    
    df = carregar_todos_resultados(DB_PATH)
    res = simular_cenario_passado(df, cid, params)
    
    return render_template('resultado_simulacao.html', res=res)

if __name__ == '__main__':
    app.run(debug=True)