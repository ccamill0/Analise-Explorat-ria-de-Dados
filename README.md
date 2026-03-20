# 🛡️ Análise Exploratória de Dados (EDA): Guardrails Training Data

> **Case Financeiro:** Construção de painel interativo para diagnóstico de dados focados em injeções de prompt e cibersegurança.

## 🔍 Visão Geral do Projeto
Este projeto consiste em um Dashboard interativo construído em **Python (Dash/Plotly)** para realizar a Análise Exploratória de Dados (EDA) de um dataset de segurança de LLMs (Guardrails). 

O objetivo principal não foi apenas visualizar os dados, mas diagnosticar a "saúde" do dataset antes do treinamento de algoritmos, identificando vieses, vazamentos de dados (*Data Leakage*) e oportunidades para criação de regras heurísticas de defesa em um ambiente corporativo (como um banco).

---

## 🧠 Principais Descobertas e Diagnósticos

A análise profunda dos dados revelou gargalos arquitetônicos que inviabilizariam o uso do dataset em sua forma bruta para um ambiente de produção:

### 1. O Falso Positivo do Balanceamento (Viés Temático)
O dataset original apresentava um desbalanceamento severo (90% Inseguro / 10% Seguro). Para corrigir isso, aplicou-se a técnica de *undersampling*. Embora a paridade matemática de 50/50 tenha sido atingida, o Dashboard revelou que a classe "Segura" é dominada quase que exclusivamente por conversas de um fórum de saúde mental (`suicide-watch`). 
* **Conclusão Analítica:** Um modelo treinado com esses dados associaria segurança apenas a temas de terapia, reprovando conversas financeiras benignas por falta de vocabulário correspondente.

### 2. Risco de Data Leakage (Vazamento de Dados)
A análise semântica (Nuvens de Palavras) detectou forte presença de tokens de sistema estruturais, como `start_of_turn` e `end_of_turn`, rotulados dentro da classe "Insegura".
* **Conclusão Analítica:** Sem uma etapa prévia de limpeza via Expressões Regulares (Regex), o modelo penalizaria prompts legítimos gerados pelas APIs internas do sistema, gerando altos índices de Falsos Positivos.

### 3. Engenharia de Features e Regras Heurísticas
Variáveis comportamentais criadas no projeto (como *comprimento do texto* e *contagem de caracteres especiais*) apresentaram correlação linear fraca com a variável alvo. Contudo, a análise de *Outliers* revelou o *modus operandi* de ataques de força bruta (ex: textos com mais de 40.000 caracteres).
* **Conclusão Analítica:** A arquitetura de segurança não deve depender exclusivamente de Inteligência Artificial. Recomenda-se uma defesa em múltiplas camadas, implementando WAFs (*Hard Rules*) para bloquear instantaneamente anomalias volumétricas, economizando custos de inferência de LLM.

---

## 🛠️ Estrutura Técnica e Ferramentas

* **Linguagem:** Python 3.x
* **Framework Web:** Dash (Plotly) para Dataviz interativo
* **Manipulação de Dados:** Pandas, NumPy
* **Técnicas Aplicadas:** Feature Engineering, Undersampling, Análise de Multicolinearidade (Pearson), Distribuição de Cauda Longa.

---

## 🚀 Como Executar o Projeto

Para rodar este Dashboard localmente na sua máquina, siga os passos abaixo:

**1. Clone este repositório:**
```bash
git clone [https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git](https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git)