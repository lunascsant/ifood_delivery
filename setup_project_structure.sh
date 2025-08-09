#!/bin/bash

# Script simples para criar estrutura básica do projeto iFood
echo "Criando estrutura do projeto iFood..."

# Criar diretório principal
mkdir -p projeto_ifood
cd projeto_ifood

# Criar arquivos principais conforme a árvore solicitada
touch "ifood_optimizer.py"          # Implementação principal
touch "advanced_features.py"        # Análises avançadas  
touch "setup.py"                   # Script de configuração
touch "exemplo_uso.py"             # Exemplos de uso
touch "README.md"                  # Esta documentação
touch "requirements.txt"           # Dependências

# Criar arquivos de dados (placeholders)
touch "restaurantes.csv"    # Dados dos restaurantes
touch "entregadores.csv"           # Dados dos entregadores
touch "pedidos.csv"       # Dados dos pedidos

echo "✓ Estrutura criada em: projeto_ifood/"
echo "✓ Arquivos criados:"
ls -la

echo ""
echo "Próximos passos:"
echo "1. cd projeto_ifood"
echo "2. Copiar seus arquivos de dados reais para substituir os placeholders"
echo "3. Implementar o código nos arquivos .py"

# Mostrar estrutura usando tree (se disponível) ou ls
if command -v tree &> /dev/null; then
    echo ""
    echo "Estrutura atual:"
    tree
else
    echo ""
    echo "Estrutura atual:"
    echo "projeto_ifood/"
    ls -1 | sed 's/^/├── /'
fi
