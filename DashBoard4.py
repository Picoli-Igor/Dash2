import os
import pyodbc
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State
import plotly.express as px
import dash_bootstrap_components as dbc

# Função para buscar dados do banco de dados
def fetch_data(server, database, username, password):
    try:
        connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

        # Conectando ao banco de dados
        conn = pyodbc.connect(connection_string)

        # Consulta SQL
        query = '''
        SELECT ticket.OID, 
               CodigoTicket, 
               usuario.UserName AS 'Usuário',
               usuarioresponsavel.UserName AS 'Usuário responsavel',
               Situacao.DescricaoSituacao AS 'Descrição Situacao',
               convert(int,Situacao.CodigoSituacao) AS 'CodSituacao',
               Sprint.Nome AS 'Nome Sprint'
        FROM ticket
        INNER JOIN SecuritySystemUser AS usuario ON usuario.Oid = ticket.Usuario
        INNER JOIN SecuritySystemUser AS usuarioresponsavel ON usuarioresponsavel.Oid = ticket.UsuarioResponsavel
        INNER JOIN Sprint sprint ON sprint.Oid = ticket.Sprints
        INNER JOIN Situacao ON Situacao.OID = ticket.Situacao
        WHERE sprint.OID = 187
        '''

        # Buscando dados
        df = pd.read_sql(query, conn)

        # Fechando a conexão
        conn.close()
        
        return df
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        return pd.DataFrame()

# Criação do Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout do Dash app
app.layout = html.Div([
    html.Div([
        html.Img(src='/assets/logo.png', height=40, width=40, className='logo-image'),
        html.H1('SS Soluções'),
        html.H3(id='sprint-name')  # Subtítulo para o nome da sprint
    ], className='header'),
    html.Div(id='login-form', children=[
        dbc.Input(id='server-input', placeholder='Servidor', type='text'),
        dbc.Input(id='database-input', placeholder='Banco de Dados', type='text'),
        dbc.Input(id='username-input', placeholder='Usuário', type='text'),
        dbc.Input(id='password-input', placeholder='Senha', type='password'),
        dbc.Button('Login', id='login-button', color='primary', n_clicks=0),
        html.Div(id='login-error', style={'color': 'red'})
    ]),
    html.Div(id='content', style={'display': 'none'}, children=[
        html.Div(className='content', children=[
            html.Div([
                dbc.Stack(
                    [
                        html.Div([
                            html.H4('Total de Tickets'),
                            html.P(id='total-tickets')
                        ], className='summary-box'),
                        html.Div([
                            html.H4('Total não Iniciado'),
                            html.P(id='total-naoiniciado')
                        ], className='summary-box'),
                        html.Div([
                            html.H4('Total em Execução'),
                            html.P(id='total-execucao')
                        ], className='summary-box'),
                        html.Div([
                            html.H4('Total em Teste'),
                            html.P(id='total-testes')
                        ], className='summary-box'),
                        html.Div([
                            html.H4('Total de Concluídos'),
                            html.P(id='total-concluidos')
                        ], className='summary-box'),
                    ],
                    direction="horizontal",
                    gap=3,
                ),
            ], className='summary-container'),
            html.Div([
                dcc.Graph(id='situacao-bar-chart'),
                dcc.Graph(id='usuario-bar-chart'),
                dcc.Graph(id='responsavel-bar-chart')
            ]),
            dcc.Interval(
                id='interval-component',
                interval=60*1000,  # Atualiza a cada minuto
                n_intervals=0
            )
        ])
    ])
])

# Callback para verificar o login e buscar os dados
@app.callback(
    [Output('content', 'style'),
     Output('login-form', 'style'),
     Output('sprint-name', 'children'),
     Output('total-tickets', 'children'),
     Output('total-naoiniciado', 'children'),
     Output('total-execucao', 'children'),
     Output('total-testes', 'children'),
     Output('total-concluidos', 'children'),
     Output('situacao-bar-chart', 'figure'),
     Output('usuario-bar-chart', 'figure'),
     Output('responsavel-bar-chart', 'figure')],
    [Input('login-button', 'n_clicks')],
    [State('server-input', 'value'),
     State('database-input', 'value'),
     State('username-input', 'value'),
     State('password-input', 'value')]
)
def update_dashboard(n_clicks, server, database, username, password):
    if n_clicks > 0:
        df = fetch_data(server, database, username, password)

        if df.empty:
            return {'display': 'none'}, {'display': 'block'}, "Erro ao carregar sprint", "Erro", "Erro", "Erro", "Erro", "Erro", {}, {}, {}

        sprint_name = df['Nome Sprint'].iloc[0] if not df.empty else "Sprint não encontrada"
        
        total_tickets = df.shape[0]
        total_naoiniciado = df[df['CodSituacao'] == 3].shape[0]
        total_execucao = df[df['CodSituacao'] == 8].shape[0]
        total_testes = df[df['CodSituacao'].isin([9, 12, 13])].shape[0]
        total_concluidos = df[df['CodSituacao'].isin([7, 14, 15, 17])].shape[0]
        
        fig_situacao = px.bar(df, x='Descrição Situacao',
                              text='CodigoTicket',
                              title='Tickets por Situação',
                              hover_data={'CodigoTicket': True, 'Descrição Situacao': False},
                              labels={'Descrição Situacao': 'Situação', 'count': 'Nº de Tickets'})
        fig_situacao.update_traces(textposition='inside')
        fig_situacao.update_layout(
            xaxis_tickangle=0,
            height=600,
            margin=dict(l=20, r=20, t=50, b=150),
            uniformtext_minsize=8,
            uniformtext_mode='hide',
            xaxis_title="Situação",
            yaxis_title="Número de Tickets",
            bargap=0.2  # Adiciona espaçamento entre as barras
        )

        fig_usuario = px.bar(df, x='Usuário',
                             text='CodigoTicket',
                             title='Tickets por Usuário',
                             hover_data={'CodigoTicket': True, 'Usuário': False},
                             labels={'CodigoTicket': 'Número do Ticket', 'count': 'Nº Tickets'})
        fig_usuario.update_traces(textposition='inside')
        fig_usuario.update_layout(
            xaxis_tickangle=0,
            height=600,
            margin=dict(l=20, r=20, t=50, b=150),
            uniformtext_minsize=8,
            uniformtext_mode='hide',
            xaxis_title="Usuário",
            yaxis_title="Número de Tickets",
            bargap=0.2  # Adiciona espaçamento entre as barras
        )

        fig_responsavel = px.bar(df, x='Usuário responsavel',
                                 text='CodigoTicket',
                                 title='Tickets por Responsável',
                                 hover_data={'CodigoTicket': True, 'Usuário responsavel': False},
                                 labels={'CodigoTicket': 'Número do Ticket', 'Usuário responsavel': 'Usuário Responsável', 'count': 'Nº Tickets'})
        fig_responsavel.update_traces(textposition='inside')
        fig_responsavel.update_layout(
            xaxis_tickangle=0,
            height=600,
            margin=dict(l=20, r=20, t=50, b=150),
            uniformtext_minsize=8,
            uniformtext_mode='hide',
            xaxis_title="Usuário Responsável",
            yaxis_title="Número de Tickets",
            bargap=0.2  # Adiciona espaçamento entre as barras
        )

        return {'display': 'block'}, {'display': 'none'}, sprint_name, total_tickets, total_naoiniciado, total_execucao, total_testes, total_concluidos, fig_situacao, fig_usuario, fig_responsavel

    return {'display': 'none'}, {'display': 'block'}, "", "", "", "", "", "", {}, {}, {}

# Rodar o servidor Dash
if __name__ == '__main__':
    app.run_server(debug=True)
