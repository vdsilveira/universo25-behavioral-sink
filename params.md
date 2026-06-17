# Blueprint de Modelagem: Simulação do Universo 25

Esta documentação define a arquitetura de parâmetros para uma Modelagem Baseada em Agentes (ABM) para replicar o experimento do "Ralo Comportamental" de John B. Calhoun.

## 1. Parâmetros Globais do Ambiente (Environment)

Estes parâmetros definem as propriedades físicas e estruturais do habitat (universo artificial). Os recursos são infinitos, simulando a utopia material.

| Variável | Tipo | Descrição | Valor Sugerido Inicial |
|---|---|---|---|
| `GRID_WIDTH` | Inteiro | Largura da matriz/grid bidimensional | 30 |
| `GRID_HEIGHT` | Inteiro | Altura da matriz/grid bidimensional | 30 |
| `TOROIDAL` | Booleano | Se verdadeiro, o espaço não tem bordas (conecta topo-fundo, esquerda-direita). Se falso, tem paredes | False (paredes limitam fuga) |
| `INITIAL_POPULATION` | Inteiro | Número de agentes iniciais introduzidos no Dia 0 | 8 (4 machos, 4 fêmeas) |
| `MAX_SUPPORT_CAPACITY` | Inteiro | Capacidade física máxima teórica de abrigo | 3800 |
| `RESOURCE_AVAILABILITY` | Float | Multiplicador de comida/água. 1.0 significa abundância contínua (sem fome) | 1.0 |
| `NEST_COUNT` | Inteiro | Número de quadrantes designados como "ninhos/abrigos" | 15 |
| `STRESSED_DENSITY_THRESHOLD` | Inteiro | Número crítico de agentes no mesmo quadrante que dispara o ganho de estresse | 10 |
| `FEEDING_STATIONS_COUNT` | Inteiro | Número de pontos de comida/água no mapa | 3 |
| `STATION_MAX_OCCUPANCY` | Inteiro | Quantos agentes podem comer no mesmo spot ao mesmo tempo | 3 |
| `TERRITORY_SIZE` | Inteiro | Raio de células ao redor de um ninho que um macho ALPHA tenta proteger | 2 |
| `DOMINANCE_THRESHOLD` | Float | Valor de força/status necessário para um macho expulsar outro de um território | 0.6 |

## 2. Atributos Individuais dos Agentes (Agent Attributes)

Cada agente (camundongo) possui variáveis de estado internas que guiam suas decisões a cada iteração (step).

| Atributo | Tipo | Descrição | Domínio de Valores |
|---|---|---|---|
| `id` | Inteiro | Identificador único do agente | 1, 2, 3... |
| `sex` | String / Enum | Gênero biológico do agente | M ou F |
| `age` | Inteiro | Idade do agente medida em ciclos/turnos | 0 a `MAX_AGE` |
| `stress` | Float | Nível de trauma social acumulado pelo agente | 0.0 (tranquilo) a 1.0 (colapso) |
| `social_status` | String / Enum | Papel ou comportamento social assumido pelo agente | `ALPHA`, `BETA`, `MATERNAL`, `BEAUTIFUL` |
| `is_pregnant` | Booleano | Indica se a fêmea está carregando filhotes | True ou False |
| `gestation_timer` | Inteiro | Contador de turnos restantes para o parto | 0 a `PREGNANCY_DURATION` |
| `aggression_trait` | Float | Tendência inata do agente para iniciar brigas | 0.0 (pacífico) a 1.0 (altamente agressivo) |
| `sociability_trait` | Float | Tolerância do agente a estar perto de outros antes de acumular estresse | 0.0 (antissocial) a 1.0 (sociável) |
| `social_learning_factor` | Float | O quão rápido o agente copia o comportamento dos pais (ex: mães estressadas geram filhotes com alto estresse basal) | 0.0 a 1.0 |

## 3. Parâmetros Biológicos de Controle (Biological Constants)

Constantes que regulam a dinâmica natural de vida, morte e reprodução da espécie na ausência de estresse.

| Variável | Tipo | Descrição | Valor Sugerido Inicial |
|---|---|---|---|
| `MAX_AGE` | Inteiro | Tempo máximo de vida de um agente (em turnos) | 600 |
| `REPRODUCTIVE_AGE_START` | Inteiro | Idade em que o agente se torna sexualmente maduro | 30 turnos |
| `REPRODUCTIVE_AGE_END` | Inteiro | Idade em que o agente entra em menopausa/andropausa | 450 turnos |
| `BASE_FERTILITY_RATE` | Float | Probabilidade base de uma fêmea engravidar ao interagir com um macho | 0.25 |
| `PREGNANCY_DURATION` | Inteiro | Quantidade de turnos que dura uma gestação | 18 turnos |
| `LITTER_SIZE` | Inteiro | Quantidade de novos agentes gerados por parto bem-sucedido | 4 a 8 (aleatório) |
| `WEANING_PERIOD` | Inteiro | Tempo que o filhote precisa de cuidados antes de virar agente autônomo | 18 turnos |

## 4. Parâmetros de Comportamento e Patologia Social

Estes parâmetros controlam como as interações sociais degradam o comportamento dos agentes conforme a densidade populacional cresce.

### A. Dinâmica de Estresse e Ralo Comportamental

```python
# Fórmula conceitual para atualização do estresse por turno:
if agentes_no_mesmo_quadrante > STRESSED_DENSITY_THRESHOLD:
    stress += STRESS_GAIN_RATE
else:
    stress -= STRESS_RECOVERY_RATE
```

- **`STRESS_GAIN_RATE`** (Float): O quanto o estresse aumenta por turno em áreas superlotadas. Sugerido: `0.03`
- **`STRESS_RECOVERY_RATE`** (Float): O quão rápido o estresse diminui se o agente ficar isolado. Sugerido: `0.008`

### B. Transição de Status Social

- **`ALPHA_THRESHOLD`** (Float): Nível máximo de estresse que um macho tolera antes de perder a capacidade de defender território. Se `stress > 0.55`, o macho passa de `ALPHA` para `BETA`.
- **`BEAUTIFUL_EMERGENCE_THRESHOLD`** (Float): Nível de estresse global da colônia no momento do nascimento do agente. Quando `colony_stress` ultrapassa este limiar, a probabilidade de um recém-nascido se tornar um "Lindo" (`BEAUTIFUL`) é de 90% (ou 30% com enriquecimento ambiental). Sugerido: `0.55`.

### C. Regras de Decisão Baseadas em Variáveis

| Comportamento | Regra / Equação de Probabilidade | Consequência no Modelo |
|---|---|---|
| Acasalamento | $P(\text{acasalamento}) = \text{BASE\_FERTILITY\_RATE} \times (1 - \text{stress})$ | Reduz a natalidade a zero quando o estresse atinge o ápice |
| Agressão (Brigas) | $P(\text{ataque}) = \text{stress}^2$ (se for `BETA` ou `ALPHA`) | Gera violência gratuita e aleatória no grid. Aumenta o estresse dos vizinhos |
| Abandono Materno | $P(\text{abandono}) = \text{stress}_{\text{mãe}}$ | Se a mãe abandonar o ninho durante o `WEANING_PERIOD`, os filhotes morrem instantaneamente |
| Isolamento ("Os Lindos") | Se `social_status == BEAUTIFUL`: $P(\text{ataque}) = 0$, $P(\text{acasalamento}) = 0$ | O agente ignora todos os outros no grid. Só executa movimentos aleatórios e consome recursos |

### D. Hipersexualidade e Pansexualidade

Conforme o estresse social aumenta, os rituais normais de acasalamento que dependem de cortejo desaparecem. Os agentes passam a tentar cruzar com qualquer parceiro mais próximo, independente de sexo ou maturidade.

- **`HYPERSEXUALITY_THRESHOLD`** (Float): Se o stress individual for superior a `0.60`, o agente ignora a verificação de sexo e status social ao tentar a função de acasalamento.

### E. Canibalismo e Necrofagia

- **`CANNIBALISM_PROBABILITY`** (Float): Probabilidade de um agente atacar e consumir um filhote abandonado ou outro agente morto caso esteja no mesmo quadrante, engatado pelo estresse social extremo da colônia. Sugerido: `0.05` (incremental com estresse médio da colônia).

## 5. Métricas de Monitoramento (Jupyter Plots)

Para gerar os gráficos no seu notebook e validar se a simulação seguiu o comportamento histórico de Calhoun, você deve rastrear e plotar as seguintes variáveis a cada passo de tempo ($t$):

- **População Total ($N$):** Soma de todos os agentes vivos.
- **Taxa de Natalidade vs. Mortalidade Infantil:** Número de nascimentos vs. número de filhotes que morreram antes do fim do `WEANING_PERIOD`.
- **Distribuição de População por Status:** Gráfico de área empilhada mostrando a transição de `ALPHA`s e Fêmeas Ativas para `BETA`s e `BEAUTIFUL` Ones.
- **Índice de Estresse Médio:** Média aritmética do atributo `stress` de todos os agentes vivos. Deve correlacionar diretamente com a inversão da curva de crescimento populacional.

## 6. Validação — Curva Alvo de Calhoun

Ao rodar o modelo no Jupyter Lab, seu objetivo principal de calibração é replicar as fases reais observadas no experimento original. O comportamento histórico esperado da população ao longo do tempo é:

| Dia (DAC) | Evento | População Aproximada |
|---|---|---|---|
| 0 | Introdução dos 4 casais | 8 |
| 104 | Início da Fase B (primeiras ninhadas) | ~50 |
| 315 | Fim da Fase B — início da estagnação | **620** |
| 560 | **Pico populacional** | **2.200** |
| 600 | Último nascimento vivo | ~2.100 |
| 736 | Declínio lento | **2.056** |
| 1471 | Quase extinto | ~100 |

Fonte: Calhoun (1973), Fig 2. O colapso populacional é **muito mais gradual** do que geralmente se supõe: após o pico de 2.200 em 560 dias, a população ainda era de 2.056 em 736 dias — uma queda de apenas ~7% em 176 dias. O último nascimento ocorreu em 600 dias, a última concepção em 920 dias, e a população só chegou a ~100 em 1471 dias.

Se sua simulação continuar crescendo até bater o teto físico de 3800, significa que os parâmetros de estresse ou de abandono materno estão muito fracos.

## 7. Parâmetro Extra — Cenário Alternativo

Cientistas posteriores criticaram Calhoun dizendo que os animais não enlouqueceram pelo excesso de população, mas sim pelo tédio e falta de desafios (uma vida sem precisar lutar por nada). Você pode adicionar um parâmetro disruptivo no seu código para testar essa hipótese:

- **`ENVIRONMENTAL_ENRICHMENT`** (Booleano): Se ativado (`True`), o ambiente introduz aleatoriamente pequenas tarefas ou obstáculos no grid (ex: barreiras mutáveis, quebra-cabeças para liberar comida). O ganho de estresse global deve ser reduzido, provando que o estímulo mental previne o surgimento d'Os Lindos, mesmo em densidades populacionais elevadas.

## 8. Esquema de Cores para Visualização

Esquema cromático para facilitar a identificação visual dos diferentes tipos de agente e elementos do ambiente nos plots do Jupyter.

### Cores dos Agentes

| Categoria | Condição | Cor | Código Hex |
|---|---|---|---|
| Macho ALPHA | `sex == M` e `social_status == ALPHA` | Azul escuro | `#1E3A5F` |
| Macho BETA | `social_status == BETA` | Azul claro | `#6495ED` |
| Fêmea MATERNAL | `sex == F` e `social_status == MATERNAL` | Rosa | `#FF69B4` |
| Fêmea grávida | `is_pregnant == True` | Rosa escuro | `#FF1493` |
| Filhote | `age < WEANING_PERIOD` | Amarelo ouro | `#FFD700` |
| Lindo (BEAUTIFUL) | `social_status == BEAUTIFUL` | Cinza claro | `#D3D3D3` |
| Morto | agente morto no turno | Marrom | `#8B4513` |

### Cores do Ambiente (Grid)

| Elemento | Cor | Código Hex |
|---|---|---|
| Célula vazia (fundo) | Bege claro | `#FFF5EE` |
| Ninho / abrigo | Verde musgo | `#556B2F` |
| Estação de comida | Laranja | `#FF8C00` |

### Mapa de Calor de Estresse

Para visualizar a distribuição espacial do estresse, use um gradiente verde (0.0) → amarelo (0.5) → vermelho (1.0) com `plt.cm.RdYlGn_r` do matplotlib. Sugere-se plotar lado a lado: scatterplot colorido dos agentes (esquerda) e heatmap de estresse no grid (direita).

### Código conceitual

```python
AGENT_COLORS = {
    ('M', 'ALPHA'):    '#1E3A5F',
    ('M', 'BETA'):     '#6495ED',
    ('F', 'MATERNAL'): '#FF69B4',
    ('F', 'PREGNANT'): '#FF1493',
    'PUPPY':           '#FFD700',
    'BEAUTIFUL':       '#D3D3D3',
    'DEAD':            '#8B4513',
}

GRID_COLORS = {
    'empty':        '#FFF5EE',
    'nest':         '#556B2F',
    'food_station': '#FF8C00',
}

stress_cmap = plt.cm.RdYlGn_r
```

## 9. Parâmetros Adicionais (Implementação V0)

Parâmetros que existem no código mas não constam nas seções anteriores, incluindo os adicionados nas funcionalidades de canibalismo, estações de comida e enriquecimento ambiental.

| Variável | Tipo | Descrição | Valor |
|---|---|---|---|
| `LITTER_SIZE_MIN` | Inteiro | Tamanho mínimo da ninhada (aleatório entre min e max) | 5 |
| `LITTER_SIZE_MAX` | Inteiro | Tamanho máximo da ninhada | 9 |
| `STRESS_SPREAD_RATE` | Float | Taxa de contágio social de estresse entre vizinhos | 0.03 |
| `HUNGER_THRESHOLD` | Float | Limiar de fome que dispara busca por estação de comida | 0.5 |
| `CORPSE_DECAY_TURNS` | Inteiro | Turnos que um cadáver permanece no grid antes de desaparecer | 5 |
| `STEPS` | Inteiro | Número de turnos padrão da simulação | 900 |
| `COLONY_STRESS_DIVISOR` | Inteiro | População que equivale a 50% do estresse da colônia (via pop/divisor × 0.5 + stress_médio × 0.5) | 3500 |
| `RESORPTION_PROBABILITY` | Float | Chance de uma gestação ser reabsorvida a cada turno, escalando com o estresse individual | 0.35 |
| `MATERNAL_AGGRESSION_THRESHOLD` | Float | Nível de estresse individual acima do qual a mãe pode atacar e matar seus próprios filhotes | 0.40 |
