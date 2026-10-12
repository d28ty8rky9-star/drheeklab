# Pendência resolvida na versão 2.9.1

O ZIP do usuário foi recebido, a marca e os ícones incorporados, e o novo instalador passou pela validação Windows com 255 testes. Veja docs/ajustes-marca-2.9.1.md. As notas abaixo são históricas.

# Ajustes posteriores à versão 2.9.0

Implementados localmente: Início somente com dashboard e atalhos; remoção do alerta amarelo e informações inferiores dessa tela; aba Configurações → Sobre com informações do programa, histórico e anotações preservadas; remoção de fase/rodapé; logotipo na barra lateral acima do nome; ícone de janela/aplicativo e identificação de tarefa Windows; empacotamento de assets e ícone obrigatório no build Windows.

Validação local: 254 testes aprovados, zero falhas, em 61,25 s. Capturas em dist/revisao-sobre/inicio.png e sobre.png. A revisão não foi enviada ao GitHub nem compilada no Windows: o arquivo original do logotipo ainda não está disponível no filesystem. A imagem exibida no chat não pôde ser acessada por um identificador de arquivo. Não redesenhar nem substituir a marca.

Próximo passo: receber um ZIP contendo o PNG/JPG oficial, extrair a imagem original e executar `.venv/bin/python tools/prepare_branding.py /caminho/logo.png`. Isso salva o PNG e ICO multirresolução em src/drheeklab/assets. Confirmar que o conteúdo corresponde à imagem do usuário. Então atualizar versão/metadata e caminho do Setup no workflow, testar os fluxos afetados, gerar novas capturas, enviar as alterações autorizadas e validar o novo instalador Windows. O instalador 2.9.0 anterior ainda não contém esta revisão.

Posicionamento confirmado pelo usuário: logotipo no canto superior esquerdo da barra lateral, nome Dr. Heek Lab 2.0 e versão atual imediatamente abaixo. Implementado label de versão que acompanha __version__ e é ocultado somente ao recolher a barra lateral.

Pedido final: substituir os oito ícones da barra lateral pelos ícones da folha enviada (casa, carrinho, produção, cubo, caixas, financeiro, impressora e engrenagem). Loader src/drheeklab/menu_icons.py usa regiões do arquivo original sem redesenho, excluindo legendas; mantém nomes, tooltips, acessibilidade e navegação recolhida. Aguardar ZIP com essa folha e o logo; copiar a folha original para src/drheeklab/assets/menu-referencia.png (ou .jpg/.jpeg). Não gerar imagens substitutas. Verificar a correspondência e enquadramento com o arquivo recebido antes do empacotamento.
