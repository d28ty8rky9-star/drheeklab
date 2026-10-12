# Dr. Heek Lab 2.9.1 — ajustes finais de identidade

O ZIP fornecido pelo usuário contém o logotipo oficial PNG 1254 × 1254 e a folha JPEG dos oito ícones. O PNG empacotado preserva todos os pixels do original. A folha de ícones foi copiada sem alterar seus bytes; a interface exibe as regiões correspondentes, sem as legendas da folha. O ICO contém tamanhos 16, 24, 32, 48, 64, 128 e 256 pixels.

- Logotipo no canto superior esquerdo, com nome e versão abaixo.
- Ícones correspondentes às oito áreas, mantendo nomes, acessibilidade e navegação.
- Menu recolhível e com rolagem para janelas menores.
- Início somente com dashboard e atalhos; alerta amarelo e informações inferiores retirados dessa tela.
- Configurações → Sobre reúne informações, histórico e anotações; rascunhos antigos preservados.
- Executável principal e instalador usam o ICO oficial. O ícone também é aplicado à janela/aplicativo.
- Nenhuma fórmula, regra de negócio ou migração foi alterada.

Validação local: 255 testes aprovados, zero falhas/erros/pulos, em 66,52 s. Inclui verificação dos oito ícones carregados, logo, versão, navegação e acesso ao menu em 780 × 560. Capturas reais usando um ambiente temporário de TESTES vazio:

![Início](capturas-2.9.1/inicio.png)
![Sobre](capturas-2.9.1/sobre.png)
![Menu recolhido](capturas-2.9.1/menu-recolhido.png)

Para repetir: `QT_QPA_PLATFORM=offscreen .venv/bin/python tools/capture_branding.py`.

## Entrega Windows aprovada

255 testes passaram no Windows, sem falhas, erros ou pulos. Executável empacotado e instalador aprovados; instalação, reinstalação, backup antes da atualização, preservação do banco/arquivos, backup sem interface, tarefa agendada e desinstalação aprovados. Após o download, hashes de Setup/GUI/helper e dos três assets empacotados conferidos. Os sete frames do ICO oficial foram encontrados tanto no executável principal quanto no instalador.

- Build: https://github.com/d28ty8rky9-star/drheeklab/actions/runs/38319542522 .
- Código compilado: `09423e0ea372a16911a2c766348d688b9ec08dfc`.
- Pacote: https://github.com/d28ty8rky9-star/drheeklab/actions/runs/38319542522/artifacts/11779025415 .
- Extraia o ZIP e execute `installer/DrHeekLab-2.9.1-Fase8-Setup.exe`.
- Cópia local: `dist/windows-2.9.1/installer/DrHeekLab-2.9.1-Fase8-Setup.exe`.

A validação é automatizada em runner Windows; avaliação prática no computador do proprietário permanece pendente. Nenhum dado real do usuário foi usado nas capturas/testes.
