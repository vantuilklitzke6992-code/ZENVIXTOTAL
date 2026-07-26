# Script para remover espaços em branco desnecessários
with open("app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Remove espaços em branco do final de cada linha
lines = [line.rstrip() + '\n' if line.strip() else '\n' for line in lines]

# Remove linhas em branco no final do arquivo
while lines and lines[-1].strip() == '':
    lines.pop()

# Adiciona uma única quebra de linha no final
if lines:
    lines.append('\n')

with open("app.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Arquivo limpo com sucesso!")
