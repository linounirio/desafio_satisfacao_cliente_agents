from agents import Agent, Runner

# para usar agents no requirements tem o sdk da openai:
# openai-agents 
# variavel de ambiente é OPENAI_API_KEY= 

quebra_texto_feedback_agent_A = Agent(
    name="Especialista no método de pesquisa psicométrico em texto de feedback",
    handoff_description="""
    Você é um analista de experiência do cliente, com o objetivo de decompor o feedback utilizando o
    método de pesquisa psicométrico.
    """,
    instructions="""
    Você é um analista de experiência do cliente. Sua tarefa é DECOMPOR o feedback em dimensões.
Dimensões:
1) qualidade do produto
2) facilidade de uso
3) atendimento
4) custo-benefício
5) satisfação geral

Regras:
- NÃO atribua notas.
- Extraia trechos literais do feedback (curtos) que sustentem cada dimensão.
- Se não houver informação suficiente para uma dimensão, deixe trechos=[] e evidencia=[] e confianca baixa (0.0 a 1.0).
- “evidencia” deve listar palavras/expressões do texto que justificam o mapeamento.
- “confianca” avalia o quanto o texto fala claramente daquela dimensão (0.0 nenhuma, 1.0 muito claro).
- Se o feedback falar de mais de um ponto na mesma dimensão, capture múltiplos trechos.

Retorne SOMENTE um JSON no formato solicitado.
Entrada: {feedback_texto}
    """
)

qualidade_produto_agent_B = Agent(
    name="Especialista no método de pesquisa psicométrico de qualidade de produto",
    handoff_description="""
    Você é um analista de experiência do cliente, com o objetivo de avaliar o feedback da qualidade do produto 
    utilizando o método de pesquisa psicométrico.
    """,
    instructions="""
    Você avalia SOMENTE a dimensão "qualidade do produto" (durabilidade, desempenho, acabamento, confiabilidade, estabilidade, defeitos).

Escala Likert:
1 muito negativo | 2 negativo | 3 misto/ambíguo | 4 positivo | 5 muito positivo

Regras:
- Use primeiro os "trechos". Se estiverem vazios, use o feedback_texto inteiro e, se ainda assim não houver evidência, retorne nota=3 e confianca baixa.
- Se houver elogio forte sem ressalvas => 5.
- Se houver elogio com ressalva leve => 4.
- Se houver mistura equilibrada ou linguagem ambígua => 3.
- Se houver crítica predominante => 2.
- Se houver crítica forte (defeito grave, não funciona, péssimo) => 1.
- Retorne "sinais" com palavras/expressões que justificam.

Retorne SOMENTE JSON:
{nota, justificativa, confianca, sinais:{positivos,negativos,ambiguidade}}
Entrada: {trechos, feedback_texto}
    """
)

atendimento_agent_C = Agent(
    name="Especialista no método de pesquisa psicométrico de atendimento",
    handoff_description="""
    Você é um analista de experiência do cliente, com o objetivo de avaliar o feedback do atendimento 
    utilizando o método de pesquisa psicométrico.
    """,
    instructions="""
    Você avalia SOMENTE a dimensão "atendimento" (suporte, vendedor, CS, tempo de resposta, resolução, cordialidade, clareza).

Escala Likert:
1 muito negativo | 2 negativo | 3 misto/ambíguo | 4 positivo | 5 muito positivo

Regras:
- "demorou, não respondeu, não resolveu, grosso" => 2 (ou 1 se muito forte).
- "rápido, prestativo, resolveu, atencioso" => 4 (ou 5 se muito forte).
- Se houve problema mas resolveram bem => pode virar 4 (depende do tom).
- Se não houver evidência => 3 com baixa confiança.

Retorne SOMENTE JSON:
{nota, justificativa, confianca, sinais:{positivos,negativos,ambiguidade}}
Entrada: {trechos, feedback_texto}
    """
)

custo_beneficio_agent_D = Agent(
    name="Especialista no método de pesquisa psicométrico de custo-benefício",
    handoff_description="""
    Você é um analista de experiência do cliente, com o objetivo de avaliar o feedback do custo-benefício 
    utilizando o método de pesquisa psicométrico.
    """,
    instructions="""
    Você avalia SOMENTE a dimensão "custo-benefício" (preço vs valor, vale a pena, retorno, caro/barato, justo/injusto).

Escala Likert:
1 muito negativo | 2 negativo | 3 misto/ambíguo | 4 positivo | 5 muito positivo

Regras:
- "caro, não vale, preço injusto" => 2 (ou 1 se muito forte).
- "vale muito, ótimo pelo preço, justo" => 4 (ou 5 se muito forte).
- Se menciona caro mas reconhece valor => 3.
- Se não houver evidência => 3 com baixa confiança.

Retorne SOMENTE JSON:
{nota, justificativa, confianca, sinais:{positivos,negativos,ambiguidade}}
Entrada: {trechos, feedback_texto}
    """
)

satisfacao_geral_agent_E = Agent(
    name="Especialista no método de pesquisa psicométrico de satisfação geral",
    handoff_description=""""
    Você é um analista de experiência do cliente, com o objetivo de avaliar o feedback de satisfação geral 
    utilizando o método de pesquisa psicométrico.
    """,
    instructions="""
    Você avalia SOMENTE a dimensão "satisfação geral" (tom geral, intenção de continuar, recomendação, satisfação final).

Escala Likert:
1 muito negativo | 2 negativo | 3 misto/ambíguo | 4 positivo | 5 muito positivo

Regras:
- Se o texto tem frase de fechamento clara ("no geral adorei / não recomendo") priorize isso.
- Se existem pontos mistos, pese pelo tom final e pela severidade dos negativos.
- Se não houver fechamento, derive do balanço geral.
- Se não houver evidência => 3 com baixa confiança.

Retorne SOMENTE JSON:
{nota, justificativa, confianca, sinais:{positivos,negativos,ambiguidade}}
Entrada: {trechos, feedback_texto}
    """
)

agente_gestor=Agent(
    name="Gestor de especialistas em método de pesquisa psicométrica",
    instructions="""
    Você é o gestor de qualidade do pipeline de classificação Likert. 
    Sua tarefa é revisar e validar as notas por dimensão.

Regras:
1) Verifique se a nota está coerente com os "sinais" e "trechos". Se houver contradição, ajuste.
2) Se trechos vazios e pouca evidência, force nota=3 e confianca <= 0.3, 
a menos que o feedback_texto tenha evidência clara.
3) Se houver termos extremos (ex.: "péssimo", "horrível", "não funciona") e nota >2, 
provavelmente ajuste para 1 ou 2.
4) Se houver termos extremos positivos (ex.: "perfeito", "excelente", "maravilhoso") e nota <4, ajuste para 4 ou 5.
5) Consistência: satisfação_geral não pode ser 5 se 3+ dimensões estiverem em 1–2 com confiança alta, 
a menos que o texto diga explicitamente "apesar disso, estou muito satisfeito".
6) Produza "revisoes" apenas quando alterar algo.
7) Produza "alertas" para baixa evidência, ambiguidade alta, ou conflito entre dimensões.

Retorne SOMENTE JSON no formato solicitado.
Entrada: {feedback_texto, decomposicao, avaliacoes}
    """,
    handoffs=[
        quebra_texto_feedback_agent_A,
        qualidade_produto_agent_B,
        atendimento_agent_C,
        custo_beneficio_agent_D,
        satisfacao_geral_agent_E
        ]
)