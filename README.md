# Receba – Sistema de Gerenciamento de Encomendas

Este projeto é um sistema simples de gerenciamento de encomendas desenvolvido em Python usando o micro‑framework **Flask** e um banco de dados SQLite local. O objetivo do sistema é auxiliar porteiros de condomínios a registrar e controlar encomendas destinadas aos moradores.

## Funcionalidades

* **Login de Porteiro** – apenas porteiros cadastrados conseguem acessar o sistema. Um usuário padrão (`admin`/`admin`) é criado automaticamente na primeira execução.
* **Dashboard** – após o login, o porteiro visualiza uma lista de encomendas pendentes de retirada, com dados resumidos como ID, código do armário/pacote, empresa e data do registro.
* **Registrar Encomenda** – tela para cadastrar novas encomendas informando código do armário/pacote, empresa de entrega, nome do entregador, morador e seu WhatsApp (opcional). Cada encomenda recebe um identificador único (UUID) e tem um QR Code gerado automaticamente apontando para a página de confirmação de retirada.
  * A empresa de entrega pode ser escolhida em uma lista com transportadoras mais comuns (Correios, Mercado Livre, Amazon, Shopee) ou, ao selecionar **Outro**, digitar manualmente.
  * Para selecionar o morador associado à encomenda você pode pesquisá‑lo por **nome** ou por **bloco/torre** e **apartamento**. Se a busca retornar apenas um morador ele é pré‑selecionado; se houver mais de um, o sistema exibe uma lista para escolha. Também há um link de **Lista de Moradores** no menu que mostra todos os moradores cadastrados — basta clicar no morador desejado para abrir a tela de registro de encomenda com seus dados já preenchidos.
  * Se o morador tiver um número de WhatsApp cadastrado, o sistema disponibiliza um link para enviar uma mensagem via `wa.me` contendo o ID da encomenda ao morador.
* **Registrar Retirada** – permite procurar uma encomenda pelo ID (os primeiros 8 caracteres do UUID) para registrar a retirada. O porteiro pode:
  * Informar manualmente o nome do morador e concluir a retirada;
  * Ou utilizar o QR Code previamente gerado: basta o morador escanear o código e o status é atualizado automaticamente.
* **Histórico** – lista completa de todas as encomendas, com dados de registro e retirada. Agora o histórico exibe tanto o porteiro que **recebeu** a encomenda quanto o porteiro que **registrou a retirada**, além do nome do morador e as datas correspondentes.
* **Cadastro de Moradores** – tela dedicada para registrar moradores informando nome, torre/bloco, apartamento e telefone (WhatsApp). Essas informações são utilizadas posteriormente na associação de encomendas e na geração de links para mensagem.
* **Cadastro de Porteiros** – permite criar novos usuários porteiros (nome, usuário e senha). Útil para que mais de um porteiro possa utilizar o sistema.

* **Lista de Moradores** – página que exibe todos os moradores cadastrados no sistema. Além de consultar rapidamente torre/apartamento e telefone, essa lista possui um botão de atalho para a tela de registro de encomendas já com o morador selecionado.

## Estrutura do Projeto

```
receba/
├── app.py              # Aplicação Flask com as rotas e lógica de negócio
├── models.py           # Definição dos modelos (Porteiro, Morador, Encomenda) e instância do banco (SQLAlchemy)
├── controllers.py      # Métodos que acessam o banco de dados com querys SQL.
├── routes.py           # Endpoints que apontam para os métodos do Controllers.
├── templates/          # Páginas HTML com Jinja2 (base, login, dashboard, registrar, retirar, histórico)
├── static/
│   └── qrcodes/        # Imagens de QR Code geradas automaticamente
└── README.md           # Este documento
```

## Pré‑requisitos

Para executar a aplicação, você precisa ter o Python 3 instalado. Além disso, instale as dependências necessárias com o `pip`:

```bash
pip install flask flask_sqlalchemy qrcode pillow
```

O pacote `qrcode` utiliza o Pillow para gerar imagens PNG dos códigos QR.

## Como Executar

1. Faça o download ou clone este repositório.
2. Instale as dependências conforme mostrado acima.
3. No terminal, navegue até o diretório `receba` e execute o aplicativo:

   ```bash
   export FLASK_APP=app.py
   flask run
   ```

   Por padrão, o Flask inicia em `http://127.0.0.1:5000/`. Acesse esta URL no seu navegador.

4. Faça login com o usuário padrão:
   * **Usuário:** `admin`
   * **Senha:** `admin`

   Após o login, utilize o menu lateral para registrar encomendas, registrar retiradas e visualizar o histórico.

## Observações

* O sistema utiliza uma base SQLite (`receba.db`) criada automaticamente no primeiro acesso.
* O QR Code gerado para cada encomenda contém a URL de confirmação de retirada. Ao escanear esse código (por exemplo, com a câmera do celular), o morador será direcionado para a página que marca a encomenda como retirada.
* Para um ambiente de produção, recomenda‑se alterar a `SECRET_KEY` em `app.py` e criar usuários porteiros pelo banco de dados ou via um painel de administração.

## Licença

Este projeto é fornecido sem garantia de funcionamento em produção. Sinta‑se livre para modificá‑lo e adaptá‑lo conforme as necessidades do seu condomínio.