import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from wordcloud import WordCloud
import io
import base64


#========================CONFIGURAÇÕES DE TEMA (Design Profissional Azul Escuro)========================#

TEMA_BG = '#0A192F'        # Fundo principal (Azul Marinho muito escuro)
TEMA_CARD = '#112240'      # Fundo dos gráficos (Azul Slate)
TEMA_TEXTO = '#CCD6F6'     # Cor do texto principal (Azul clarinho)
TEMA_TITULO = '#64FFDA'    # Destaque para títulos (Ciano/Verde água)
COR_SEGURO = '#3B82F6'     # Azul vivo para classe Segura
COR_INSEGURO = '#F97316'   # Laranja vivo para classe Insegura

TEMA_PLOTLY = 'plotly_dark'


#========================CARREGAMENTO E BLINDAGEM DOS DADOS========================#

def preparar_dados(df_temp):
    df_temp = df_temp.copy()
    
    if 'source' not in df_temp.columns:
        cols_source = [c for c in df_temp.columns if c.startswith('source_')]
        df_temp['source'] = df_temp[cols_source].idxmax(axis=1).astype(str).str.replace('source_', '') if cols_source else 'Desconhecida'

    if 'categories' not in df_temp.columns and 'category' not in df_temp.columns:
        cols_cat = [c for c in df_temp.columns if c.startswith('category_') or c.startswith('categories_')]
        df_temp['categories'] = df_temp[cols_cat].idxmax(axis=1).astype(str).apply(lambda x: x.split('_', 1)[-1]) if cols_cat else 'Desconhecida'
    elif 'category' in df_temp.columns:
        df_temp['categories'] = df_temp['category']

    for col in ['text_length', 'n_uppercase_ratio', 'n_special_chars', 'n_urls', 'word_count']:
        if col not in df_temp.columns:
            df_temp[col] = 0
            
    if 'text' not in df_temp.columns:
        df_temp['text'] = "Texto Indisponível"

    return df_temp

print("Carregando bases de dados...")
df_antes = preparar_dados(pd.read_parquet('df_antes.parquet'))
df_depois = preparar_dados(pd.read_parquet('df_depois.parquet'))
print("Bases carregadas com sucesso!")


#========================FUNÇÕES GERADORAS DE GRÁFICOS========================#

def layout_grafico():
    return dict(plot_bgcolor=TEMA_CARD, paper_bgcolor=TEMA_CARD, font=dict(color=TEMA_TEXTO))

def gerar_nuvem_palavras(textos, titulo, colormap):
    texto_junto = " ".join(textos.astype(str).sample(min(1000, len(textos))).tolist())
    wc = WordCloud(width=500, height=300, background_color=TEMA_CARD, colormap=colormap, max_words=80).generate(texto_junto)
    
    img = wc.to_image()
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    encoded = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return html.Div(style={'backgroundColor': TEMA_CARD, 'padding': '15px', 'borderRadius': '10px', 'textAlign': 'center', 'height': '100%'}, children=[
        html.H4(titulo, style={'color': TEMA_TEXTO, 'marginBottom': '10px'}),
        html.Img(src=f'data:image/png;base64,{encoded}', style={'width': '100%', 'borderRadius': '5px'})
    ])


#========================APLICAÇÃO DASH========================#

app = dash.Dash(__name__, suppress_callback_exceptions=True)

app.layout = html.Div(style={'backgroundColor': TEMA_BG, 'minHeight': '100vh', 'padding': '30px', 'fontFamily': 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif'}, children=[
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


#========================PÁGINA 1: VISÃO GERAL========================# 

def layout_pagina_1():
    return html.Div([
        html.Div([
            html.H1("Visão Geral do Dataset (Guardrails Training Data)", style={'color': '#EC7000', 'fontFamily': '"Itau Display", "Itau Text", Arial, sans-serif','display': 'inline-block'}),
            dcc.Link(html.Button("➡️ Ir para Análise Variável Alvo (Target)", style={'float': 'right', 'padding': '15px 25px', 'backgroundColor': COR_SEGURO, 'color': 'white', 'border': 'none', 'borderRadius': '8px', 'cursor': 'pointer', 'fontWeight': 'bold', 'fontSize': '16px'}), href='/pagina-2')
        ], style={'marginBottom': '30px'}),

        html.Div(style={'textAlign': 'center', 'marginBottom': '30px', 'padding': '15px', 'backgroundColor': TEMA_CARD, 'borderRadius': '10px'}, children=[
            html.H3("Filtrar Amostragem:", style={'color': TEMA_TEXTO, 'display': 'inline-block', 'marginRight': '20px'}),
            dcc.RadioItems(
                id='filtro-amostragem',
                options=[{'label': ' Original (Antes)', 'value': 'antes'}, {'label': ' Balanceado (Depois)', 'value': 'depois'}],
                value='antes', inline=True, style={'color': TEMA_TEXTO, 'fontSize': '18px', 'display': 'inline-block'}
            )
        ]),

        html.Div(id='container-graficos-p1')
    ])

def gerar_graficos_pagina_1(df_atual):
    df_atual = df_atual.copy()
    df_atual['is_safe_str'] = df_atual['is_safe'].map({True: 'Seguro', False: 'Inseguro'})


    # Peguei no máximo 5.000 linhas para não travar o navegador nos boxplots e histogramas.
    tamanho_amostra = min(5000, len(df_atual))
    df_leve = df_atual.sample(n=tamanho_amostra, random_state=42)


    fig_safe = px.pie(df_atual, names='is_safe_str', title='Prompt Seguro?', hole=0.4, color='is_safe_str', color_discrete_map={'Seguro': COR_SEGURO, 'Inseguro': COR_INSEGURO}, template=TEMA_PLOTLY)
    fig_safe.update_layout(**layout_grafico())

    fig_cat = px.bar(df_atual['categories'].value_counts().reset_index().head(10), x='count', y='categories', orientation='h', title='Top 10 Categorias', template=TEMA_PLOTLY, color_discrete_sequence=[TEMA_TITULO])
    fig_cat.update_layout(yaxis={'categoryorder':'total ascending'}, **layout_grafico())

    fig_source = px.bar(df_atual['source'].value_counts().reset_index().head(10), x='count', y='source', orientation='h', title='Top 10 Fontes', template=TEMA_PLOTLY, color_discrete_sequence=['#A78BFA'])
    fig_source.update_layout(yaxis={'categoryorder':'total ascending'}, **layout_grafico())

    if 'original_label' in df_atual.columns:
        fig_label = px.pie(df_atual['original_label'].fillna('Vazio').value_counts().reset_index().head(10), names='original_label', values='count', title='Rótulos Originais', hole=0.3, template=TEMA_PLOTLY)
    else:
        fig_label = px.pie(title='Rótulos Originais (Indisponível)', template=TEMA_PLOTLY)
    fig_label.update_layout(**layout_grafico())

    faixas = [0, 50, 200, 500, float('inf')]
    nomes_faixas = ['Muito Curto (0-50)', 'Curto (51-200)', 'Médio (201-500)', 'Longo (>500)']
    df_len = pd.cut(df_atual['text_length'], bins=faixas, labels=nomes_faixas).value_counts().reset_index()
    fig_len_prop = px.bar(df_len, x='text_length', y='count', title='Proporção dos Tamanhos de Texto', color='text_length', template=TEMA_PLOTLY)
    fig_len_prop.update_layout(**layout_grafico())

    cross = pd.crosstab(df_atual['categories'], df_atual['source'])
    limite_cor = cross.stack().quantile(0.95)
    fig_heat_cat = px.imshow(cross, text_auto=True, aspect='auto', color_continuous_scale='Blues', range_color=[0, limite_cor] ,title='Mapa de Calor: Categories vs Source', template=TEMA_PLOTLY)
    fig_heat_cat.update_layout(height=750, xaxis_tickangle=-45, margin=dict(l=250, r=50, t=80, b=250),xaxis_tickfont=dict(size=13),yaxis_tickfont=dict(size=14), **layout_grafico())


    fig_hist_len_safe = px.histogram(df_leve, x='text_length', color='is_safe_str', barmode='overlay', title='Distribuição do Tamanho (Amostra 5k)', template=TEMA_PLOTLY, color_discrete_map={'Seguro': COR_SEGURO, 'Inseguro': COR_INSEGURO})
    fig_hist_len_safe.update_layout(xaxis=dict(range=[0, df_leve['text_length'].quantile(0.99)]), **layout_grafico())

    fig_box_len = px.box(df_leve, x='is_safe_str', y='text_length', color='is_safe_str', title='Comprimento do Texto por Segurança', color_discrete_map={'Seguro': COR_SEGURO, 'Inseguro': COR_INSEGURO}, template=TEMA_PLOTLY)
    fig_box_len.update_layout(yaxis=dict(range=[0, min(df_leve['text_length'].max(), 3000)]), **layout_grafico())

    fig_box_upper = px.box(df_leve, x='is_safe_str', y='n_uppercase_ratio', color='is_safe_str', title='Maiúsculas por Segurança', color_discrete_map={'Seguro': COR_SEGURO, 'Inseguro': COR_INSEGURO}, template=TEMA_PLOTLY)
    fig_box_upper.update_layout(**layout_grafico())
    
    fig_box_spec = px.box(df_leve, x='is_safe_str', y='n_special_chars', color='is_safe_str', title='Caracteres Especiais por Segurança', color_discrete_map={'Seguro': COR_SEGURO, 'Inseguro': COR_INSEGURO}, template=TEMA_PLOTLY)
    fig_box_spec.update_layout(yaxis=dict(range=[0, min(df_leve['n_special_chars'].max(), 500)]), **layout_grafico())

    fig_box_urls = px.box(df_leve, x='is_safe_str', y='n_urls', color='is_safe_str', title='Total de URLs por Segurança', color_discrete_map={'Seguro': COR_SEGURO, 'Inseguro': COR_INSEGURO}, template=TEMA_PLOTLY)
    fig_box_urls.update_layout(yaxis=dict(range=[0, min(df_leve['n_urls'].max(), 10)]), **layout_grafico())

    # Para categorias e fontes, achamos o Top 10 no df original, mas filtrei no df_leve
    top_10_cats = df_atual['categories'].value_counts().head(10).index
    df_top_cat_leve = df_leve[df_leve['categories'].isin(top_10_cats)]
    fig_box_cat_len = px.box(df_top_cat_leve, x='categories', y='text_length', title='Comprimento por Categoria (Top 10)', template=TEMA_PLOTLY, color_discrete_sequence=[TEMA_TITULO])
    fig_box_cat_len.update_layout(yaxis=dict(range=[0, df_top_cat_leve['text_length'].quantile(0.99)]), **layout_grafico())

    top_10_srcs = df_atual['source'].value_counts().head(10).index
    df_top_src_leve = df_leve[df_leve['source'].isin(top_10_srcs)]
    fig_box_src_word = px.box(df_top_src_leve, x='source', y='word_count', title='Contagem de Palavras por Fonte (Top 10)', template=TEMA_PLOTLY, color_discrete_sequence=['#A78BFA'])
    fig_box_src_word.update_layout(yaxis=dict(range=[0, df_top_src_leve['word_count'].quantile(0.99)]), **layout_grafico())

    # Nuvens de Palavras 
    nuvem_segura = gerar_nuvem_palavras(df_atual[df_atual['is_safe'] == True]['text'], "Nuvem: Palavras Seguras", "Blues")
    nuvem_insegura = gerar_nuvem_palavras(df_atual[df_atual['is_safe'] == False]['text'], "Nuvem: Palavras Inseguras", "Reds")

    return html.Div([
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'marginBottom': '20px'}, children=[
            dcc.Graph(figure=fig_safe, style={'borderRadius': '10px', 'overflow': 'hidden'}),
            dcc.Graph(figure=fig_cat, style={'borderRadius': '10px', 'overflow': 'hidden'})
        ]),
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'marginBottom': '20px'}, children=[
            dcc.Graph(figure=fig_source, style={'borderRadius': '10px', 'overflow': 'hidden'}),
            dcc.Graph(figure=fig_label, style={'borderRadius': '10px', 'overflow': 'hidden'})
        ]),
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'marginBottom': '20px'}, children=[
            dcc.Graph(figure=fig_len_prop, style={'borderRadius': '10px', 'overflow': 'hidden'}),
            dcc.Graph(figure=fig_hist_len_safe, style={'borderRadius': '10px', 'overflow': 'hidden'})
        ]),
        html.Div(dcc.Graph(figure=fig_heat_cat, style={'borderRadius': '10px', 'overflow': 'hidden', 'marginBottom': '20px'})),
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'marginBottom': '20px'}, children=[
            dcc.Graph(figure=fig_box_len, style={'borderRadius': '10px', 'overflow': 'hidden'}),
            dcc.Graph(figure=fig_box_upper, style={'borderRadius': '10px', 'overflow': 'hidden'})
        ]),
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'marginBottom': '20px'}, children=[
            dcc.Graph(figure=fig_box_spec, style={'borderRadius': '10px', 'overflow': 'hidden'}),
            dcc.Graph(figure=fig_box_urls, style={'borderRadius': '10px', 'overflow': 'hidden'})
        ]),
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'marginBottom': '20px'}, children=[
            dcc.Graph(figure=fig_box_cat_len, style={'borderRadius': '10px', 'overflow': 'hidden'}),
            dcc.Graph(figure=fig_box_src_word, style={'borderRadius': '10px', 'overflow': 'hidden'})
        ]),
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px'}, children=[nuvem_segura, nuvem_insegura])
    ])



#========================PÁGINA 2: Variável Alvo (Target)========================#

def renderizar_pagina_2():
    df_atual = df_depois.copy()
    df_atual['is_safe_str'] = df_atual['is_safe'].map({True: 'Seguro', False: 'Inseguro'})
    
    # --- 1. RELAÇÕES COM VARIÁVEL ALVO ---
    fig_rel_len = px.histogram(df_atual, x='text_length', color='is_safe_str', barmode='overlay', title='Relação: text_length vs Seguro', template=TEMA_PLOTLY, color_discrete_map={'Seguro': COR_SEGURO, 'Inseguro': COR_INSEGURO})
    fig_rel_len.update_layout(**layout_grafico(), xaxis=dict(range=[0, df_atual['text_length'].quantile(0.99)]))

    fig_rel_upper = px.histogram(df_atual, x='n_uppercase_ratio', color='is_safe_str', barmode='overlay', title='Relação: n_uppercase_ratio vs Seguro', template=TEMA_PLOTLY, color_discrete_map={'Seguro': COR_SEGURO, 'Inseguro': COR_INSEGURO})
    fig_rel_upper.update_layout(**layout_grafico(), xaxis=dict(range=[0, df_atual['n_uppercase_ratio'].quantile(0.99)]))

    fig_rel_spec = px.histogram(df_atual, x='n_special_chars', color='is_safe_str', barmode='overlay', title='Relação: n_special_chars vs Seguro', template=TEMA_PLOTLY, color_discrete_map={'Seguro': COR_SEGURO, 'Inseguro': COR_INSEGURO})
    fig_rel_spec.update_layout(**layout_grafico(), xaxis=dict(range=[0, df_atual['n_special_chars'].quantile(0.99)]))

    fig_rel_urls = px.histogram(df_atual, x='n_urls', color='is_safe_str', barmode='overlay', title='Relação: n_urls vs Seguro', template=TEMA_PLOTLY, color_discrete_map={'Seguro': COR_SEGURO, 'Inseguro': COR_INSEGURO})
    fig_rel_urls.update_layout(**layout_grafico(), xaxis=dict(range=[0, df_atual['n_urls'].quantile(0.99)]))

    fig_rel_word = px.histogram(df_atual, x='word_count', color='is_safe_str', barmode='overlay', title='Relação: word_count vs Seguro', template=TEMA_PLOTLY, color_discrete_map={'Seguro': COR_SEGURO, 'Inseguro': COR_INSEGURO})
    fig_rel_word.update_layout(**layout_grafico(), xaxis=dict(range=[0, df_atual['word_count'].quantile(0.99)]))

    # --- 2. ANÁLISE DE CORRELAÇÃO ---
    cols_num = ['is_safe', 'text_length', 'n_uppercase_ratio', 'n_special_chars', 'n_urls', 'word_count']
    corr = df_atual[cols_num].corr()
    
    # Heatmap
    fig_corr_map = px.imshow(corr, text_auto=".2f", aspect='auto', color_continuous_scale='RdBu_r', title='Mapa de Correlação: is_safe vs Numéricas', template=TEMA_PLOTLY)
    fig_corr_map.update_layout(**layout_grafico())

    # Barras de Força
    corr_bar = corr[['is_safe']].drop('is_safe').sort_values(by='is_safe', ascending=False)
    fig_corr_bar = px.bar(corr_bar, x=corr_bar.values.flatten(), y=corr_bar.index, orientation='h', title='Força de Correlação com is_safe', template=TEMA_PLOTLY, color=corr_bar.values.flatten(), color_continuous_scale='RdBu_r')
    fig_corr_bar.update_layout(**layout_grafico())

    # --- 3. OUTLIERS EXTREMOS ---
    cols_outliers = ['text_length', 'word_count', 'n_special_chars', 'n_urls']
    fig_out = make_subplots(rows=2, cols=2, subplot_titles=cols_outliers)
    for i, col in enumerate(cols_outliers):
        fig_out.add_trace(go.Box(y=df_atual[col], name=col, marker_color=TEMA_TITULO), row=(i//2)+1, col=(i%2)+1)
    fig_out.update_layout(title_text="Painel de Análise de Outliers", height=700, showlegend=False, template=TEMA_PLOTLY, **layout_grafico())

    # --- 4. DISTRIBUIÇÃO DOS DADOS GERAL ---
    fig_dist_len = px.histogram(df_atual, x='text_length', title='Distribuição do Tamanho do Texto', template=TEMA_PLOTLY, color_discrete_sequence=[TEMA_TITULO])
    fig_dist_len.update_layout(**layout_grafico(), xaxis=dict(range=[0, df_atual['text_length'].quantile(0.99)]))

    fig_dist_url = px.histogram(df_atual, x='n_urls', title='Distribuição de n_urls', template=TEMA_PLOTLY, color_discrete_sequence=[TEMA_TITULO])
    fig_dist_url.update_layout(**layout_grafico(), xaxis=dict(range=[0, df_atual['n_urls'].quantile(0.99)]))

    fig_dist_spec = px.histogram(df_atual, x='n_special_chars', title='Distribuição de n_special_chars', template=TEMA_PLOTLY, color_discrete_sequence=[TEMA_TITULO])
    fig_dist_spec.update_layout(**layout_grafico(), xaxis=dict(range=[0, df_atual['n_special_chars'].quantile(0.99)]))

    fig_dist_word = px.histogram(df_atual, x='word_count', title='Distribuição de word_count', template=TEMA_PLOTLY, color_discrete_sequence=[TEMA_TITULO])
    fig_dist_word.update_layout(**layout_grafico(), xaxis=dict(range=[0, df_atual['word_count'].quantile(0.99)]))


    return html.Div([
        html.Div([
            dcc.Link(html.Button("⬅️ Voltar à Visão Geral", style={'padding': '10px 20px', 'backgroundColor': '#475569', 'color': 'white', 'border': 'none', 'borderRadius': '8px', 'cursor': 'pointer', 'marginRight': '20px'}), href='/'),
            html.H1("Variável Alvo (Target): Análise Estatística (Apenas Dados Balanceados)", style={'color': TEMA_TITULO, 'display': 'inline-block'})
        ], style={'marginBottom': '30px'}),

        html.H2("1. Relações com Variável Alvo (Segurança)", style={'color': TEMA_TEXTO}),
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'marginBottom': '20px'}, children=[
            dcc.Graph(figure=fig_rel_len, style={'borderRadius': '10px', 'overflow': 'hidden'}),
            dcc.Graph(figure=fig_rel_upper, style={'borderRadius': '10px', 'overflow': 'hidden'})
        ]),
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'marginBottom': '20px'}, children=[
            dcc.Graph(figure=fig_rel_spec, style={'borderRadius': '10px', 'overflow': 'hidden'}),
            dcc.Graph(figure=fig_rel_urls, style={'borderRadius': '10px', 'overflow': 'hidden'})
        ]),
        html.Div(dcc.Graph(figure=fig_rel_word, style={'borderRadius': '10px', 'overflow': 'hidden', 'marginBottom': '40px'})),

        html.H2("2. Análise de Correlação", style={'color': TEMA_TEXTO}),
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'marginBottom': '40px'}, children=[
            dcc.Graph(figure=fig_corr_map, style={'borderRadius': '10px', 'overflow': 'hidden'}),
            dcc.Graph(figure=fig_corr_bar, style={'borderRadius': '10px', 'overflow': 'hidden'})
        ]),

        html.H2("3. Análise de possíveis outliers", style={'color': TEMA_TEXTO}),
        html.Div(dcc.Graph(figure=fig_out, style={'borderRadius': '10px', 'overflow': 'hidden', 'marginBottom': '40px'})),

        html.H2("4. Análise a distribuição geral dos dados", style={'color': TEMA_TEXTO}),
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'marginBottom': '20px'}, children=[
            dcc.Graph(figure=fig_dist_len, style={'borderRadius': '10px', 'overflow': 'hidden'}),
            dcc.Graph(figure=fig_dist_url, style={'borderRadius': '10px', 'overflow': 'hidden'})
        ]),
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'marginBottom': '40px'}, children=[
            dcc.Graph(figure=fig_dist_spec, style={'borderRadius': '10px', 'overflow': 'hidden'}),
            dcc.Graph(figure=fig_dist_word, style={'borderRadius': '10px', 'overflow': 'hidden'})
        ]),
    ])


#========================CALLBACKS========================#

@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def gerenciar_paginas(pathname):
    if pathname == '/pagina-2':
        return renderizar_pagina_2()
    return layout_pagina_1()

@app.callback(
    Output('container-graficos-p1', 'children'),
    [Input('filtro-amostragem', 'value')]
)
def atualizar_graficos_p1(filtro_amostra):
    if filtro_amostra is None:
        filtro_amostra = 'antes'
        
    df_atual = df_antes if filtro_amostra == 'antes' else df_depois
    return gerar_graficos_pagina_1(df_atual)


#========================EXECUTAR APP========================#

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)