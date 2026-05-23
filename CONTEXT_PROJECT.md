# 📐 Project Context — resale_manager

You are working on a reseller control system named **resale_manager**.
Whenever you start a new conversation or receive a new prompt, consider this document the single source of truth for the project.

---

## 🎯 System Goal

Web system for an independent reseller to manage:
- Purchased and resold products
- Customers
- Sales (with payment tracking)
- Stock
- Monthly financial dashboard
- Optional public product catalog (feature-flagged)

---

## 🛠️ Stack tecnológica

| Camada | Tecnologia |
|--------|-----------|
| Backend | Django 5.2 |
| Frontend | Django Templates + HTMX (`django-htmx`) + Tailwind CSS (CDN) |
| Banco de dados | PostgreSQL (produção) / SQLite (dev via `dj-database-url`) |
| Servidor de aplicação | Gunicorn |
| Proxy reverso | Nginx |
| Infraestrutura | VPS Ubuntu 22.04 (1GB RAM) |
| Autenticação | Django Auth nativo (sessão) + `EmailOrUsernameBackend` customizado |
| Gráficos | Chart.js (CDN) |
| Formulários | `django-widget-tweaks` |
| Variáveis de ambiente | `python-decouple` + `dj-database-url` |
| Imagens | Pillow — redimensiona para 500×500 WebP ao salvar |
| Arquivos estáticos | Whitenoise (`CompressedManifestStaticFilesStorage`) |
| E-mail | Brevo SMTP (em produção) / console backend (em dev) |

**Não utilizar:** Django REST Framework, React, Vue, Node.js, Docker ou qualquer outra tecnologia fora dessa lista, a menos que seja explicitamente solicitado.

---

## 📁 Apps structure

```
resale_manager/        ← Django project
├── core/               ← BaseModel, SessionSortMixin, middleware, utils, context_processors
├── users/              ← authentication, UserProfile, password reset
├── products/           ← products with image, SKU, catalog flags
├── customers/          ← customer catalog
├── sales/              ← sales, sale items, receipt view
├── stock/              ← stock, manual entries and exits
├── dashboard/          ← financial dashboard (metrics + charts)
└── catalog/            ← public product catalog (feature-flagged via USE_CATALOG)
```

---

## 🖥️ Descrição das telas (conforme UI implementada)

### Início (Dashboard)
- Header: título "Início" + ícone de logout no canto superior direito
- Filtro de período: botões pill **"Este mês"** (`month`, padrão) / **"Este ano"** (`year`) / **"Tudo"** (`all`)
- 4 cards de métricas em grid 2×2:
  - **Faturado** — total faturado no período (todas as vendas)
  - **Recebido** — vendas com `is_paid=True`
  - **A receber** — vendas com `is_paid=False`
  - **Custo** — custo das vendas pagas (via `product.purchase_price`)
- Banner verde escuro: **"Lucro líquido (sobre vendas pagas)"** com valor em destaque
- Gráfico 1: **"Recebido vs A receber"** — série verde e amarela, buckets diários (mês) ou mensais (ano/tudo)
- Gráfico 2: **"Venda vs Compra"** — receita total vs custo total no período

### Vendas
- Barra de busca: "Buscar por cliente..."
- Filtro por status (tabs pill): **Todas** / **Em aberto** / **Pagas** — com contadores
- Cards de venda: nome do cliente, data · método de pagamento, valor total, badge de status
  - Badge **Pago**: fundo verde claro, texto verde
  - Badge **Aguardando**: fundo amarelo claro, ícone de relógio, texto amarelo escuro
- FAB verde no canto inferior direito: **"+ Nova venda"**
- Tela de detalhe com itens da venda e botão "Marcar como pago"
- Tela de edição de venda com formset inline de itens
- Comprovante público (`/vendas/<pk>/comprovante/`) — sem login, compartilhável com o cliente
- **Paginação** no rodapé da lista

### Clientes
- Barra de busca: "Buscar cliente..."
- Cards de cliente: nome em negrito, telefone (ícone de telefone), endereço (quando preenchido)
- Ícone de lixeira vermelho para excluir (soft-delete via `active=False`)
- FAB verde: **"+ Novo cliente"**
- Edição inline via modal HTMX
- **Paginação** no rodapé da lista

### Produtos
- Barra de busca: "Buscar produto..."
- Ordenação persistida por sessão (`SessionSortMixin`)
- Cards de produto: nome, categoria, SKU, badge **BAIXO** (vermelho) quando estoque baixo
  - Linha de preços: `Compra R$ X,XX` · `Venda R$ X,XX` · `Lucro R$ X,XX` (lucro em verde)
  - `Estoque: N` (vermelho quando baixo)
- Soft-delete: produtos com vendas vinculadas têm `active=False` em vez de exclusão física
- FAB verde: **"+ Novo produto"**
- **Paginação** no rodapé da lista

### Estoque
- Banner de alerta (fundo vermelho claro): "N produtos com estoque baixo" + link "Ver apenas baixos"
  - Banner visível apenas quando há produtos com estoque baixo
- Barra de busca: "Buscar produto..." + filtro `?low=1` para ver apenas baixos
- Cards de estoque: nome, categoria, badge **BAIXO** quando aplicável, `Mínimo: N`
  - Quantidade exibida à direita: número em **vermelho** se baixo, preto se normal, + `UNID.`
  - Botão `+` (entrada) e botão `-` (saída manual) para registrar movimentações
- **Paginação** no rodapé da lista

### Catálogo Público (`/catalogo/`) — opcional, ativado por `USE_CATALOG=True`
- Lista pública de produtos filtrados por `show_in_catalog=True`
- Hierarquia de categorias com navegação por breadcrumb
- Filtro por categoria, busca por nome, ordenação por nome/preço
- Carrinho de compras via sessão (`CART_SESSION_ID`)
- Checkout: cliente informa nome e telefone → gera `PedidoCatalogo`
- Resumo do pedido com link de confirmação via WhatsApp (`WHATSAPP_NUMBER`)
- Gerenciamento interno de categorias (`/catalogo/categories/`)

### Usuário / Perfil
- Login com username **ou** e-mail
- Recuperação de senha via e-mail (Brevo SMTP)
- Tela de perfil: foto, nome da loja, telefone da loja
- Alteração de senha in-app

---

## 🗄️ Main models (code and internal names in English; user-facing texts in Portuguese)

### BaseModel (`core/models.py`) — herdado por todos os modelos principais
```python
created_at: DateTimeField (auto_now_add)
updated_at: DateTimeField (auto_now)
active:     BooleanField (default=True)
```

### Product (`products/models.py`)
```python
name:             CharField(max_length=255)
category:         CharField(max_length=100, blank, null)   # texto livre
sku:              CharField(max_length=50, unique)          # gerado automaticamente se vazio
image:            ImageField(upload_to='products/', null)   # otimizada para 500×500 WebP
purchase_price:   DecimalField(10,2, default=0)
sale_price:       DecimalField(10,2, default=0)
min_stock:        IntegerField(default=5)                   # limiar de estoque baixo
description:      TextField(blank, null)
show_in_catalog:  BooleanField(default=False)               # exibir no catálogo público
catalog_category: ForeignKey('catalog.Category', null)     # categoria do catálogo
# (herda created_at, updated_at, active de BaseModel)

# Properties
profit          → sale_price - purchase_price
is_low_stock    → stock.quantity <= min_stock
```

### Customer (`customers/models.py`)
```python
name:     CharField(max_length=255)
email:    EmailField(unique, blank, null)
phone:    CharField(max_length=20, blank, null)
document: CharField(max_length=20, blank, null)  # CPF/CNPJ
address:  CharField(max_length=255, blank, null)
notes:    TextField(blank, null)
# (herda created_at, updated_at, active de BaseModel)
```

### Stock (`stock/models.py`)
```python
product:  OneToOneField(Product, related_name='stock')
quantity: IntegerField(default=0)
# (herda created_at, updated_at, active de BaseModel)
```

### StockEntry (`stock/models.py`)
```python
product:  ForeignKey(Product, related_name='entries')
quantity: IntegerField
notes:    TextField(blank, null)
# (herda created_at, updated_at, active de BaseModel)
```

### StockExit (`stock/models.py`)
```python
product:  ForeignKey(Product, related_name='exits')
quantity: IntegerField
notes:    TextField(blank, null)
# (herda created_at, updated_at, active de BaseModel)
```

### Sale (`sales/models.py`)
```python
customer:       ForeignKey(Customer, null, related_name='sales')
sale_date:      DateTimeField(auto_now_add)
payment_method: CharField choices: pix | cash | card | other
is_paid:        BooleanField(default=False)
installments:   PositiveSmallIntegerField(null, blank)
# (herda created_at, updated_at, active de BaseModel)

# Property
total_price → sum(item.total_price for item in items)
```

### SaleItem (`sales/models.py`)
```python
sale:            ForeignKey(Sale, related_name='items')
product:         ForeignKey(Product, related_name='sale_items', PROTECT)
quantity:        IntegerField
unit_sale_price: DecimalField(10,2)   # snapshot do preço no momento da venda
# (herda created_at, updated_at, active de BaseModel)

# Property
total_price → unit_sale_price × quantity
```

> **Nota:** `unit_cost_price` **não** é armazenado em `SaleItem`. O dashboard calcula o custo usando `product.purchase_price` dinamicamente via ORM expressions.

### UserProfile (`users/models.py`)
```python
user:        OneToOneField(User, related_name='profile')
photo:       ImageField(upload_to='profile_photos/', null)  # otimizada para WebP
store_name:  CharField(max_length=100, blank)
store_phone: CharField(max_length=30, blank)
```

### Category (`catalog/models.py`)
```python
name:   CharField(max_length=100, unique)
slug:   SlugField(auto-gerado)
parent: ForeignKey('self', null, related_name='subcategories')  # árvore N níveis
# Métodos: get_ancestors(), get_descendants(), get_full_name()
```

### PedidoCatalogo (`catalog/models.py`)
```python
id:               UUIDField (primary key)
numero_pedido:    CharField(unique, auto-gerado como #00001, #00002…)
cliente_nome:     CharField(blank, null)
cliente_telefone: CharField(blank, null)
total:            DecimalField(10,2)
status:           CharField choices: aguardando | confirmado | cancelado
criado_em:        DateTimeField(auto_now_add)
```

### ItemPedidoCatalogo (`catalog/models.py`)
```python
pedido:         ForeignKey(PedidoCatalogo, related_name='itens')
produto:        ForeignKey(Product, null, SET_NULL)
quantidade:     PositiveIntegerField
preco_unitario: DecimalField(10,2)
# Property: subtotal → quantidade × preco_unitario
```

---

## 🎨 Padrões de interface

> **Contexto de uso:** o sistema é acessado exclusivamente via **navegador de celular**. Toda decisão de UI deve priorizar usabilidade em telas pequenas com toque.

### Design
- **Mobile first** — o sistema é usado exclusivamente no **navegador de celular**
- Tailwind CSS via CDN for styling
- Bottom navigation bar fixa com 5 itens: Início, Vendas, Clientes, Produtos, Estoque
- **Never use HTML tables** — use cards e listas
- Botões grandes e espaçados (min `py-3 px-6`) para uso com o polegar
- Tipografia legível em telas pequenas (min `text-base`)
- **FAB (Floating Action Button)** no canto inferior direito para criar novos registros
- Ícone de logout (`→`) no canto superior direito do header
- **Paginação obrigatória em todas as listas** — `paginate_by = 10` via `Django Paginator`

### Paleta de cores
| Uso | Cor Tailwind |
|-----|-------------|
| Primária / ações / FAB / nav ativo | `green-600` |
| Lucro / recebido / status Pago | `green-500` (badge fundo `green-100`) |
| A receber / status Aguardando | `yellow-500` (badge fundo `yellow-100`) |
| Custo / perigo / alerta / estoque baixo badge | `red-500` |
| Fundo principal | `gray-50` |
| Cards | `white` com `shadow-sm` |
| Banner lucro líquido | fundo `green-600`, texto `white` |
| Banner alerta estoque baixo | fundo `red-50`, texto `red-600` |

### HTMX — required patterns
- Live search: `hx-trigger="keyup changed delay:300ms"` with `hx-target` pointing to the list
- Modals: `hx-target="#modal"` with `hx-swap="innerHTML"`
- Marcar como pago: `hx-post` retornando apenas o fragment do badge atualizado
- Paginação: links de página devem usar HTMX (`hx-get` + `hx-target`) para trocar apenas o bloco da lista sem reload completo
- Sempre verificar `request.htmx` na view — retornar fragment para HTMX, template completo caso contrário
- Feedback de sucesso/erro via `HX-Trigger` com eventos `showSuccess` / `showError`

### Ordenação persistida (`SessionSortMixin`)
- `core/mixins.py` contém `SessionSortMixin` que persiste a ordenação escolhida por view na sessão
- Opções padrão: `alpha_asc`, `alpha_desc`, `recent`, `oldest`
- Injetar `current_sort` no contexto para destacar a opção ativa

### Templates — required structure
```
templates/
├── base.html                    ← layout principal com bottom nav e modal
├── login.html
├── 404.html / 500.html / 503.html
├── dashboard/
│   └── index.html
├── products/
│   ├── list.html
│   ├── list_partial.html        ← HTMX fragment
│   └── form.html
├── customers/
│   ├── list.html
│   ├── list_partial.html
│   └── form.html
├── sales/
│   ├── list.html
│   ├── list_partial.html
│   ├── form.html
│   ├── edit_form.html
│   ├── detail.html
│   ├── receipt.html             ← comprovante público (sem login)
│   └── _badge.html              ← fragment HTMX do badge de status
├── stock/
│   ├── list.html
│   ├── list_partial.html
│   ├── entry_form.html
│   └── exit_form.html
├── users/
│   ├── profile.html
│   └── password_change.html
├── registration/                ← templates do fluxo de password reset
└── catalog/                     ← templates do catálogo público
```

---

## 🔐 Autenticação

- Login obrigatório em todas as views internas (`ProjectLoginRequiredMixin` de `users/mixins.py`)
- Login aceita **username ou e-mail** (`EmailOrUsernameBackend` em `users/backends.py`)
- Usuário único (sem cadastro público — criar usuário via `createsuperuser`)
- Redirecionar para `/login/` se não autenticado
- Após login, redirecionar para `/dashboard/`
- Recuperação de senha via e-mail (`/password_reset/`) com templates em `templates/registration/`

---

## 💰 Regras de negócio

1. Ao salvar um `SaleItem` (novo), decrementar automaticamente o estoque via `stock/signals.py`
2. Ao editar uma venda, reconciliar estoque: devolver quantidade antiga e debitar a nova
3. Ao excluir uma venda, devolver todos os itens ao estoque antes de deletar
4. `lucro_liquido` = soma de `(unit_sale_price − product.purchase_price) × quantity` dos itens de vendas com `is_paid=True`
5. `total_a_receber` = soma de `unit_sale_price × quantity` dos itens de vendas com `is_paid=False`
6. `faturado` = soma de `unit_sale_price × quantity` de todas as vendas no período
7. `recebido` = soma de `unit_sale_price × quantity` das vendas com `is_paid=True` no período
8. `custo` = soma de `product.purchase_price × quantity` das vendas pagas no período
9. Estoque baixo = `stock.quantity <= product.min_stock`
10. Ao marcar uma venda como paga, atualizar apenas o campo `is_paid` (via `update_fields=['is_paid']`)
11. `unit_sale_price` em `SaleItem` é **copiado no momento da venda** (snapshot); o custo é lido dinamicamente de `product.purchase_price`
12. Métodos de pagamento aceitos: `pix`, `cash`, `card`, `other`
13. Status de venda exibido como badge: **Pago** (verde) ou **Aguardando** (amarelo)
14. Dashboard possui filtro de período: **Este mês** (`month`, padrão) / **Este ano** (`year`) / **Tudo** (`all`)
15. Dashboard exibe dois gráficos (Chart.js): "Recebido vs A receber" e "Venda vs Compra", com buckets diários para `month` e mensais para `year`/`all`
16. Na tela de Estoque, exibir banner de alerta quando houver produtos com estoque baixo, com link `?low=1`
17. Na tela de Produtos, exibir badge **BAIXO** (vermelho) nos produtos com `is_low_stock=True`
18. Soft-delete em Produtos e Clientes: setar `active=False` em vez de excluir fisicamente quando há registros vinculados
19. Preços dos produtos são **bloqueados para edição** quando o produto já tem estoque (`stock.quantity > 0`)
20. SKU gerado automaticamente (8 chars UUID) se não informado
21. Imagens de produtos e fotos de perfil são automaticamente redimensionadas para 500×500 WebP via `core/utils.optimize_image()`
22. O catálogo público (`/catalogo/`) só fica ativo quando `USE_CATALOG=True` no `.env`; caso contrário, as rotas retornam 404
23. Comprovante de venda (`/vendas/<pk>/comprovante/`) é público — não exige login — para permitir compartilhamento com o cliente
24. `MaintenanceModeMiddleware`: quando `MAINTENANCE_MODE=True` no `.env`, retorna HTTP 503 para todas as rotas exceto `/admin/`

---

## 🚀 Deploy

- VPS Ubuntu 22.04 com 1GB de RAM
- Gunicorn como servidor WSGI (4 workers)
- Nginx como proxy reverso na porta 80/443
- SSL via Certbot (Let's Encrypt)
- Arquivos estáticos servidos pelo Whitenoise
- Banco PostgreSQL local na própria VPS
- Variáveis de ambiente via arquivo `.env` com python-decouple

### Variáveis de ambiente necessárias
```env
SECRET_KEY=
DEBUG=False
ALLOWED_HOSTS=
DATABASE_URL=
USE_CATALOG=False
WHATSAPP_NUMBER=
MAINTENANCE_MODE=False
EMAIL_BACKEND=
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=
```

---

## ✅ Boas práticas obrigatórias

- Always use CBV (Class Based Views) with mixins
- `forms.py` in each app with `ModelForm`
- `admin.py` configured in all apps
- No business logic in views — move to models or managers
- Variable names and comments in **English** (code-level)
- User-facing texts (labels, templates, forms) in **Portuguese (pt-BR)**
- Small, descriptive commits
- Never commit the `.env` file
- Use `ProjectLoginRequiredMixin` (from `users/mixins.py`) — not the plain Django `LoginRequiredMixin` — in all internal views
- Apply `SessionSortMixin` (from `core/mixins.py`) in all list views that support sorting

---

*This file is the base context for the project. Include it at the start of any new conversation to ensure consistency across development.*

---

## BaseModel (core/models.py)

All models should inherit from `BaseModel`:

```python
# core/models.py
from django.db import models

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    active = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        abstract = True
```

## URL prefixes

| App | Prefixo |
|-----|---------|
| users | `/` (login, logout) + `/perfil/` |
| dashboard | `/dashboard/` |
| products | `/produtos/` |
| customers | `/clientes/` |
| sales | `/vendas/` |
| stock | `/estoque/` |
| catalog | `/catalogo/` (apenas se `USE_CATALOG=True`) |