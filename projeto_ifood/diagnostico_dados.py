#!/usr/bin/env python3
"""
Script de diagnóstico para identificar problemas nos dados do iFood
"""

import pandas as pd
import numpy as np
import os

def diagnosticar_arquivo(caminho_arquivo, nome_arquivo):
    """
    Diagnostica um arquivo específico
    """
    print(f"\n{'='*60}")
    print(f"DIAGNÓSTICO: {nome_arquivo}")
    print(f"{'='*60}")
    
    if not os.path.exists(caminho_arquivo):
        print(f"❌ ERRO: Arquivo não encontrado: {caminho_arquivo}")
        return None
    
    try:
        # Tentar carregar o arquivo
        if caminho_arquivo.endswith('.xlsx'):
            df = pd.read_excel(caminho_arquivo)
        else:
            df = pd.read_csv(caminho_arquivo)
        
        print(f"✅ Arquivo carregado com sucesso!")
        print(f"📊 Dimensões: {df.shape[0]} linhas x {df.shape[1]} colunas")
        
        # Informações básicas
        print(f"\n📋 COLUNAS ENCONTRADAS:")
        for i, col in enumerate(df.columns, 1):
            tipo = df[col].dtype
            nulos = df[col].isnull().sum()
            unicos = df[col].nunique()
            print(f"  {i:2d}. {col:<30} | Tipo: {tipo:<10} | Nulos: {nulos:3d} | Únicos: {unicos}")
        
        # Verificar valores nulos
        print(f"\n🔍 ANÁLISE DE VALORES NULOS:")
        total_nulos = df.isnull().sum().sum()
        if total_nulos > 0:
            print(f"  Total de valores nulos: {total_nulos}")
            colunas_com_nulos = df.isnull().sum()[df.isnull().sum() > 0]
            for col, nulos in colunas_com_nulos.items():
                percentual = (nulos / len(df)) * 100
                print(f"    {col}: {nulos} nulos ({percentual:.1f}%)")
        else:
            print("  ✅ Nenhum valor nulo encontrado!")
        
        # Primeiras linhas
        print(f"\n📝 PRIMEIRAS 3 LINHAS:")
        for i, row in df.head(3).iterrows():
            print(f"  Linha {i+1}:")
            for col in df.columns:
                valor = row[col]
                if pd.isna(valor):
                    valor_str = "NaN"
                elif isinstance(valor, str):
                    valor_str = f'"{valor}"'
                else:
                    valor_str = str(valor)
                print(f"    {col}: {valor_str}")
            print()
        
        return df
        
    except Exception as e:
        print(f"❌ ERRO ao carregar arquivo: {e}")
        return None

def diagnosticar_dados_numericos(df, nome_dataset, colunas_criticas):
    """
    Diagnóstica especificamente colunas numéricas críticas
    """
    print(f"\n🔢 ANÁLISE NUMÉRICA - {nome_dataset}")
    print(f"{'-'*40}")
    
    for col in colunas_criticas:
        if col not in df.columns:
            print(f"  ❌ Coluna '{col}' não encontrada!")
            continue
            
        print(f"\n  📊 Coluna: {col}")
        serie = df[col]
        
        # Tipo atual
        print(f"    Tipo atual: {serie.dtype}")
        
        # Valores únicos (primeiros 10)
        valores_unicos = serie.unique()[:10]
        print(f"    Valores únicos (amostra): {valores_unicos}")
        
        # Tentar conversão numérica
        try:
            # Converter para string primeiro
            serie_str = serie.astype(str)
            # Limpar caracteres não numéricos
            serie_limpa = serie_str.str.replace(r'[^\d.,]', '', regex=True)
            serie_limpa = serie_limpa.str.replace(',', '.')
            # Tentar converter para numérico
            serie_numerica = pd.to_numeric(serie_limpa, errors='coerce')
            
            nulos_original = serie.isnull().sum()
            nulos_apos_conversao = serie_numerica.isnull().sum()
            perdas = nulos_apos_conversao - nulos_original
            
            print(f"    Nulos originais: {nulos_original}")
            print(f"    Nulos após conversão: {nulos_apos_conversao}")
            if perdas > 0:
                print(f"    ⚠️  PERDAS na conversão: {perdas} registros")
                
                # Mostrar valores que causaram problemas
                print(f"    Valores problemáticos:")
                problematicos = serie[serie_numerica.isnull() & serie.notnull()]
                for idx, valor in problematicos.head(5).items():
                    print(f"      Linha {idx}: '{valor}'")
            else:
                print(f"    ✅ Conversão numérica bem-sucedida!")
                
            # Estatísticas dos valores válidos
            if nulos_apos_conversao < len(serie):
                valores_validos = serie_numerica.dropna()
                print(f"    Estatísticas dos valores válidos:")
                print(f"      Min: {valores_validos.min():.2f}")
                print(f"      Max: {valores_validos.max():.2f}")
                print(f"      Média: {valores_validos.mean():.2f}")
                
        except Exception as e:
            print(f"    ❌ Erro na análise numérica: {e}")

def diagnostico_completo():
    """
    Executa diagnóstico completo de todos os arquivos
    """
    print("🔍 DIAGNÓSTICO COMPLETO DOS DADOS IFOOD")
    print("="*60)
    
    # Definir arquivos e suas características
    arquivos_para_analisar = [
        {
            'caminho': 'restaurantes.csv',
            'nome': 'RESTAURANTES',
            'colunas_criticas': ['Número', 'CEP']
        },
        {
            'caminho': 'entregadores.csv',
            'nome': 'ENTREGADORES',
            'colunas_criticas': ['Capacidade Máxima', 'Velocidade Média (km/h)', 'Custo Operacional (R$/h)', 'Disponibilidade (h/dia)']
        },
        {
            'caminho': 'pedidos.csv',
            'nome': 'PEDIDOS',
            'colunas_criticas': ['valor_pedido', 'tempo_preparo_min', 'tempo_deslocamento_min', 'distancia_km']
        }
    ]
    
    datasets = {}
    
    # Analisar cada arquivo
    for arquivo_info in arquivos_para_analisar:
        df = diagnosticar_arquivo(arquivo_info['caminho'], arquivo_info['nome'])
        if df is not None:
            datasets[arquivo_info['nome']] = df
            diagnosticar_dados_numericos(df, arquivo_info['nome'], arquivo_info['colunas_criticas'])
    
    # Resumo final
    print(f"\n{'='*60}")
    print("📋 RESUMO DO DIAGNÓSTICO")
    print(f"{'='*60}")
    
    problemas_encontrados = []
    
    for arquivo_info in arquivos_para_analisar:
        nome = arquivo_info['nome']
        if nome in datasets:
            df = datasets[nome]
            print(f"\n✅ {nome}:")
            print(f"  📊 {df.shape[0]} registros, {df.shape[1]} colunas")
            
            # Verificar problemas específicos
            if nome == 'PEDIDOS':
                # Análise específica dos pedidos
                colunas_criticas = ['tempo_deslocamento_min', 'distancia_km', 'tempo_preparo_min']
                registros_validos = len(df)
                
                for col in colunas_criticas:
                    if col in df.columns:
                        # Simular limpeza
                        serie_limpa = pd.to_numeric(
                            df[col].astype(str).str.replace(r'[^\d.,]', '', regex=True).str.replace(',', '.'),
                            errors='coerce'
                        )
                        nulos = serie_limpa.isnull().sum()
                        if nulos > 0:
                            registros_validos = min(registros_validos, len(df) - nulos)
                
                if registros_validos == 0:
                    problemas_encontrados.append(f"❌ {nome}: Todos os registros seriam removidos na limpeza!")
                elif registros_validos < len(df):
                    problemas_encontrados.append(f"⚠️  {nome}: {len(df) - registros_validos} registros seriam perdidos")
                else:
                    print(f"  ✅ Todos os registros passariam na limpeza")
            
            elif nome == 'ENTREGADORES':
                # Análise específica dos entregadores
                colunas_criticas = ['Velocidade Média (km/h)', 'Custo Operacional (R$/h)']
                temp_df = df.copy()
                
                for col in colunas_criticas:
                    if col in temp_df.columns:
                        temp_df[col] = pd.to_numeric(
                            temp_df[col].astype(str).str.replace(',', '.'),
                            errors='coerce'
                        )
                
                registros_validos = len(temp_df.dropna(subset=[col for col in colunas_criticas if col in temp_df.columns]))
                
                if registros_validos < len(df):
                    problemas_encontrados.append(f"⚠️  {nome}: {len(df) - registros_validos} registros seriam perdidos")
                else:
                    print(f"  ✅ Todos os registros passariam na limpeza")
        else:
            problemas_encontrados.append(f"❌ {nome}: Arquivo não pôde ser carregado")
    
    # Mostrar problemas encontrados
    if problemas_encontrados:
        print(f"\n🚨 PROBLEMAS IDENTIFICADOS:")
        for problema in problemas_encontrados:
            print(f"  {problema}")
        
        print(f"\n💡 SUGESTÕES PARA CORREÇÃO:")
        print(f"  1. Verifique se os arquivos de dados estão no formato correto")
        print(f"  2. Confirme se os dados numéricos usam vírgula ou ponto decimal")
        print(f"  3. Verifique se há caracteres especiais nos campos numéricos")
        print(f"  4. Considere usar dados de exemplo se os originais estão corrompidos")
    else:
        print(f"\n🎉 NENHUM PROBLEMA GRAVE IDENTIFICADO!")
        print(f"  Os dados parecem estar em bom estado para processamento.")
    
    print(f"\n📁 Para resolver problemas, você pode:")
    print(f"  1. Executar: python diagnostico_dados.py")
    print(f"  2. Corrigir os arquivos manualmente")
    print(f"  3. Usar o modo de dados de exemplo: python ifood_optimizer.py --exemplo")

if __name__ == "__main__":
    diagnostico_completo()