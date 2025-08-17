#!/usr/bin/env python3
"""
Exemplo de uso do otimizador iFood
"""

from ifood_optimizer import IFoodDeliveryOptimizer

def exemplo_completo():
    """
    Exemplo de uso completo do otimizador
    """
    print("=== EXEMPLO DE USO - OTIMIZADOR IFOOD ===\n")
    
    # Criar otimizador
    otimizador = IFoodDeliveryOptimizer()
    
    # Carregar dados
    print("1. Carregando dados...")
    if not otimizador.carregar_dados(
        "restaurantes.csv",
        "entregadores.csv", 
        "pedidos.csv"
    ):
        print("Erro ao carregar dados!")
        return
    
    # Preprocessar
    print("\n2. Preprocessando dados...")
    otimizador.preprocessar_dados()
    
    # Criar modelo
    print("\n3. Criando modelo de otimização...")
    otimizador.criar_modelo()
    
    # Resolver
    print("\n4. Resolvendo modelo...")
    if otimizador.resolver_modelo():
        print("\n5. Exportando resultados...")
        otimizador.exportar_resultados("resultado_exemplo.json")
        
        print("\n6. Gerando relatório...")
        otimizador.gerar_relatorio()
        
        print("\n✓ Exemplo executado com sucesso!")
    else:
        print("✗ Falha na resolução do modelo")

def exemplo_rapido():
    """
    Exemplo rápido para teste
    """
    print("=== TESTE RÁPIDO ===\n")
    
    otimizador = IFoodDeliveryOptimizer()
    
    # Carregar apenas primeiros registros para teste rápido
    if otimizador.carregar_dados(
        "restaurantes.csv",
        "entregadores.csv",
        "pedidos.csv"
    ):
        # Limitar dados para teste rápido
        otimizador.entregadores = otimizador.entregadores.head(10)
        otimizador.pedidos = otimizador.pedidos.head(20)
        
        otimizador.preprocessar_dados()
        otimizador.criar_modelo()
        
        if otimizador.resolver_modelo():
            print("✓ Teste rápido passou!")
            print(f"Tempo médio: {otimizador.resultado['tempo_medio']:.1f} min")
        else:
            print("✗ Teste rápido falhou")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rapido":
        exemplo_rapido()
    else:
        exemplo_completo()
