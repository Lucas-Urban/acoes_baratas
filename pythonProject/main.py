import math
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup

# pegando conteudo da web
from pandas import DataFrame

def somente_numero(numero):

    if type(numero) is str:

        caracteres_para_remover = ["%","$"," "]
        numero = numero.replace(".", "")
        numero = numero.replace(",", "." )
        numero = re.sub('[A-Za-z]', '', numero)

        for caractere in caracteres_para_remover:
            if numero.find(caractere) >= 0:
                numero = numero.replace(caractere,"")


    numero = float(numero)

    return numero

def get_lista_acoes():
    url = 'https://www.investsite.com.br/selecao_acoes.php'
    data = {'num_result': 1000}
    request = requests.post(url=url, data=data)

    html = request.text

    # print(html)

    # pegando tabela html
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', id='tabela_selecao_acoes')
    table_str = str(table)

    # print(table_str)

    # convertendo tabela html em estrutura de dados python
    lista_acoes: DataFrame = pd.read_html(table_str, index_col='Ação', thousands='.', decimal=',')[0]
    lista_acoes.sort_values(by='EV/EBIT', ascending= True, inplace=True)

    print('retornou ' + str(len(lista_acoes)) + ' Ações ')
    print('Colunas retornadas:')
    print(lista_acoes.columns)

    return lista_acoes

def remover_por_volume_financeiro(lista_acoes):
    # removendo ações com volume financeiro menor que 1 milhão
    removida_volume_financeiro = 0
    acoes = ''

    for index, row in lista_acoes.iterrows():
        if somente_numero(row['Volume Financ.(R$)']) < 1000000:
            lista_acoes.drop([index], inplace=True)
            removida_volume_financeiro += 1
            acoes += ' '+index

    print('removidas por não ter valor financeiro: ' + str(removida_volume_financeiro)+acoes)

    return lista_acoes

def remover_por_lucro_operacional(lista_acoes):
    # removendo ações sem lucro operacional
    removida_lucro_operacional = 0
    acoes = ''

    for index, row in lista_acoes.iterrows():
        if somente_numero(row['Margem EBIT']) < 1:
            lista_acoes.drop([index], inplace=True)
            removida_lucro_operacional += 1
            acoes += ' '+index

    print('removidas por não ter lucro operacional: ' + str(removida_lucro_operacional)+acoes)

    return lista_acoes

def remover_acoes_duplicadas(lista_acoes):
    # quando duas ações são da mesma empresa manter a que tem mais movimentação financeira
    removida_empresa_duplicada = 0
    acoes = ''

    for index, row in lista_acoes.iterrows():
        for index2, row2 in lista_acoes.iterrows():
            if row['Empresa'] == row2['Empresa'] and row['Volume Financ.(R$)'] > row2['Volume Financ.(R$)']:
                lista_acoes.drop([index2], inplace=True)
                removida_empresa_duplicada += 1
                acoes += ' '+index2

    print('removidas ações duplicadas: ' + str(removida_empresa_duplicada)+acoes)

    return lista_acoes

def carregar_html_acao(lista_acoes):
    # quando duas ações são da mesma empresa manter a que tem mais movimentação financeira

    removida_recuperacao_judicial = 0
    contador = 0
    acoes = ''
    lista_html = []

    for index, row in lista_acoes.iterrows():
        contador = contador+1
        if contador > 500:
            break

        print('carregando html ' + str(contador) + '/' + str(len(lista_acoes)) + ': ' + index, end=' - ')

        url = 'https://www.investsite.com.br/principais_indicadores.php?cod_negociacao='+index
        request = requests.post(url=url)
        html = request.text
        lista_html.append(html)

    lista_acoes['html'] = lista_html

    print("")

    return lista_acoes

def remover_recuperacao_judicial(lista_acoes):
    # removendo empresas com recuperaçào judicial

    removida_recuperacao_judicial = 0
    acoes = ''

    for index, row in lista_acoes.iterrows():

        # pegando tabela html
        soup = BeautifulSoup(row['html'], 'html.parser')
        table = soup.find('table', id='tabela_resumo_empresa')
        table_str = str(table)

        #print(table)

        dados_basicos: DataFrame = pd.read_html(table_str, thousands='.', decimal=',')[0]
        #print(dados_basicos)

        for dado_basico in dados_basicos.iterrows():
            #print(dado_basico[0])
            if dado_basico[1][0] == 'Situação Emissor' and dado_basico[1][1] != 'FASE OPERACIONAL' :
                lista_acoes.drop([index], inplace=True)
                removida_recuperacao_judicial += 1
                acoes += ' '+index


    print('removidas Recuperação Judicial: ' + str(removida_recuperacao_judicial)+acoes)

    return lista_acoes

def remover_ebit_negativo(lista_acoes):

    removido = 0
    acoes = ''

    for index, row in lista_acoes.iterrows():

        # pegando tabela html
        soup = BeautifulSoup(row['html'], 'html.parser')
        table = soup.find('table', id='tabela_resumo_empresa_dre_3meses')
        table_str = str(table)

        #print(table)

        dados_basicos: DataFrame = pd.read_html(table_str, thousands='.', decimal=',')[0]
        #print(dados_basicos)

        for dado_basico in dados_basicos.iterrows():
            #print(dado_basico[0])
            if dado_basico[1][0] == 'EBIT' and somente_numero(dado_basico[1][1]) < 0 :
                lista_acoes.drop([index], inplace=True)
                removido += 1
                acoes += ' '+index

    print('removidas com ebit negativo 3 meses: ' + str(removido)+acoes)

    removido = 0
    acoes = ''

    for index, row in lista_acoes.iterrows():

        # pegando tabela html
        soup = BeautifulSoup(row['html'], 'html.parser')
        table = soup.find('table', id='tabela_resumo_empresa_dre_12meses')
        table_str = str(table)

        #print(table)

        dados_basicos: DataFrame = pd.read_html(table_str, thousands='.', decimal=',')[0]
        #print(dados_basicos)

        for dado_basico in dados_basicos.iterrows():
            #print(dado_basico[0])
            if dado_basico[1][0] == 'EBIT' and somente_numero(dado_basico[1][1]) < 0 :
                lista_acoes.drop([index], inplace=True)
                removido += 1
                acoes += ' '+index

    print('removidas com ebit negativo 12 meses: ' + str(removido)+acoes)

    return lista_acoes

def remover_lucroliquido_negativo(lista_acoes):

    removido = 0
    acoes = ''

    for index, row in lista_acoes.iterrows():

        # pegando tabela html
        soup = BeautifulSoup(row['html'], 'html.parser')
        table = soup.find('table', id='tabela_resumo_empresa_dre_3meses')
        table_str = str(table)

        #print(table)

        dados_basicos: DataFrame = pd.read_html(table_str, thousands='.', decimal=',')[0]
        #print(dados_basicos)

        for dado_basico in dados_basicos.iterrows():
            #print(dado_basico[0])
            if dado_basico[1][0] == 'Lucro Líquido' and somente_numero(dado_basico[1][1]) < 0 :
                lista_acoes.drop([index], inplace=True)
                removido += 1
                acoes += ' '+index

    print('removidas com lucro liquido negativo 3 meses: ' + str(removido)+acoes)

    return lista_acoes

def remover_por_setor(lista_acoes):
    removido = 0
    acoes = ''

    for index, row in lista_acoes.iterrows():

        # pegando tabela html
        soup = BeautifulSoup(row['html'], 'html.parser')
        table = soup.find('table', id='tabela_resumo_empresa')
        table_str = str(table)

        # print(table)

        dados_basicos: DataFrame = pd.read_html(table_str, thousands='.', decimal=',')[0]
        # print(dados_basicos)

        for dado_basico in dados_basicos.iterrows():
            # print(dado_basico[0])
            if dado_basico[1][0] == 'Segmento' and (dado_basico[1][1]=='Bancos' or dado_basico[1][1]=='Seguradoras') :
                lista_acoes.drop([index], inplace=True)
                removido += 1
                acoes += ' ' + index

    print('removidas por setor(bancos e seguradoras): ' + str(removido) + acoes)

    return lista_acoes

def main():

    lista_acoes= get_lista_acoes()

    lista_acoes= remover_por_volume_financeiro(lista_acoes)

    lista_acoes= remover_por_lucro_operacional(lista_acoes)

    lista_acoes= remover_acoes_duplicadas(lista_acoes)

    lista_acoes= carregar_html_acao(lista_acoes)

    lista_acoes= remover_recuperacao_judicial(lista_acoes)

    lista_acoes= remover_ebit_negativo(lista_acoes)

    lista_acoes= remover_lucroliquido_negativo(lista_acoes)

    lista_acoes= remover_por_setor(lista_acoes)


    # removendo colunas do retorno
    lista_acoes.drop(['html', 'ROTanC', 'ROInvC', 'RPL' ,'ROA', 'Margem Líquida','Margem Bruta', 'Margem EBIT', 'Giro Ativo', 'Alav.Financ.','Passivo/PL','P/Rec.Líq.', 'P/FCO', 'P/FCF', 'P/EBIT','P/NCAV', 'P/Ativo Total', 'P/Cap.Giro', '# Ações Total','# Ações Ord.', '# Ações Pref.'], axis = 1, inplace = True)

    print(lista_acoes.to_string())
    #lista_acoes.to_excel(r'C:\Users\lucas\OneDrive\Área de Trabalho\acoes_baratas.xlsx')

main()