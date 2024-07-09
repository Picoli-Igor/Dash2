import pyodbc
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# Função para buscar dados do banco de dados
def fetch_data():
    # Configurações da conexão
    server = 'UNSQL01.FAIRCLOUD.COM.BR,14022'
    database = 'SSBDHELPDESK_PD'
    username = 'sa'
    password = 'sssolucoesbd@'
    connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

    # Conectando ao banco de dados
    conn = pyodbc.connect(connection_string)

    # Consulta SQL
    query = '''
    select ticket.OID, 
           CodigoTicket, 
           usuario.UserName as 'Usuário',
           usuarioresponsavel.UserName as 'Usuário responsavel',
           Situacao.DescricaoSituacao as 'Descrição Situacao'
    from ticket
    inner join SecuritySystemUser as usuario on usuario.Oid = ticket.Usuario
    inner join SecuritySystemUser as usuarioresponsavel on usuarioresponsavel.Oid = ticket.UsuarioResponsavel
    inner join Sprint sprint on sprint.Oid = ticket.Sprints
    inner join Situacao on Situacao.OID = ticket.Situacao
    where sprint.OID = 187
    '''

    # Buscando dados
    df = pd.read_sql(query, conn)

    # Fechando a conexão
    conn.close()
    
    return df

# Criação do Dash app
app = Dash(__name__)

# Layout do Dash app
app.layout = html.Div([
    html.H1('Sprint 136 - Dashboard de Tickets'),
    html.Div([
        html.Div([
            html.H4('Total de Tickets'),
            html.P(id='total-tickets')
        ], className='summary-box'),
        html.Div([
            html.H4('Total de Usuários'),
            html.P(id='total-users')
        ], className='summary-box'),
        html.Div([
            html.H4('Total de Responsáveis'),
            html.P(id='total-responsaveis')
        ], className='summary-box'),
        html.Div([
            html.H4('Total de Situações'),
            html.P(id='total-situacoes')
        ], className='summary-box'),
    ], className='summary-container'),
    dcc.Graph(id='situacao-pie-chart'),
    dcc.Graph(id='usuario-bar-chart'),
    dcc.Graph(id='responsavel-bar-chart'),
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # Atualiza a cada minuto
        n_intervals=0
    )
])

# Callback para atualizar os gráficos e resumos
@app.callback(
    [Output('total-tickets', 'children'),
     Output('total-users', 'children'),
     Output('total-responsaveis', 'children'),
     Output('total-situacoes', 'children'),
     Output('situacao-pie-chart', 'figure'),
     Output('usuario-bar-chart', 'figure'),
     Output('responsavel-bar-chart', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    df = fetch_data()
    
    total_tickets = df.shape[0]
    total_users = df['Usuário'].nunique()
    total_responsaveis = df['Usuário responsavel'].nunique()
    total_situacoes = df['Descrição Situacao'].nunique()
    
    fig_situacao = px.pie(df, names='Descrição Situacao', title='Proporção de Tickets por Situação')
    fig_usuario = px.bar(df, x='Usuário', title='Contagem de Tickets por Usuário', labels={'count': 'Nº Tickets'})
    fig_responsavel = px.bar(df, x='Usuário responsavel', title='Contagem de Tickets por Responsável', labels={'count': 'Nº Tickets'})
    
    return total_tickets, total_users, total_responsaveis, total_situacoes, fig_situacao, fig_usuario, fig_responsavel

# Rodar o servidor Dash
if __name__ == '__main__':
    app.run_server(debug=True)
