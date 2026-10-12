# Ajustes posteriores à versão 2.9.0

Implementados localmente: Início somente com dashboard e atalhos; remoção do alerta amarelo e informações inferiores dessa tela; aba Configurações → Sobre com informações do programa, histórico e anotações preservadas; remoção de fase/rodapé; logotipo na barra lateral acima do nome; ícone de janela/aplicativo e identificação de tarefa Windows; empacotamento de assets e ícone obrigatório no build Windows.

Validação local: 254 testes aprovados, zero falhas, em 61,25 s. Capturas em dist/revisao-sobre/inicio.png e sobre.png. A revisão não foi enviada ao GitHub nem compilada no Windows: o arquivo original do logotipo ainda não está disponível no filesystem. A imagem exibida no chat não pôde ser acessada por um identificador de arquivo. Não redesenhar nem substituir a marca.

Próximo passo: receber um ZIP contendo o PNG/JPG oficial, extrair a imagem original e executar `.venv/bin/python tools/prepare_branding.py /caminho/logo.png`. Isso salva o PNG e ICO multirresolução em src/drheeklab/assets. Confirmar que o conteúdo corresponde à imagem do usuário. Então atualizar versão/metadata e caminho do Setup no workflow, testar os fluxos afetados, gerar novas capturas, enviar as alterações autorizadas e validar o novo instalador Windows. O instalador 2.9.0 anterior ainda não contém esta revisão.
