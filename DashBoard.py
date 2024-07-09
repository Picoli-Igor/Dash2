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
    html.H1('Sprint 136'),
    dcc.Graph(id='situacao-bar-chart'),
    dcc.Graph(id='usuario-bar-chart'),
    dcc.Graph(id='responsavel-bar-chart'),
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # Atualiza a cada minuto
        n_intervals=0
    )
])

# Callback para atualizar os gráficos
@app.callback(
    [Output('usuario-bar-chart', 'figure'),
     Output('responsavel-bar-chart', 'figure'),
     Output('situacao-bar-chart', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_graphs(n):
    df = fetch_data()
    
    fig_situacao = px.bar(df, x='Descrição Situacao', title='Contagem de Tickets por Situação', labels={'count': 'Nº Tickets'})
    fig_usuario = px.bar(df, x='Usuário', title='Contagem de Tickets por Usuário', labels={'count': 'Nº Tickets'})
    fig_responsavel = px.bar(df, x='Usuário responsavel', title='Contagem de Tickets por Responsável', labels={'count': 'Nº Tickets'})
    
    return fig_usuario, fig_responsavel, fig_situacao

# Rodar o servidor Dash
if __name__ == '__main__':
    app.run_server(debug=True)
