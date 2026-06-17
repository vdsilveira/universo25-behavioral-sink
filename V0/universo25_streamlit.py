import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import time
import requests
import json
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

from universo25_model import (
    Universe25Model, MouseAgent,
    GRID_WIDTH, GRID_HEIGHT, STEPS,
    plot_grid, plot_metrics,
    STRESS_GAIN_RATE, STRESS_RECOVERY_RATE,
    STRESS_SPREAD_RATE, ALPHA_THRESHOLD,
    BEAUTIFUL_EMERGENCE_THRESHOLD, HYPERSEXUALITY_THRESHOLD,
    BASE_FERTILITY_RATE, PREGNANCY_DURATION,
    LITTER_SIZE_MIN, LITTER_SIZE_MAX, WEANING_PERIOD,
    MAX_AGE, REPRODUCTIVE_AGE_START, REPRODUCTIVE_AGE_END,
    ENVIRONMENTAL_ENRICHMENT,
    CANNIBALISM_PROBABILITY, RESOURCE_AVAILABILITY,
    STATION_MAX_OCCUPANCY, FEEDING_STATIONS_COUNT,
    COLONY_STRESS_DIVISOR,
    RESORPTION_PROBABILITY, MATERNAL_AGGRESSION_THRESHOLD,
    SOCIAL_DAMAGE_BEAUTIFUL_THRESHOLD,
)

st.set_page_config(
    page_title="Universo 25 — Simulação",
    page_icon="🐭",
    layout="wide",
)

st.title("🐭 Universo 25 — Simulação do Paraíso dos Ratos")
st.markdown(
    "Recriação computacional do experimento de John B. Calhoun (1968) "
    "com Modelagem Baseada em Agentes (ABM). Ajuste os parâmetros e "
    "observe as quatro fases do colapso social."
)

with st.sidebar:
    st.header("Parâmetros da Simulação")

    n_steps = st.slider("Passos a simular", 100, 2000, 1588, 50,
                        help="Quantidade de turnos (dias) da simulação")

    st.subheader("Ambiente")
    grid_w = st.slider("Largura do grid", 30, 80, GRID_WIDTH, 5,
                        help="Número de células na horizontal. 50² = 2500 células, 80² = 6400.")
    grid_h = st.slider("Altura do grid", 30, 80, GRID_HEIGHT, 5,
                        help="Número de células na vertical.")

    st.subheader("Biológicos")
    fertility = st.slider("Taxa de fertilidade",
                          0.05, 0.50, BASE_FERTILITY_RATE, 0.05,
                          help="Probabilidade base de um par acasalar a cada passo. "
                               "0.05 = valor calibrado v29.")
    litter_max = st.slider("Tamanho máximo da ninhada",
                           3, 12, LITTER_SIZE_MAX, 1,
                           help="Máximo de filhotes por parto. Varia aleatoriamente entre 3 e este valor.")
    max_age = st.slider("Idade máxima (turnos)",
                        200, 1000, MAX_AGE, 50,
                        help="Turnos de vida máxima. Agentes morrem ao atingir esta idade.")

    st.subheader("Estresse")
    stress_gain = st.slider("Ganho de estresse",
                            0.01, 0.15, STRESS_GAIN_RATE, 0.01,
                            format="%.2f",
                            help="Stress ganho por passo em alta densidade. "
                                 "Quanto maior, mais rápido o colapso social.")
    stress_recovery = st.slider("Recuperação de estresse",
                                0.001, 0.05, STRESS_RECOVERY_RATE, 0.001,
                                format="%.3f",
                                help="Stress perdido por passo em baixa densidade.")
    alpha_th = st.slider("Limiar ALPHA → BETA",
                         0.2, 0.9, ALPHA_THRESHOLD, 0.05,
                         help="Stress máximo que um macho ALPHA tolera antes de virar BETA.")
    beautiful_th = st.slider("Limiar BEAUTIFUL",
                             0.3, 0.9, BEAUTIFUL_EMERGENCE_THRESHOLD, 0.05,
                             help="Colony stress mínimo para surgirem os Lindos (BEAUTIFUL).")
    col_div = st.slider("Divisor estresse colônia",
                        100, 10000, COLONY_STRESS_DIVISOR, 50,
                        help="População que equivale a 50% do estresse da colônia. "
                             "Aumente para grids maiores.")

    st.subheader("Canibalismo & Comida")
    cannibal = st.slider("Prob. de canibalismo",
                         0.0, 0.25, CANNIBALISM_PROBABILITY, 0.01,
                         format="%.2f",
                         help="Chance base de um agente consumir um cadáver. "
                              "Escalada com colony_stress.")
    resource_avail = st.slider("Disponibilidade de recursos",
                               0.1, 2.0, RESOURCE_AVAILABILITY, 0.1,
                               format="%.1f",
                               help="Multiplicador de comida/água. 1.0 = abundância.")
    station_max = st.slider("Ocupação máxima por estação",
                            1, 10, STATION_MAX_OCCUPANCY, 1,
                            help="Máximo de agentes por estação de comida.")
    n_stations = st.slider("Número de estações de comida",
                           1, 12, FEEDING_STATIONS_COUNT, 1,
                           help="Total de pontos de alimentação no grid.")

    st.subheader("Gestação & Maternidade")
    resorption_p = st.slider("Prob. reabsorção fetal",
                             0.0, 0.8, RESORPTION_PROBABILITY, 0.05,
                             help="Chance de gestação ser reabsorvida sob estresse")
    mat_aggr_th = st.slider("Limiar agressão maternal",
                            0.2, 0.9, MATERNAL_AGGRESSION_THRESHOLD, 0.05,
                            help="Estresse acima do qual mães podem atacar os próprios filhotes")

    st.subheader("Cenário Alternativo")
    enrichment = st.checkbox("Enriquecimento ambiental",
                             value=ENVIRONMENTAL_ENRICHMENT,
                             help="Reduz estresse com estímulos mentais")

    st.subheader("Visualização")
    anim_speed = st.slider("Velocidade da animação (ms)",
                           10, 500, 10, 10,
                           help="Delay entre quadros. 10ms = mais rápido, 500ms = mais lento.")

    run_btn = st.button("▶ Rodar Simulação", type="primary", use_container_width=True)

    if run_btn:
        from universo25_model import (
            GRID_WIDTH as _, GRID_HEIGHT as _,
            STEPS as __,
        )

if 'model' not in st.session_state:
    st.session_state.model = None
    st.session_state.data = None
    st.session_state.step = 0


CALHOUN_CHECKPOINTS = [0, 104, 315, 560, 600, 736, 1471, 1588]
CALHOUN_TARGETS  = [8, 50, 620, 2200, 2100, 2056, 100, 0]


def evaluate_with_llm(pop_history, stress_history, col_history,
                       beautiful_history, params_used, n_steps):
    api_key = os.getenv('OLLAMA_API_KEY', '')
    base_url = os.getenv('OLLAMA_BASE_URL', 'https://api.ollama.com')
    model_name = os.getenv('OLLAMA_MODEL', 'ministral-3:3b')

    if not api_key:
        return None, "API key da Ollama não configurada no .env"

    sim_at_checkpoints = []
    for d in CALHOUN_CHECKPOINTS:
        idx = min(d, len(pop_history) - 1)
        sim_at_checkpoints.append(int(pop_history[idx]))

    pop_peak = max(pop_history)
    pop_final = pop_history[-1]
    stress_peak = max(stress_history)
    beautiful_peak = max(beautiful_history)
    beautiful_final = beautiful_history[-1]

    prompt = f"""Você é um cientista avaliando uma simulação do experimento Universo 25 de John B. Calhoun.

## Dados da simulação

Parâmetros utilizados: {json.dumps(params_used, indent=2)}

População nos checkpoints de Calhoun (dias 0, 104, 315, 560, 600, 736, 1471, 1588):
{sim_at_checkpoints}

Curva alvo de Calhoun:
{CALHOUN_TARGETS}

Pico populacional: {pop_peak}
População final: {pop_final}
Pico de estresse médio: {stress_peak:.3f}
Pico de agentes BEAUTIFUL: {beautiful_peak}
Agentes BEAUTIFUL no final: {beautiful_final}

## Tarefa

Analise os resultados da simulação comparando com a curva alvo do experimento real de Calhoun.
Responda em português, em no máximo 3 parágrafos:

1. A simulação se aproxima do comportamento observado por Calhoun? (considere crescimento, pico, colapso e surgimento dos BEAUTIFUL)
2. Quais fatores mais contribuíram para as diferenças (se houverem)?
3. O que isso sugere sobre a validade do modelo?
"""

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': model_name,
        'prompt': prompt,
        'stream': False,
        'options': {'temperature': 0.3, 'num_predict': 600},
    }

    try:
        resp = requests.post(
            f'{base_url.rstrip("/")}/api/generate',
            headers=headers,
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        result = resp.json()
        text = result.get('response', '').strip()
        return text, None
    except Exception as e:
        return None, f"Erro ao chamar Ollama: {e}"


def run_simulation(n_steps, grid_w, grid_h, fertility, litter_max,
                   max_age, stress_gain, stress_recovery,
                   alpha_th, beautiful_th, col_div, enrichment, anim_speed,
                   cannibal, resource_avail, station_max, n_stations,
                   resorption_p, mat_aggr_th):
    params = {
        'GRID_WIDTH': grid_w,
        'GRID_HEIGHT': grid_h,
        'BASE_FERTILITY_RATE': fertility,
        'LITTER_SIZE_MAX': litter_max,
        'MAX_AGE': max_age,
        'STRESS_GAIN_RATE': stress_gain,
        'STRESS_RECOVERY_RATE': stress_recovery,
        'ALPHA_THRESHOLD': alpha_th,
        'BEAUTIFUL_EMERGENCE_THRESHOLD': beautiful_th,
        'COLONY_STRESS_DIVISOR': col_div,
        'ENVIRONMENTAL_ENRICHMENT': enrichment,
        'CANNIBALISM_PROBABILITY': cannibal,
        'RESOURCE_AVAILABILITY': resource_avail,
        'STATION_MAX_OCCUPANCY': station_max,
        'FEEDING_STATIONS_COUNT': n_stations,
        'RESORPTION_PROBABILITY': resorption_p,
        'MATERNAL_AGGRESSION_THRESHOLD': mat_aggr_th,
    }

    import universo25_model as m
    for k, v in params.items():
        setattr(m, k, v)

    model = Universe25Model(rng=42, environmental_enrichment=enrichment)

    chart_placeholder = st.empty()
    status_placeholder = st.empty()

    pop_history = []
    stress_history = []
    col_history = []
    beautiful_history = []

    for step in range(n_steps):
        model.step()
        data = model.datacollector.get_model_vars_dataframe()
        pop = data['Population'].iloc[-1]
        stress = data['Mean Stress'].iloc[-1]
        col_stress = data['Colony Stress'].iloc[-1]
        beautiful = data['BEAUTIFUL Count'].iloc[-1]

        pop_history.append(pop)
        stress_history.append(stress)
        col_history.append(col_stress)
        beautiful_history.append(beautiful)

        if step % max(1, n_steps // 50) == 0 or step == n_steps - 1:
            fig, axes = plt.subplots(1, 3, figsize=(18, 5))

            plot_grid(model, ax=axes[0])
            axes[0].set_title(f'Passo {step + 1} — Pop: {pop:.0f}')

            ax = axes[1]
            ax.plot(pop_history, color='#1E3A5F', linewidth=1.5)
            ax.axhline(y=2200, color='red', linestyle='--', alpha=0.4,
                       label='Alvo Calhoun (2200)')
            ax.set_xlabel('Passo')
            ax.set_ylabel('População')
            ax.set_title('População')
            ax.grid(True, alpha=0.2)
            if step > 10:
                ax.set_xlim(0, n_steps)

            ax = axes[2]
            ax.plot(stress_history, color='#8B4513', linewidth=1.5,
                    label='Estresse médio')
            ax.plot(col_history, color='#FF6347', linewidth=1.5,
                    linestyle='--', label='Estresse colônia')
            ax.axhline(y=beautiful_th, color='red', linestyle=':',
                       alpha=0.5, label=f'Limiar BEAUTIFUL')
            ax.set_xlabel('Passo')
            ax.set_ylabel('Estresse')
            ax.set_title('Estresse')
            ax.legend(fontsize=7)
            ax.grid(True, alpha=0.2)
            if step > 10:
                ax.set_xlim(0, n_steps)

            plt.tight_layout()
            chart_placeholder.pyplot(fig)
            plt.close(fig)

            status_placeholder.markdown(
                f"**Passo:** {step + 1}/{n_steps} | "
                f"**Pop:** {pop:.0f} | "
                f"**Estresse:** {stress:.2f} | "
                f"**BEAUTIFUL:** {beautiful:.0f}"
            )

            time.sleep(anim_speed / 1000.0)

    # Final metrics
    st.subheader("Resultados Finais")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("População Final", f"{pop:.0f}")
    col2.metric("Pico Populacional", f"{max(pop_history):.0f}")
    col3.metric("Estresse Máximo", f"{max(stress_history):.2f}")
    col4.metric("BEAUTIFUL (final)", f"{beautiful:.0f}")

    # LLM evaluation
    with st.spinner("Analisando resultados com IA..."):
        llm_text, llm_error = evaluate_with_llm(
            pop_history, stress_history, col_history,
            beautiful_history, params, n_steps,
        )

    st.subheader("Avaliação do Modelo")
    if llm_text:
        st.markdown(
            f"<div style='padding:1rem; border-radius:0.5rem; "
            f"background:#1a1a2e; border:1px solid #e94560; "
            f"color:#eee; line-height:1.6;'>"
            f"{llm_text.replace(chr(10), '<br>')}"
            f"</div>",
            unsafe_allow_html=True,
        )
    elif llm_error:
        st.warning(llm_error)

    fig = plot_metrics(model)
    st.pyplot(fig)
    plt.close(fig)

    return model


if run_btn:
    with st.spinner("Simulando..."):
        st.session_state.model = run_simulation(
            n_steps, grid_w, grid_h, fertility, litter_max,
            max_age, stress_gain, stress_recovery,
            alpha_th, beautiful_th, col_div, enrichment, anim_speed,
            cannibal, resource_avail, station_max, n_stations,
            resorption_p, mat_aggr_th,
        )
    st.success("Simulação concluída!")
else:
    st.info("Ajuste os parâmetros na barra lateral e clique em **▶ Rodar Simulação**.")

st.markdown("---")
st.markdown(
    '**Referência:** Calhoun, J. B. (1973). '
    '*Death squared: The explosive growth and demise of a mouse population*. '
    'Proceedings of the Royal Society of Medicine, 66(1), 80–88. '
    '[Link](https://journals.sagepub.com/doi/epdf/10.1177/00359157730661P202)'
)
