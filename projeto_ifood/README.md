# Otimização de Entregadores iFood - Juiz de Fora/MG

Este projeto implementa um modelo de programação linear para otimizar a alocação de entregadores do iFood em Juiz de Fora, minimizando o tempo total de entrega ponderado por prioridade, considerando capacidades dos entregadores, prioridades dos pedidos e custos operacionais.

## 📋 Descrição do Problema

**Objetivo**: Alocar entregadores do iFood a pedidos de forma a minimizar o tempo total de entrega ponderado pela prioridade dos pedidos.

**Considerações**:
- Capacidades máximas dos entregadores
- Prioridades dos pedidos (1=Normal, 2=Prioritário, 3=Expresso)
- Tempos de preparo e deslocamento
- Custos operacionais
- Disponibilidade dos entregadores
- **Ponderação por prioridade**: Pedidos prioritários têm peso maior na função objetivo

## 🏗️ Modelo Matemático

### Conjuntos e Índices
- **I**: Conjunto de entregadores disponíveis
- **J**: Conjunto de pedidos a serem entregues
- **R**: Conjunto de restaurantes
- **K**: Conjunto de clientes/endereços

### Variáveis de Decisão
- **x_ij ∈ {0,1}**: Vale 1 se entregador i é designado para pedido j
- **T_j ≥ 0**: Tempo total de entrega do pedido j (minutos)

### Função Objetivo
```
Minimizar: Z = Σ T_j × p_j
```

**Onde:**
- T_j = tempo total de entrega do pedido j
- p_j = prioridade do pedido j (1, 2 ou 3)

**Interpretação**: A função prioriza pedidos expressos e prioritários, penalizando mais severamente atrasos em pedidos de alta prioridade.

### Principais Restrições
1. **Atribuição única**: Cada pedido deve ser atribuído a exatamente um entregador
2. **Cálculo de tempo**: T_j = tempo_deslocamento + tempo_preparo + tempo_entrega
3. **Capacidade**: Respeitar capacidade máxima de cada entregador

## 🛠️ Instalação

### 1. Pré-requisitos
- Python 3.8+
- Solver GLPK (GNU Linear Programming Kit)

### 2. Instalação do GLPK

**Windows:**
```bash
# Baixar de: https://www.gnu.org/software/glpk/
# Extrair para C:\glpk
# Adicionar C:\glpk\w64 ao PATH do sistema
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install glpk-utils
```

**macOS:**
```bash
brew install glpk
```

### 3. Dependências Python
```bash
pip install pandas numpy pulp openpyxl xlrd
```

### 4. Configuração Automática
```bash
python setup.py
```

## 📁 Estrutura dos Arquivos

```
projeto_ifood/
├── ifood_optimizer.py          # Implementação principal
├── advanced_features.py        # Análises avançadas
├── setup.py                   # Script de configuração
├── exemplo_uso.py             # Exemplos de uso
├── README.md                  # Esta documentação
├── requirements.txt           # Dependências
├── restaurantes.csv           # Dados dos restaurantes
├── entregadores.csv           # Dados dos entregadores
└── pedidos.csv                # Dados dos pedidos
```

## 🚀 Como Usar

### Uso Básico

```python
from ifood_optimizer import IFoodDeliveryOptimizer

# Criar otimizador
otimizador = IFoodDeliveryOptimizer()

# Carregar dados
otimizador.carregar_dados(
    "restaurantes.csv",
    "entregadores.csv", 
    "pedidos.csv"
)

# Preprocessar dados
otimizador.preprocessar_dados()

# Criar e resolver modelo
otimizador.criar_modelo()
otimizador.resolver_modelo()

# Exportar resultados
otimizador.exportar_resultados("resultado.json")

# Gerar relatório
otimizador.gerar_relatorio()
```

### Execução Direta
```bash
# Otimização básica
python ifood_optimizer.py

# Exemplo completo
python exemplo_uso.py

# Teste rápido
python exemplo_uso.py rapido

# Análise completa com funcionalidades avançadas
python advanced_features.py
```

## 📊 Funcionalidades Avançadas

### 1. Análise de Sensibilidade
- Variação da capacidade dos entregadores
- Impacto no tempo total de entrega
- Identificação de pontos ótimos

### 2. Análises Estatísticas
- Distribuição de tempos de entrega
- Utilização dos entregadores
- Análise por prioridade de pedidos

### 3. Cenários Alternativos
- Otimização com restrições de tempo
- Comparação de diferentes configurações
- Análise de trade-offs

### 4. Visualizações e Relatórios
- Relatórios detalhados em JSON e TXT
- Estatísticas de performance
- Métricas de eficiência

## 📈 Resultados Esperados

### Métricas de Saída

**Principais Indicadores:**
- **Valor da função objetivo**: Soma ponderada dos tempos de entrega (considera prioridades)
- **Tempo total de entrega**: Soma simples de todos os tempos de entrega (tempo real)
- **Tempo médio por pedido**: Tempo total ÷ número de pedidos
- **Taxa de utilização**: Percentual de entregadores utilizados
- **Distribuição por prioridade**: Análise detalhada por tipo de pedido

**Interpretação dos Resultados:**
- O valor da função objetivo será sempre ≥ tempo total de entrega
- A razão entre eles indica a distribuição de prioridades dos pedidos
- Valores próximos (≈1.0x) indicam predominância de pedidos normais
- Valores altos (≈3.0x) indicam muitos pedidos expressos

**Exemplo de Saída:**
```
Valor da função objetivo: 36.221,88
Tempo total de entrega: 18.551,54 minutos
Tempo médio por pedido: 74,21 minutos
Entregadores utilizados: 85/100 (85%)
Pedidos alocados: 250/250 (100%)
```

### Arquivos de Saída
- `resultado_otimizacao.json`: Resultados principais
- `resultado_otimizacao_alocacoes.csv`: Detalhes das alocações
- `analise_completa_ifood.json`: Análises avançadas
- `analise_completa_ifood.txt`: Relatório em texto

## 🔧 Personalização

### Modificar Parâmetros
```python
# Alterar pesos das prioridades na função objetivo
# Nota: Isso requer modificação do código fonte
prioridades_customizadas = {1: 1.0, 2: 1.5, 3: 2.5}

# Definir limites de tempo específicos
tempo_max_expresso = 25  # minutos
tempo_max_prioritario = 40  # minutos

# Ajustar capacidades
capacidade_personalizada = 5  # pedidos por entregador
```

### Adicionar Restrições
```python
# Exemplo: Restrição de distância máxima
for i in I:
    for j in J:
        if distancia[i][j] > DISTANCIA_MAX:
            modelo += x[i,j] == 0
```

## 🐛 Solução de Problemas

### Erro: GLPK não encontrado
```bash
# Verificar instalação
python -c "import pulp; print(pulp.GLPK_CMD().available())"

# Se False, reinstalar GLPK conforme instruções acima
```

### Erro: Dados com vírgulas decimais
```bash
# O sistema automaticamente converte vírgulas para pontos
# Certifique-se de que os CSVs usam vírgulas como separador decimal (padrão brasileiro)
```

### Erro: Arquivo não encontrado
```bash
# Verificar arquivos no diretório
ls -la *.csv

# Executar verificação automática
python setup.py
```

### Problema infeasível
- Verificar se as capacidades dos entregadores são suficientes
- Relaxar restrições de tempo se muito restritivas
- Verificar dados de entrada por inconsistências

### Performance lenta
```python
# Para datasets grandes, limitar dados para teste
otimizador.entregadores = otimizador.entregadores.head(20)
otimizador.pedidos = otimizador.pedidos.head(50)
```

## 📚 Referências Técnicas

### Bibliotecas Utilizadas
- **PuLP**: Modelagem de programação linear
- **Pandas**: Manipulação de dados
- **NumPy**: Operações numéricas
- **GLPK**: Solver de otimização

### Algoritmos
- **Programação Linear Inteira Mista (MILP)**: Para decisões de alocação
- **Simplex**: Método de resolução (via GLPK)
- **Branch and Bound**: Para variáveis binárias

### Características do Modelo
- **Tipo**: Problema de atribuição generalizada com ponderação
- **Complexidade**: NP-difícil
- **Escalabilidade**: Testado com até 100 entregadores e 250 pedidos

## 🤝 Contribuição

Para contribuir com o projeto:

1. Faça fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📞 Suporte

Em caso de dúvidas ou problemas:

1. Verifique a seção de Solução de Problemas
2. Execute `python setup.py` para diagnóstico
3. Consulte a documentação das bibliotecas utilizadas

## 📄 Licença

Este projeto é desenvolvido para fins acadêmicos como parte do trabalho de Pesquisa Operacional.

---

**Desenvolvido para o curso de Otimização - Pesquisa Operacional**  
**Universidade Federal de Juiz de Fora - UFJF**  
**Agosto 2025**