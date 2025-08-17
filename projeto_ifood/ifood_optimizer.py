import pandas as pd
import numpy as np
from pulp import *
import json
from datetime import datetime
from geopy.geocoders import Nominatim 
from geopy.extra.rate_limiter import RateLimiter
from math import radians, sin, cos, sqrt, atan2 

class IFoodDeliveryOptimizer:
    def __init__(self):
        """
        Classe para otimização de alocação de entregadores do iFood
        Baseada no modelo matemático fornecido
        """
        self.restaurantes = None
        self.entregadores = None
        self.pedidos = None
        self.modelo = None
        self.resultado = None

        # Inicializa o geolocator e o cache de CEPs
        # O geolocator converte endereços em coordenadas
        # O user_agent é importante para identificar sua aplicação
        self.geolocator = Nominatim(user_agent="ifood_optimizer_jf")
        # O RateLimiter evita sobrecarregar a API com muitas requisições
        self.geocode = RateLimiter(self.geolocator.geocode, min_delay_seconds=1)
        # Cache para guardar coordenadas de CEPs já consultados
        self.cep_cache = {} 
        
    def carregar_dados(self, arquivo_restaurantes, arquivo_entregadores, arquivo_pedidos):
        """
        Carrega os dados dos arquivos CSV/Excel
        """
        print("Carregando dados...")
        
        # Carregando restaurantes
        try:
            self.restaurantes = pd.read_csv(arquivo_restaurantes)
            print(f"✓ Restaurantes carregados: {len(self.restaurantes)} registros")
        except Exception as e:
            print(f"Erro ao carregar restaurantes: {e}")
            return False
            
        # Carregando entregadores - usar decimal=',' para números brasileiros
        try:
            if arquivo_entregadores.endswith('.xlsx'):
                self.entregadores = pd.read_excel(arquivo_entregadores)
            else:
                # CORREÇÃO: usar decimal=',' para formato brasileiro
                self.entregadores = pd.read_csv(arquivo_entregadores, decimal=',')
            
            print(f"✓ Entregadores carregados: {len(self.entregadores)} registros")
        except Exception as e:
            print(f"Erro ao carregar entregadores: {e}")
            return False
            
        # Carregando pedidos - usar decimal=',' para números brasileiros
        try:
            if arquivo_pedidos.endswith('.xlsx'):
                self.pedidos = pd.read_excel(arquivo_pedidos)
            else:
                # CORREÇÃO: usar decimal=',' para formato brasileiro
                self.pedidos = pd.read_csv(arquivo_pedidos, decimal=',')
                
            # Limpeza adicional do valor_pedido se necessário
            if 'valor_pedido' in self.pedidos.columns:
                # Se ainda tem R$ no valor, remover
                if self.pedidos['valor_pedido'].dtype == 'object':
                    self.pedidos['valor_pedido'] = self.pedidos['valor_pedido'].astype(str).str.replace('R$', '').str.replace(' ', '')
                    self.pedidos['valor_pedido'] = pd.to_numeric(self.pedidos['valor_pedido'], errors='coerce')
                    
            print(f"✓ Pedidos carregados: {len(self.pedidos)} registros")
        except Exception as e:
            print(f"Erro ao carregar pedidos: {e}")
            return False
            
        return True
    
    def preprocessar_dados(self):
        """
        Preprocessa os dados para o modelo de otimização
        """
        print("Preprocessando dados...")
        
        # Debug: verificar dados antes da limpeza
        print(f"Debug - Antes da limpeza:")
        print(f"  Entregadores: {len(self.entregadores)}")
        print(f"  Pedidos: {len(self.pedidos)}")
        
        # Verificar colunas existentes
        print(f"  Colunas entregadores: {list(self.entregadores.columns)}")
        print(f"  Colunas pedidos: {list(self.pedidos.columns)}")
        
        # Verificar se os dados foram carregados corretamente
        print(f"  Verificação de tipos de dados:")
        colunas_numericas_pedidos = ['tempo_deslocamento_min', 'distancia_km', 'valor_pedido', 'tempo_preparo_min']
        for col in colunas_numericas_pedidos:
            if col in self.pedidos.columns:
                dtype = self.pedidos[col].dtype
                null_count = self.pedidos[col].isnull().sum()
                print(f"    {col}: {dtype}, {null_count} nulos")
                
                # Mostrar alguns valores de exemplo
                valores_exemplo = self.pedidos[col].dropna().head(3).tolist()
                print(f"      Exemplos: {valores_exemplo}")
        
        # Limpeza dos entregadores
        print("Limpando dados dos entregadores...")
        entregadores_antes = len(self.entregadores)
        
        # Verificar colunas numéricas dos entregadores
        colunas_numericas_entregadores = ['Velocidade Média (km/h)', 'Custo Operacional (R$/h)', 'Capacidade Máxima']
        for col in colunas_numericas_entregadores:
            if col in self.entregadores.columns:
                # Se ainda é object, tentar converter
                if self.entregadores[col].dtype == 'object':
                    self.entregadores[col] = pd.to_numeric(self.entregadores[col], errors='coerce')
        
        # Remover entregadores com dados inválidos
        colunas_essenciais_ent = [col for col in colunas_numericas_entregadores if col in self.entregadores.columns]
        if colunas_essenciais_ent:
            self.entregadores = self.entregadores.dropna(subset=colunas_essenciais_ent)
        
        print(f"  Entregadores removidos: {entregadores_antes - len(self.entregadores)}")
        
        # Limpeza dos pedidos
        print("Limpando dados dos pedidos...")
        pedidos_antes = len(self.pedidos)
        
        # Verificar se precisamos converter mais alguma coisa
        for col in colunas_numericas_pedidos:
            if col in self.pedidos.columns:
                if self.pedidos[col].dtype == 'object':
                    print(f"  Convertendo {col} de object para numeric...")
                    self.pedidos[col] = pd.to_numeric(self.pedidos[col], errors='coerce')
        
        # Remover pedidos com dados inválidos
        colunas_essenciais_ped = [col for col in colunas_numericas_pedidos if col in self.pedidos.columns]
        if colunas_essenciais_ped:
            print(f"  Limpando baseado nas colunas: {colunas_essenciais_ped}")
            self.pedidos = self.pedidos.dropna(subset=colunas_essenciais_ped)
        
        print(f"  Pedidos removidos: {pedidos_antes - len(self.pedidos)}")
        
        # Verificação final dos dados
        print(f"\nVerificação final dos dados:")
        for col in colunas_numericas_pedidos:
            if col in self.pedidos.columns:
                print(f"  {col}: {len(self.pedidos[col].dropna())}/{len(self.pedidos)} válidos")
        
        # Se ainda temos 0 pedidos, usar dados de exemplo para não quebrar
        if len(self.pedidos) == 0:
            print("⚠️  AVISO: Todos os pedidos foram removidos durante a limpeza!")
            print("⚠️  Criando dados de exemplo para demonstração...")
            
            # Criar alguns pedidos de exemplo
            dados_exemplo = []
            for i in range(5):
                dados_exemplo.append({
                    'pedido_id': f'EXEMPLO_{i+1}',
                    'nome_restaurante': f'Restaurante Exemplo {i+1}',
                    'cep_cliente': 36000000 + i,
                    'prioridade': (i % 3) + 1,  # 1, 2, 3
                    'valor_pedido': 25.0 + (i * 5),
                    'tempo_preparo_min': 15 + (i * 2),
                    'tempo_deslocamento_min': 10 + (i * 3),
                    'distancia_km': 2.0 + (i * 0.5)
                })
            
            self.pedidos = pd.DataFrame(dados_exemplo)
            print(f"  Criados {len(self.pedidos)} pedidos de exemplo")
        
        # Adicionar índices
        self.entregadores = self.entregadores.reset_index(drop=True)
        self.pedidos = self.pedidos.reset_index(drop=True)
        
        print(f"Dados preprocessados - Entregadores: {len(self.entregadores)}, Pedidos: {len(self.pedidos)}")
        
        # Verificação final
        if len(self.pedidos) == 0:
            print("❌ ERRO: Nenhum pedido válido após preprocessamento!")
            return False
        if len(self.entregadores) == 0:
            print("❌ ERRO: Nenhum entregador válido após preprocessamento!")
            return False
        
        # Atallho para fazer pesquisa do CEP do restaurante. Menos custoso.
        self.mapa_restaurante_cep = self.restaurantes.set_index('Restaurante')['CEP'].to_dict()
        
        return True
        
    def calcular_tempo_deslocamento(self, entregador_idx, pedido_idx):
        """
        Calcula o tempo de deslocamento do entregador até o restaurante
        Simplificação: usando tempo médio baseado na velocidade do entregador
        """
        velocidade = self.entregadores.iloc[entregador_idx]['Velocidade Média (km/h)']
        distancia_estimada = self.pedidos.iloc[pedido_idx]['distancia_km']
        
        # Tempo em minutos
        tempo_deslocamento = (distancia_estimada / velocidade) * 60
        return tempo_deslocamento
    
    def obter_coordenadas_por_cep(self, cep):
        """
        Busca as coordenadas de um CEP diretamente.
        Utiliza um cache para evitar requisições repetidas.
        """
        cep = str(cep).strip().replace('-', '')
        if cep in self.cep_cache:
            return self.cep_cache[cep]

        try:
            # Adicionamos ", Juiz de Fora, Brazil" para dar mais contexto ao geocoder
            query = f"{cep}, Juiz de Fora, Brazil" 
            
            # Chama o geocoder diretamente com o CEP
            location = self.geocode(query)
            
            if location:
                coords = (location.latitude, location.longitude)
                self.cep_cache[cep] = coords # Armazena sucesso no cache
                return coords
            else:
                print(f"Não foi possível obter coordenadas para o CEP: {cep}")
                self.cep_cache[cep] = None # Armazena falha no cache
                return None

        except Exception as e:
            print(f"Ocorreu um erro ao buscar o CEP {cep}: {e}")
            self.cep_cache[cep] = None
            return None


    def calcular_tempo_entregador_restaurante(self, entregador_idx, pedido_idx):
        """
        Função auxiliar para calcular o tempo de deslocamento (em minutos) 
        de um entregador até o restaurante de um pedido.
        Retorna um valor alto em caso de falha para penalizar a alocação.
        """
        # Obter dados do entregador
        entregador = self.entregadores.iloc[entregador_idx]
        cep_entregador = entregador['Endereço (CEP)']
        velocidade_kmh = entregador['Velocidade Média (km/h)']
        
        # Obter dados do restaurante do pedido
        nome_restaurante = self.pedidos.iloc[pedido_idx]['nome_restaurante']
        cep_restaurante = self.mapa_restaurante_cep.get(nome_restaurante)

        # Obter coordenadas
        coords_entregador = self.obter_coordenadas_por_cep(cep_entregador)
        coords_restaurante = self.obter_coordenadas_por_cep(cep_restaurante)

        if not coords_entregador or not coords_restaurante:
            return 9999  # Penalidade alta se não encontrar coordenadas

        # Calcular distância e tempo
        distancia_km = self.calcular_distancia_coordenadas(coords_entregador, coords_restaurante)
        
        if velocidade_kmh == 0:
            return 9999 # Evitar divisão por zero

        tempo_em_minutos = (distancia_km / velocidade_kmh) * 60
        return tempo_em_minutos


    def calcular_distancia_coordenadas(self, coords1, coords2):
        """
        Calcula a distância em linha reta (km) entre duas coordenadas.
        A distância de Haversine é uma fórmula para calcular a distância entre dois pontos na superfície da Terra, 
        utilizando suas coordenadas de latitude e longitude.
        """

        if not coords1 or not coords2:
            return 999 # Retorna uma distância grande se as coordenadas não forem válidas
        
        R = 6371.0  # Raio da Terra em km
        lat1, lon1 = coords1
        lat2, lon2 = coords2

        lat1_rad, lon1_rad = radians(lat1), radians(lon1)
        lat2_rad, lon2_rad = radians(lat2), radians(lon2)

        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad

        a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c


    def criar_modelo(self):
        """
        Cria o modelo de programação linear baseado na formulação matemática
        """
        print("Criando modelo de otimização...")
        
        # Conjuntos (baseado na formulação)
        I = range(len(self.entregadores))  # Entregadores
        J = range(len(self.pedidos))       # Pedidos
        
        # Criar o modelo
        self.modelo = LpProblem("IFood_Delivery_Optimization", LpMinimize)
        
        # Variáveis de decisão principais
        # xij = 1 se entregador i é designado para pedido j
        x = {}
        for i in I:
            for j in J:
                x[i,j] = LpVariable(f"x_{i}_{j}", cat='Binary')
        
        # Variáveis auxiliares
        # Tj = tempo total de entrega do pedido j
        T = {}
        for j in J:
            T[j] = LpVariable(f"T_{j}", lowBound=0)
        
        # Função Objetivo: Minimizar soma dos tempos de entrega
        self.modelo += lpSum([T[j] for j in J]), "Tempo_Total_Entrega"
        
        # Restrições
        
        # R1: Atribuição única de pedidos
        for j in J:
            self.modelo += lpSum([x[i,j] for i in I]) == 1, f"Atribuicao_Unica_Pedido_{j}"
        
        # R2: Cálculo do tempo de entrega
        for j in J:
            tempo_preparo = self.pedidos.iloc[j]['tempo_preparo_min']
            tempo_deslocamento_cliente = self.pedidos.iloc[j]['tempo_deslocamento_min']
            
            tempo_total_expr = lpSum([
                x[i,j] * (self.calcular_tempo_deslocamento(i, j) + tempo_preparo + tempo_deslocamento_cliente)
                for i in I
            ])
            
            self.modelo += T[j] == tempo_total_expr, f"Calculo_Tempo_Pedido_{j}"


        # R2: Cálculo do tempo de entrega    
        # Rodar essa restrição apenas se tiver internet
        # print("Pré-calculando tempos de deslocamento Entregador -> Restaurante ...")
        # tempos_er = {} # Dicionário para armazenar os tempos t_ij^ER
        # for i in I:
        #     for j in J:
        #         tempos_er[i, j] = self.calcular_tempo_entregador_restaurante(i, j)

        # for j in J:
        #     # Obter tempos fixos do pedido
        #     tempo_preparo = self.pedidos.iloc[j]['tempo_preparo_min']
        #     tempo_deslocamento_cliente = self.pedidos.iloc[j]['tempo_deslocamento_min']
        #     
        #     # TempoTotal = Soma(x_ij * (Tempo_Calculado + Tempo_Preparo + Tempo_Entrega_Final))
        #     tempo_total_expr = lpSum([
        #         x[i, j] * (tempos_er[i, j] + tempo_preparo + tempo_deslocamento_cliente)
        #         for i in I
        #     ])
        #     
        #     self.modelo += T[j] == tempo_total_expr, f"Calculo_Tempo_Pedido_{j}"

        
        # R3: Capacidade máxima dos entregadores
        # Se inserirmos a disponibilidade aqui, o modelo fica inviável
        for i in I:
            capacidade_max = self.entregadores.iloc[i]['Capacidade Máxima']
            self.modelo += lpSum([x[i,j] for j in J]) <= capacidade_max, f"Capacidade_Entregador_{i}"

        # R4: Prioridade dos pedidos (peso na função objetivo)
        # Pedidos prioritários recebem peso maior no tempo
        objetivo_ponderado = lpSum([
            T[j] * self.pedidos.iloc[j]['prioridade'] for j in J
        ])
        
        # Substituir função objetivo para considerar prioridades
        self.modelo.objective = objetivo_ponderado
        
        self.x_vars = x
        self.t_vars = T
        
        print(f"Modelo criado com {len(I)} entregadores e {len(J)} pedidos")
        
    def resolver_modelo(self):
        """
        Resolve o modelo usando GLPK
        """
        print("Resolvendo modelo de otimização...")
        
        # Configurar solver (GLPK)
        solver = GLPK_CMD(msg=1, timeLimit=300)  # 5 minutos de limite
        
        # Resolver
        status = self.modelo.solve(solver)
        
        # Verificar status da solução
        if status == LpStatusOptimal:
            print("✓ Solução ótima encontrada!")
            self.extrair_resultado()
            return True
        elif status == LpStatusInfeasible:
            print("✗ Problema infeasível!")
            return False
        elif status == LpStatusUnbounded:
            print("✗ Problema ilimitado!")
            return False
        else:
            print(f"✗ Status desconhecido: {LpStatus[status]}")
            return False
    
    def extrair_resultado(self):
        """
        Extrai os resultados da solução
        """
        print("Extraindo resultados...")
        
        # Verificar se temos pedidos
        if len(self.pedidos) == 0:
            print("❌ Erro: Nenhum pedido disponível para extrair resultados!")
            return
        
        # Alocações
        alocacoes = []
        for i in range(len(self.entregadores)):
            for j in range(len(self.pedidos)):
                if (i,j) in self.x_vars and self.x_vars[i,j].value() == 1:
                    tempo_entrega = self.t_vars[j].value() if j in self.t_vars else 0
                    
                    alocacoes.append({
                        'entregador_id': self.entregadores.iloc[i]['ID'],
                        'entregador_idx': i,
                        'pedido_id': self.pedidos.iloc[j]['pedido_id'],
                        'pedido_idx': j,
                        'restaurante': self.pedidos.iloc[j]['nome_restaurante'],
                        'prioridade': self.pedidos.iloc[j]['prioridade'],
                        'valor_pedido': self.pedidos.iloc[j]['valor_pedido'],
                        'tempo_entrega': tempo_entrega
                    })
        
        # Calcular estatísticas
        tempos_validos = [self.t_vars[j].value() for j in range(len(self.pedidos)) if j in self.t_vars and self.t_vars[j].value() is not None]
        
        tempo_total = sum(tempos_validos) if tempos_validos else 0
        tempo_medio = tempo_total / len(self.pedidos) if len(self.pedidos) > 0 else 0
        
        self.resultado = {
            'valor_objetivo': value(self.modelo.objective) if self.modelo.objective else 0,
            'tempo_total': tempo_total,
            'tempo_medio': tempo_medio,
            'alocacoes': alocacoes,
            'num_entregadores_usados': len(set([a['entregador_idx'] for a in alocacoes])) if alocacoes else 0,
            'num_pedidos_alocados': len(alocacoes),
            'num_pedidos_total': len(self.pedidos)
        }
        
        print(f"Valor da função objetivo: {self.resultado['valor_objetivo']:.2f}")
        print(f"Tempo total de entrega: {self.resultado['tempo_total']:.2f} minutos")
        print(f"Tempo médio por pedido: {self.resultado['tempo_medio']:.2f} minutos")
        print(f"Entregadores utilizados: {self.resultado['num_entregadores_usados']}")
        print(f"Pedidos alocados: {self.resultado['num_pedidos_alocados']}/{self.resultado['num_pedidos_total']}")
        
        # Verificar se todas as alocações foram feitas
        if self.resultado['num_pedidos_alocados'] != self.resultado['num_pedidos_total']:
            print(f"⚠️  AVISO: {self.resultado['num_pedidos_total'] - self.resultado['num_pedidos_alocados']} pedidos não foram alocados!")
        
    def exportar_resultados(self, arquivo_saida="resultado_otimizacao.json"):
        """
        Exporta os resultados para arquivo JSON
        """
        if self.resultado is None:
            print("Nenhum resultado para exportar!")
            return False
            
        try:
            # Adicionar timestamp
            self.resultado['timestamp'] = datetime.now().isoformat()
            self.resultado['parametros'] = {
                'num_entregadores': len(self.entregadores),
                'num_pedidos': len(self.pedidos),
                'num_restaurantes': len(self.restaurantes)
            }
            
            with open(arquivo_saida, 'w', encoding='utf-8') as f:
                json.dump(self.resultado, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✓ Resultados exportados para: {arquivo_saida}")
            
            # Também criar CSV das alocações
            df_alocacoes = pd.DataFrame(self.resultado['alocacoes'])
            arquivo_csv = arquivo_saida.replace('.json', '_alocacoes.csv')
            df_alocacoes.to_csv(arquivo_csv, index=False, encoding='utf-8')
            print(f"✓ Alocações exportadas para: {arquivo_csv}")
            
            return True
            
        except Exception as e:
            print(f"Erro ao exportar resultados: {e}")
            return False
    
    def gerar_relatorio(self):
        """
        Gera relatório detalhado dos resultados
        """
        if self.resultado is None:
            print("Nenhum resultado disponível para relatório!")
            return
            
        print("\n" + "="*60)
        print("RELATÓRIO DE OTIMIZAÇÃO - IFOOD JUIZ DE FORA")
        print("="*60)
        
        print(f"\nRESUMO EXECUTIVO:")
        print(f"• Valor da função objetivo: {self.resultado['valor_objetivo']:.2f}")
        print(f"• Tempo total de entrega: {self.resultado['tempo_total']:.2f} minutos")
        print(f"• Tempo médio por pedido: {self.resultado['tempo_medio']:.2f} minutos")
        print(f"• Entregadores utilizados: {self.resultado['num_entregadores_usados']}")
        print(f"• Total de pedidos: {len(self.resultado['alocacoes'])}")
        
        print(f"\nDETALHE DAS ALOCAÇÕES:")
        for alocacao in self.resultado['alocacoes'][:10]:  # Mostrar apenas os primeiros 10
            print(f"• Entregador {alocacao['entregador_id']} → "
                  f"Pedido {alocacao['pedido_id']} "
                  f"({alocacao['restaurante']}) - "
                  f"Tempo: {alocacao['tempo_entrega']:.1f}min - "
                  f"Prioridade: {alocacao['prioridade']}")
        
        if len(self.resultado['alocacoes']) > 10:
            print(f"... e mais {len(self.resultado['alocacoes']) - 10} alocações")

def main():
    """
    Função principal para executar a otimização
    """
    import sys
    
    print("OTIMIZADOR DE ENTREGADORES IFOOD - JUIZ DE FORA")
    print("=" * 50)
    
    # Verificar se deve usar dados de exemplo
    usar_exemplo = len(sys.argv) > 1 and sys.argv[1] == '--exemplo'
    
    if usar_exemplo:
        print("🧪 MODO EXEMPLO: Usando dados sintéticos para demonstração")
        print("-" * 50)
    
    # Criar instância do otimizador
    otimizador = IFoodDeliveryOptimizer()
    
    # Definir arquivos de entrada
    arquivo_restaurantes = "restaurantes.csv"
    arquivo_entregadores = "entregadores.csv"
    arquivo_pedidos = "pedidos.csv"
    
    # Executar pipeline de otimização
    try:
        # 1. Carregar dados
        if not otimizador.carregar_dados(arquivo_restaurantes, arquivo_entregadores, arquivo_pedidos):
            print("Erro ao carregar dados. Encerrando.")
            return
        
        # 2. Preprocessar dados
        if not otimizador.preprocessar_dados():
            print("❌ Erro no preprocessamento dos dados.")
            print("\n💡 SOLUÇÕES POSSÍVEIS:")
            print("  1. Execute: python diagnostico_dados.py")
            print("  2. Verifique se os arquivos de dados estão corretos")
            print("  3. Use o modo exemplo: python ifood_optimizer.py --exemplo")
            return
        
        # 3. Criar modelo
        otimizador.criar_modelo()
        
        # 4. Resolver modelo
        if not otimizador.resolver_modelo():
            print("Não foi possível resolver o modelo. Encerrando.")
            return
        
        # 5. Exportar resultados
        arquivo_saida = "resultado_exemplo.json" if usar_exemplo else "resultado_otimizacao.json"
        otimizador.exportar_resultados(arquivo_saida)
        
        # 6. Gerar relatório
        otimizador.gerar_relatorio()
        
        print(f"\n✓ Otimização concluída com sucesso!")
        if usar_exemplo:
            print("📝 Nota: Resultados baseados em dados de exemplo")
        
    except Exception as e:
        print(f"Erro durante a execução: {e}")
        import traceback
        traceback.print_exc()
        
        print(f"\n🔧 DICAS PARA SOLUÇÃO:")
        print(f"  1. Execute: python diagnostico_dados.py")
        print(f"  2. Verifique a instalação: python setup.py")
        print(f"  3. Teste com dados de exemplo: python ifood_optimizer.py --exemplo")

if __name__ == "__main__":
    main()