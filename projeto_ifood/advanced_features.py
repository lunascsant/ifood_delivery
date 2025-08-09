"""
Funcionalidades avançadas e análises para o otimizador iFood
Extensões do modelo básico com análises de sensibilidade e melhorias
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pulp import *
import json
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class IFoodAdvancedAnalyzer:
    def __init__(self, otimizador_base):
        """
        Analisador avançado baseado no otimizador principal
        """
        self.otimizador = otimizador_base
        self.analises = {}
        
    def analise_sensibilidade_capacidade(self, range_capacidade=(1, 10)):
        """
        Análise de sensibilidade variando a capacidade dos entregadores
        """
        print("Executando análise de sensibilidade - Capacidade...")
        
        resultados = []
        capacidade_original = self.otimizador.entregadores['Capacidade Máxima'].copy()
        
        for cap in range(range_capacidade[0], range_capacidade[1] + 1):
            print(f"  Testando capacidade: {cap}")
            
            # Alterar capacidade temporariamente
            self.otimizador.entregadores['Capacidade Máxima'] = cap
            
            # Recriar e resolver modelo
            self.otimizador.criar_modelo()
            if self.otimizador.resolver_modelo():
                resultados.append({
                    'capacidade': cap,
                    'tempo_total': self.otimizador.resultado['tempo_total'],
                    'tempo_medio': self.otimizador.resultado['tempo_medio'],
                    'entregadores_usados': self.otimizador.resultado['num_entregadores_usados'],
                    'valor_objetivo': self.otimizador.resultado['valor_objetivo']
                })
        
        # Restaurar capacidade original
        self.otimizador.entregadores['Capacidade Máxima'] = capacidade_original
        
        self.analises['sensibilidade_capacidade'] = pd.DataFrame(resultados)
        print(f"✓ Análise concluída com {len(resultados)} pontos")
        
        return self.analises['sensibilidade_capacidade']
    
    def analise_distribuicao_tempos(self):
        """
        Análise da distribuição de tempos de entrega
        """
        if self.otimizador.resultado is None:
            print("Execute primeiro a otimização principal!")
            return None
            
        print("Analisando distribuição de tempos...")
        
        tempos = [a['tempo_entrega'] for a in self.otimizador.resultado['alocacoes']]
        
        analise = {
            'media': np.mean(tempos),
            'mediana': np.median(tempos),
            'desvio_padrao': np.std(tempos),
            'minimo': np.min(tempos),
            'maximo': np.max(tempos),
            'q25': np.percentile(tempos, 25),
            'q75': np.percentile(tempos, 75),
            'tempos_detalhados': tempos
        }
        
        # Classificação por faixas de tempo
        faixas = {
            'muito_rapido': sum([1 for t in tempos if t <= 30]),
            'rapido': sum([1 for t in tempos if 30 < t <= 45]),
            'normal': sum([1 for t in tempos if 45 < t <= 60]),
            'lento': sum([1 for t in tempos if 60 < t <= 90]),
            'muito_lento': sum([1 for t in tempos if t > 90])
        }
        
        analise['distribuicao_faixas'] = faixas
        self.analises['distribuicao_tempos'] = analise
        
        print("✓ Análise de distribuição concluída")
        return analise
    
    def analise_utilizacao_entregadores(self):
        """
        Análise da utilização dos entregadores
        """
        if self.otimizador.resultado is None:
            print("Execute primeiro a otimização principal!")
            return None
            
        print("Analisando utilização de entregadores...")
        
        # Contar pedidos por entregador
        utilizacao = {}
        for alocacao in self.otimizador.resultado['alocacoes']:
            ent_id = alocacao['entregador_id']
            if ent_id not in utilizacao:
                utilizacao[ent_id] = {
                    'num_pedidos': 0,
                    'tempo_total': 0,
                    'valor_total': 0,
                    'pedidos': []
                }
            
            utilizacao[ent_id]['num_pedidos'] += 1
            utilizacao[ent_id]['tempo_total'] += alocacao['tempo_entrega']
            utilizacao[ent_id]['valor_total'] += alocacao['valor_pedido']
            utilizacao[ent_id]['pedidos'].append(alocacao)
        
        # Estatísticas de utilização
        pedidos_por_entregador = [u['num_pedidos'] for u in utilizacao.values()]
        
        analise = {
            'entregadores_utilizados': len(utilizacao),
            'entregadores_disponivelis': len(self.otimizador.entregadores),
            'taxa_utilizacao': len(utilizacao) / len(self.otimizador.entregadores),
            'media_pedidos_por_entregador': np.mean(pedidos_por_entregador),
            'max_pedidos_por_entregador': np.max(pedidos_por_entregador),
            'min_pedidos_por_entregador': np.min(pedidos_por_entregador),
            'desvio_pedidos': np.std(pedidos_por_entregador),
            'detalhes_utilizacao': utilizacao
        }
        
        self.analises['utilizacao_entregadores'] = analise
        
        print(f"✓ {analise['entregadores_utilizados']}/{analise['entregadores_disponivelis']} entregadores utilizados")
        print(f"  Taxa de utilização: {analise['taxa_utilizacao']:.1%}")
        print(f"  Média de pedidos por entregador: {analise['media_pedidos_por_entregador']:.1f}")
        
        return analise
    
    def analise_prioridades(self):
        """
        Análise do impacto das prioridades dos pedidos
        """
        if self.otimizador.resultado is None:
            print("Execute primeiro a otimização principal!")
            return None
            
        print("Analisando impacto das prioridades...")
        
        # Agrupar por prioridade
        por_prioridade = {}
        for alocacao in self.otimizador.resultado['alocacoes']:
            prio = alocacao['prioridade']
            if prio not in por_prioridade:
                por_prioridade[prio] = {
                    'count': 0,
                    'tempos': [],
                    'valores': []
                }
            
            por_prioridade[prio]['count'] += 1
            por_prioridade[prio]['tempos'].append(alocacao['tempo_entrega'])
            por_prioridade[prio]['valores'].append(alocacao['valor_pedido'])
        
        # Calcular estatísticas por prioridade
        analise = {}
        for prio, dados in por_prioridade.items():
            nome_prio = {1: 'Normal', 2: 'Prioritário', 3: 'Expresso'}.get(prio, f'Prioridade_{prio}')
            
            analise[nome_prio] = {
                'quantidade': dados['count'],
                'tempo_medio': np.mean(dados['tempos']),
                'tempo_min': np.min(dados['tempos']),
                'tempo_max': np.max(dados['tempos']),
                'valor_medio': np.mean(dados['valores']),
                'valor_total': np.sum(dados['valores'])
            }
        
        self.analises['analise_prioridades'] = analise
        
        print("✓ Análise de prioridades concluída")
        for nome, stats in analise.items():
            print(f"  {nome}: {stats['quantidade']} pedidos, tempo médio {stats['tempo_medio']:.1f}min")
        
        return analise
    
    def otimizacao_com_restricoes_tempo(self, tempo_max_expresso=30, tempo_max_prioritario=45):
        """
        Versão do modelo com restrições de tempo por prioridade
        """
        print(f"Otimizando com restrições de tempo:")
        print(f"  Expresso: ≤ {tempo_max_expresso} min")
        print(f"  Prioritário: ≤ {tempo_max_prioritario} min")
        
        # Criar novo modelo baseado no original
        I = range(len(self.otimizador.entregadores))
        J = range(len(self.otimizador.pedidos))
        
        modelo_restrito = LpProblem("IFood_Delivery_Restricted", LpMinimize)
        
        # Variáveis
        x = {}
        for i in I:
            for j in J:
                x[i,j] = LpVariable(f"x_{i}_{j}", cat='Binary')
        
        T = {}
        for j in J:
            T[j] = LpVariable(f"T_{j}", lowBound=0)
        
        # Função objetivo
        modelo_restrito += lpSum([T[j] * self.otimizador.pedidos.iloc[j]['prioridade'] for j in J])
        
        # Restrições originais
        for j in J:
            modelo_restrito += lpSum([x[i,j] for i in I]) == 1
        
        for i in I:
            capacidade_max = self.otimizador.entregadores.iloc[i]['Capacidade Máxima']
            modelo_restrito += lpSum([x[i,j] for j in J]) <= capacidade_max
        
        for j in J:
            tempo_preparo = self.otimizador.pedidos.iloc[j]['tempo_preparo_min']
            tempo_deslocamento_cliente = self.otimizador.pedidos.iloc[j]['tempo_deslocamento_min']
            
            tempo_total_expr = lpSum([
                x[i,j] * (self.otimizador.calcular_tempo_deslocamento(i, j) + tempo_preparo + tempo_deslocamento_cliente)
                for i in I
            ])
            
            modelo_restrito += T[j] == tempo_total_expr
        
        # Novas restrições de tempo por prioridade
        for j in J:
            prioridade = self.otimizador.pedidos.iloc[j]['prioridade']
            if prioridade == 3:  # Expresso
                modelo_restrito += T[j] <= tempo_max_expresso
            elif prioridade == 2:  # Prioritário
                modelo_restrito += T[j] <= tempo_max_prioritario
        
        # Resolver
        solver = GLPK_CMD(msg=0)
        status = modelo_restrito.solve(solver)
        
        if status == LpStatusOptimal:
            print("✓ Solução ótima encontrada com restrições de tempo!")
            
            # Extrair resultados
            alocacoes_restritas = []
            for i in I:
                for j in J:
                    if x[i,j].value() == 1:
                        alocacoes_restritas.append({
                            'entregador_id': self.otimizador.entregadores.iloc[i]['ID'],
                            'pedido_id': self.otimizador.pedidos.iloc[j]['pedido_id'],
                            'prioridade': self.otimizador.pedidos.iloc[j]['prioridade'],
                            'tempo_entrega': T[j].value()
                        })
            
            resultado_restrito = {
                'valor_objetivo': value(modelo_restrito.objective),
                'alocacoes': alocacoes_restritas,
                'tempo_total': sum([T[j].value() for j in J]),
                'restricoes_atendidas': True
            }
            
            self.analises['otimizacao_restrita'] = resultado_restrito
            return resultado_restrito
        
        else:
            print("✗ Problema infeasível com as restrições de tempo especificadas")
            return None
    
    def comparar_cenarios(self):
        """
        Compara diferentes cenários de otimização
        """
        print("Comparando cenários de otimização...")
        
        cenarios = {}
        
        # Cenário 1: Original
        if self.otimizador.resultado:
            cenarios['Original'] = {
                'tempo_total': self.otimizador.resultado['tempo_total'],
                'tempo_medio': self.otimizador.resultado['tempo_medio'],
                'entregadores_usados': self.otimizador.resultado['num_entregadores_usados']
            }
        
        # Cenário 2: Com restrições de tempo
        if 'otimizacao_restrita' in self.analises:
            rest = self.analises['otimizacao_restrita']
            cenarios['Com_Restricoes_Tempo'] = {
                'tempo_total': rest['tempo_total'],
                'tempo_medio': rest['tempo_total'] / len(rest['alocacoes']),
                'entregadores_usados': len(set([a['entregador_id'] for a in rest['alocacoes']]))
            }
        
        # Cenário 3: Capacidade reduzida
        print("  Testando cenário com capacidade reduzida...")
        cap_original = self.otimizador.entregadores['Capacidade Máxima'].copy()
        self.otimizador.entregadores['Capacidade Máxima'] = self.otimizador.entregadores['Capacidade Máxima'] // 2 + 1
        
        self.otimizador.criar_modelo()
        if self.otimizador.resolver_modelo():
            cenarios['Capacidade_Reduzida'] = {
                'tempo_total': self.otimizador.resultado['tempo_total'],
                'tempo_medio': self.otimizador.resultado['tempo_medio'],
                'entregadores_usados': self.otimizador.resultado['num_entregadores_usados']
            }
        
        # Restaurar capacidade
        self.otimizador.entregadores['Capacidade Máxima'] = cap_original
        
        self.analises['comparacao_cenarios'] = cenarios
        
        print("✓ Comparação de cenários concluída")
        print("\nRESUMO DOS CENÁRIOS:")
        print("-" * 50)
        for nome, dados in cenarios.items():
            print(f"{nome}:")
            print(f"  Tempo total: {dados['tempo_total']:.1f} min")
            print(f"  Tempo médio: {dados['tempo_medio']:.1f} min")
            print(f"  Entregadores: {dados['entregadores_usados']}")
            print()
        
        return cenarios
    
    def gerar_relatorio_completo(self, arquivo_saida="relatorio_completo.json"):
        """
        Gera relatório completo com todas as análises
        """
        print("Gerando relatório completo...")
        
        relatorio = {
            'timestamp': datetime.now().isoformat(),
            'otimizacao_original': self.otimizador.resultado,
            'analises_avancadas': self.analises
        }
        
        # Salvar JSON
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False, default=str)
        
        # Gerar relatório em texto
        arquivo_txt = arquivo_saida.replace('.json', '.txt')
        with open(arquivo_txt, 'w', encoding='utf-8') as f:
            f.write("RELATÓRIO COMPLETO - OTIMIZAÇÃO IFOOD JUIZ DE FORA\n")
            f.write("=" * 60 + "\n\n")
            
            # Resumo executivo
            f.write("RESUMO EXECUTIVO\n")
            f.write("-" * 20 + "\n")
            if self.otimizador.resultado:
                f.write(f"Tempo total de entrega: {self.otimizador.resultado['tempo_total']:.1f} min\n")
                f.write(f"Tempo médio por pedido: {self.otimizador.resultado['tempo_medio']:.1f} min\n")
                f.write(f"Entregadores utilizados: {self.otimizador.resultado['num_entregadores_usados']}\n")
                f.write(f"Total de pedidos: {len(self.otimizador.resultado['alocacoes'])}\n\n")
            
            # Análises detalhadas
            if 'distribuicao_tempos' in self.analises:
                dist = self.analises['distribuicao_tempos']
                f.write("DISTRIBUIÇÃO DE TEMPOS\n")
                f.write("-" * 25 + "\n")
                f.write(f"Tempo mínimo: {dist['minimo']:.1f} min\n")
                f.write(f"Tempo máximo: {dist['maximo']:.1f} min\n")
                f.write(f"Mediana: {dist['mediana']:.1f} min\n")
                f.write(f"Desvio padrão: {dist['desvio_padrao']:.1f} min\n\n")
                
                f.write("Distribuição por faixas:\n")
                for faixa, count in dist['distribuicao_faixas'].items():
                    f.write(f"  {faixa}: {count} pedidos\n")
                f.write("\n")
            
            if 'utilizacao_entregadores' in self.analises:
                util = self.analises['utilizacao_entregadores']
                f.write("UTILIZAÇÃO DE ENTREGADORES\n")
                f.write("-" * 30 + "\n")
                f.write(f"Taxa de utilização: {util['taxa_utilizacao']:.1%}\n")
                f.write(f"Média de pedidos por entregador: {util['media_pedidos_por_entregador']:.1f}\n")
                f.write(f"Desvio padrão: {util['desvio_pedidos']:.1f}\n\n")
            
            if 'analise_prioridades' in self.analises:
                prio = self.analises['analise_prioridades']
                f.write("ANÁLISE POR PRIORIDADE\n")
                f.write("-" * 25 + "\n")
                for nome, stats in prio.items():
                    f.write(f"{nome}:\n")
                    f.write(f"  Quantidade: {stats['quantidade']} pedidos\n")
                    f.write(f"  Tempo médio: {stats['tempo_medio']:.1f} min\n")
                    f.write(f"  Valor total: R$ {stats['valor_total']:.2f}\n\n")
        
        print(f"✓ Relatório completo salvo em: {arquivo_saida}")
        print(f"✓ Relatório em texto salvo em: {arquivo_txt}")
        
        return relatorio

def executar_analise_completa():
    """
    Executa análise completa do sistema iFood
    """
    print("ANÁLISE COMPLETA DO SISTEMA IFOOD")
    print("=" * 40)
    
    # Importar otimizador principal
    from ifood_optimizer import IFoodDeliveryOptimizer
    
    # Criar otimizador
    otimizador = IFoodDeliveryOptimizer()
    
    # Carregar e processar dados
    if not otimizador.carregar_dados(
        "restaurantes.csv",
        "entregadores.csv",
        "pedidos.csv"
    ):
        print("Erro ao carregar dados!")
        return
    
    otimizador.preprocessar_dados()
    otimizador.criar_modelo()
    
    # Resolver otimização principal
    if not otimizador.resolver_modelo():
        print("Erro na otimização principal!")
        return
    
    # Criar analisador avançado
    analisador = IFoodAdvancedAnalyzer(otimizador)
    
    print("\n1. Executando análises básicas...")
    analisador.analise_distribuicao_tempos()
    analisador.analise_utilizacao_entregadores()
    analisador.analise_prioridades()
    
    print("\n2. Executando análise de sensibilidade...")
    analisador.analise_sensibilidade_capacidade(range_capacidade=(1, 8))
    
    print("\n3. Testando otimização com restrições...")
    analisador.otimizacao_com_restricoes_tempo(tempo_max_expresso=25, tempo_max_prioritario=40)
    
    print("\n4. Comparando cenários...")
    analisador.comparar_cenarios()
    
    print("\n5. Gerando relatório completo...")
    analisador.gerar_relatorio_completo("analise_completa_ifood.json")
    
    print("\n✓ Análise completa finalizada com sucesso!")
    print("Arquivos gerados:")
    print("  - analise_completa_ifood.json")
    print("  - analise_completa_ifood.txt")

if __name__ == "__main__":
    executar_analise_completa()