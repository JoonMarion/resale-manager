# resale_manager

Sistema web para gestão de revenda, pensado para acompanhar a rotina de uma revendedora de forma simples, rápida e prática. A ideia do projeto é centralizar o que normalmente fica espalhado entre caderno, bloco de notas e conversas no WhatsApp: produtos, clientes, vendas, estoque e visão financeira do mês.

Hoje a interface foi desenhada com foco total em celular. Isso não foi uma limitação técnica aleatória: foi uma decisão tomada por solicitação da cliente, porque o uso real do sistema acontece no navegador do smartphone durante o dia a dia. Por isso, toda a experiência atual prioriza telas pequenas, toque, navegação simples e agilidade no cadastro.

## Sobre o projeto

O `resale_manager` foi construído para atender um cenário real de revenda, em que a pessoa precisa registrar entradas de estoque, acompanhar o que vendeu, saber o que já recebeu, o que ainda falta receber e visualizar rapidamente se o negócio está saudável.

Mais do que um CRUD genérico, a proposta aqui foi transformar a operação da revenda em um fluxo mais organizado, com informação acessível e uma interface objetiva para uso móvel.

## Funcionalidades principais

- Autenticação de usuários com login obrigatório.
- Dashboard financeiro com visão de faturado, recebido, a receber, custo e lucro líquido.
- Gráfico com comparação entre recebido e a receber nos últimos meses.
- Cadastro e edição de clientes.
- Cadastro e edição de produtos com custo, preço de revenda e categoria.
- Controle de estoque com quantidade atual e estoque mínimo.
- Alerta visual para produtos com estoque baixo.
- Registro de entradas de estoque.
- Cadastro de vendas com cliente, itens, forma de pagamento e status.
- Acompanhamento de vendas pagas e em aberto.
- Paginação e busca nas listagens para melhorar a navegação no mobile.
- Recuperação e redefinição de senha por e-mail.

## Stack utilizada

- Django 5
- Django Templates
- HTMX
- Tailwind CSS
- Chart.js
- PostgreSQL em produção
- SQLite em desenvolvimento (configuração padrão local)
- Gunicorn + Nginx no deploy
- Whitenoise para arquivos estáticos

## Observação importante sobre a interface

No momento, o projeto está otimizado para uso mobile por solicitação da cliente. Isso significa que o layout, a navegação e os componentes foram pensados primeiro para o navegador do celular.

Ele pode até abrir em telas maiores, mas a experiência principal que guiou o desenvolvimento foi a versão mobile. Se em algum momento houver necessidade, a adaptação para uma experiência desktop mais refinada pode ser feita em uma próxima etapa.

## Como rodar o projeto localmente

### Pré-requisitos

- Python 3.10 ou superior
- Git
- Ambiente virtual Python

### 1. Clonar o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd resale_manager
```

### 2. Criar e ativar o ambiente virtual

No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

No Linux ou macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Criar o arquivo `.env`

Crie um arquivo `.env` na raiz do projeto com algo como:

```env
SECRET_KEY=sua-chave-django-aqui
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=webmaster@localhost
```

Para desenvolvimento local, o projeto já funciona com SQLite usando o `DATABASE_URL` acima. Em produção, a aplicação foi preparada para usar PostgreSQL via variável de ambiente.

### 5. Aplicar as migrations

```bash
python manage.py migrate
```

### 6. Criar um usuário administrador

```bash
python manage.py createsuperuser
```

### 7. Iniciar o servidor

```bash
python manage.py runserver
```

Depois disso, acesse:

- `http://127.0.0.1:8000/login/`
- `http://127.0.0.1:8000/admin/`

## Estrutura do projeto

O projeto está organizado em apps Django separados por responsabilidade:

- `users`: autenticação, login, perfil e senha.
- `products`: catálogo de produtos.
- `customers`: cadastro de clientes.
- `sales`: vendas, itens da venda e status de pagamento.
- `stock`: controle e movimentação de estoque.
- `dashboard`: visão consolidada dos números do negócio.
- `core`: componentes compartilhados e infraestrutura da aplicação.

## Ambiente de produção

Em produção, a aplicação foi preparada para rodar com:

- Gunicorn como servidor WSGI
- Nginx como proxy reverso
- PostgreSQL como banco de dados
- Whitenoise para arquivos estáticos
- Variáveis de ambiente com `python-decouple`
