"""
Script de configuração para o projeto de otimização do iFood
"""

import subprocess
import sys
import os

def instalar_dependencias():
    """
    Instala as dependências necessárias
    """
    print("Instalando dependências...")
    
    dependencias = [
        "pandas>=1.5.0",
        "numpy>=1.21.0", 
        "pulp>=2.7.0",
        "openpyxl>=3.0.0",
        "xlrd>=2.0.0",
        "geopy>=2.2.0",
    ]
    
    for dep in dependencias:
        try:
            print(f"Instalando {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
        except subprocess.CalledProcessError as e:
            print(f"Erro ao instalar {dep}: {e}")
            return False
    
    print("✓ Dependências instaladas com sucesso!")
    return True

def verificar_glpk():
    """
    Verifica se o GLPK está instalado
    """
    print("Verificando instalação do GLPK...")
    
    try:
        import pulp
        # Tenta criar um solver GLPK
        solver = pulp.GLPK_CMD(msg=0)
        
        # Teste simples
        prob = pulp.LpProblem("teste", pulp.LpMinimize)
        x = pulp.LpVariable("x", lowBound=0)
        prob += x
        prob += x >= 1
        
        status = prob.solve(solver)
        
        if status == pulp.LpStatusOptimal:
            print("✓ GLPK está funcionando corretamente!")
            return True
        else:
            print("⚠ GLPK encontrado mas com problemas")
            return False
            
    except Exception as e:
        print(f"✗ Erro com GLPK: {e}")
        print("\nINSTRUÇÕES PARA INSTALAR GLPK:")
        print("─" * 40)
        print("Windows:")
        print("1. Baixe GLPK em: https://www.gnu.org/software/glpk/")
        print("2. Extraia para C:\\glpk")
        print("3. Adicione C:\\glpk\\w64 ao PATH")
        print()
        print("Linux (Ubuntu/Debian):")
        print("sudo apt-get install glpk-utils")
        print()
        print("macOS:")
        print("brew install glpk")
        print()
        return False

def verificar_arquivos():
    """
    Verifica se os arquivos de dados existem
    """
    print("Verificando arquivos de dados...")
    
    arquivos_necessarios = [
        "restaurantes.csv",
        "entregadores.csv", 
        "pedidos.csv"
    ]
    
    arquivos_encontrados = []
    arquivos_faltantes = []
    
    for arquivo in arquivos_necessarios:
        if os.path.exists(arquivo):
            print(f"✓ {arquivo}")
            arquivos_encontrados.append(arquivo)
        else:
            print(f"✗ {arquivo}")
            arquivos_faltantes.append(arquivo)
    
    if arquivos_faltantes:
        print(f"\n⚠ {len(arquivos_faltantes)} arquivo(s) faltante(s):")
        for arquivo in arquivos_faltantes:
            print(f"  - {arquivo}")
        print("\nCertifique-se de que os arquivos estão no mesmo diretório do script.")
        return False
    
    print(f"\n✓ Todos os {len(arquivos_necessarios)} arquivos encontrados!")
    return True

def criar_exemplo_uso():
    """
    Cria script de exemplo de uso
    """
    exemplo = '''#!/usr/bin/env python3
"""
Exemplo de uso do otimizador iFood
"""

from ifood_optimizer import IFoodDeliveryOptimizer

def exemplo_completo():
    """
    Exemplo de uso completo do otimizador
    """
    print("=== EXEMPLO DE USO - OTIMIZADOR IFOOD ===\\n")
    
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
    print("2. Preprocessando dados...")
    otimizador.preprocessar_dados()
    
    # Criar modelo
    print("3. Criando modelo de otimização...")
    otimizador.criar_modelo()
    
    # Resolver
    print("4. Resolvendo modelo...")
    if otimizador.resolver_modelo():
        print("5. Exportando resultados...")
        otimizador.exportar_resultados("resultado_exemplo.json")
        
        print("6. Gerando relatório...")
        otimizador.gerar_relatorio()
        
        print("\\n✓ Exemplo executado com sucesso!")
    else:
        print("✗ Falha na resolução do modelo")

def exemplo_rapido():
    """
    Exemplo rápido para teste
    """
    print("=== TESTE RÁPIDO ===\\n")
    
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
'''
    
    with open("exemplo_uso.py", "w", encoding="utf-8") as f:
        f.write(exemplo)
    
    print("✓ Arquivo exemplo_uso.py criado!")

def main():
    """
    Função principal de setup
    """
    print("CONFIGURAÇÃO DO PROJETO IFOOD OTIMIZAÇÃO")
    print("=" * 45)
    
    # 1. Instalar dependências
    if not instalar_dependencias():
        print("Falha na instalação das dependências.")
        return False
    
    print()
    
    # 2. Verificar GLPK
    glpk_ok = verificar_glpk()
    
    print()
    
    # 3. Verificar arquivos
    arquivos_ok = verificar_arquivos()
    
    print()
    
    # 4. Criar exemplo
    criar_exemplo_uso()
    
    print("\n" + "=" * 45)
    print("RESUMO DA CONFIGURAÇÃO:")
    print(f"✓ Dependências Python: OK")
    print(f"{'✓' if glpk_ok else '✗'} GLPK Solver: {'OK' if glpk_ok else 'PENDENTE'}")
    print(f"{'✓' if arquivos_ok else '✗'} Arquivos de dados: {'OK' if arquivos_ok else 'FALTANTES'}")
    
    if glpk_ok and arquivos_ok:
        print("\n🎉 Setup completo! Você pode executar:")
        print("   python ifood_optimizer.py")
        print("   python exemplo_uso.py")
    else:
        print("\n⚠ Complete a instalação pendente antes de executar.")
    
    return glpk_ok and arquivos_ok

if __name__ == "__main__":
    main()