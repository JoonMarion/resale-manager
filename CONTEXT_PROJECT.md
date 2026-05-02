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

---

## 🛠️ Stack tecnológica

| Camada | Tecnologia |
|--------|-----------|
| Backend | Django 5.x |
| Frontend | Django Templates + HTMX + Tailwind CSS (CDN) |
| Banco de dados | PostgreSQL |
| Servidor de aplicação | Gunicorn |
| Proxy reverso | Nginx |
| Infraestrutura | VPS Ubuntu 22.04 (1GB RAM) |
| Autenticação | Django Auth nativo (sessão) |
| Gráficos | Chart.js (CDN) |
| Formulários | django-widget-tweaks |
| Variáveis de ambiente | python-decouple |

**Não utilizar:** Django REST Framework, React, Vue, Node.js, Docker ou qualquer outra tecnologia fora dessa lista, a menos que seja explicitamente solicitado.

---

## 📁 Apps structure

```
resale_manager/        ← Django project
├── users/              ← authentication and profile
├── products/           ← product catalog
├── customers/          ← customer catalog
├── sales/              ← sales and sale items
├── stock/              ← stock control and entries
└── dashboard/          ← monthly financial view
```

---

## � Descrição das telas (conforme UI implementada)

### Início (Dashboard)
- Header: título "Início" + ícone de logout no canto superior direito
- Filtro de período: botões pill **"Este mês"** (padrão, verde) / **"Tudo"** (branco)
- 4 cards de métricas em grid 2×2:
  - **Faturado** (ícone estrela, fundo verde claro) — total faturado no período
  - **Recebido** (ícone carteira, fundo verde claro) — vendas pagas
  - **A receber** (ícone ampulheta, fundo amarelo claro) — vendas em aberto
  - **Custo** (ícone caixa, fundo vermelho claro) — custo das vendas pagas
- Banner verde escuro: **"Lucro líquido (sobre vendas pagas)"** com valor em destaque
- Gráfico de barras: **"Recebido vs A receber (6 meses)"** — duas séries, verde e amarelo

### Vendas
- Barra de busca: "Buscar por cliente..."
- Filtro por status (tabs pill): **Todas** / **Em aberto** / **Pagas**
- Cards de venda: nome do cliente, data · método de pagamento, valor total, badge de status
  - Badge **Pago**: fundo verde claro, texto verde
  - Badge **Aguardando**: fundo amarelo claro, ícone de relógio, texto amarelo escuro
- FAB verde no canto inferior direito: **"+ Nova venda"**
- **Paginação** no rodapé da lista

### Clientes
- Barra de busca: "Buscar cliente..."
- Cards de cliente: nome em negrito, telefone (ícone de telefone), endereço (quando preenchido)
- Ícone de lixeira vermelho para excluir (por card)
- FAB verde: **"+ Novo cliente"**
- **Paginação** no rodapé da lista

### Produtos
- Barra de busca: "Buscar produto..."
- Cards de produto: nome, categoria, badge **BAIXO** (vermelho) quando estoque baixo
  - Linha de preços: `Custo R$ X,XX` · `Venda R$ X,XX` · `Lucro R$ X,XX` (lucro em verde)
  - `Estoque: N` (vermelho quando baixo)
- Ícone de lixeira vermelho para excluir (por card)
- FAB verde: **"+ Novo produto"**
- **Paginação** no rodapé da lista

### Estoque
- Banner de alerta (fundo vermelho claro): "N produtos com estoque baixo" + link "Ver apenas baixos"
  - Banner visível apenas quando há produtos com estoque baixo
- Barra de busca: "Buscar produto..."
- Cards de estoque: nome, categoria, badge **BAIXO** quando aplicável, `Mínimo: N`
  - Quantidade exibida à direita: número em **vermelho** se baixo, preto se normal, + `UNID.`
  - Botão `+` (círculo verde) para registrar entrada de estoque
- **Paginação** no rodapé da lista

---

## �🗄️ Main models (code and internal names in English; user-facing texts in Portuguese)

### Product
```python
name: CharField
category: CharField (optional)
cost_price: DecimalField
resale_price: DecimalField
created_at: DateTimeField (auto)
```

### Customer
```python
full_name: CharField
phone: CharField
address: TextField (optional)
notes: TextField (optional)
created_at: DateTimeField (auto)
```

### Stock
```python
product: OneToOneField(Product)
quantity: PositiveIntegerField
minimum_stock: PositiveIntegerField
updated_at: DateTimeField (auto)
```

### StockEntry
```python
product: ForeignKey(Product)
quantity: PositiveIntegerField
date: DateField
note: TextField (optional)
```

### Sale
```python
customer: ForeignKey(Customer)
date: DateField
payment_method: CharField (choices: pix, dinheiro, cartao)
paid: BooleanField (default=False)
created_at: DateTimeField (auto)
```

### SaleItem
```python
sale: ForeignKey(Sale)
product: ForeignKey(Product)
quantity: PositiveIntegerField
unit_cost_price: DecimalField
unit_sale_price: DecimalField
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
- **Paginação obrigatória em todas as listas** — o sistema roda no navegador mobile e listas longas degradam a experiência; usar `Django Paginator` com navegação simples (anterior / próximo) no rodapé da lista, acima da bottom nav

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

### Templates — required structure
```
templates/
├── base.html               ← main layout with bottom nav and modal
├── login.html
├── dashboard/
│   └── index.html
├── products/
│   ├── list.html
│   ├── list_partial.html   ← HTMX fragment
   └── form.html           ← used inside modal
├── customers/
│   └── (same structure)
├── sales/
│   ├── list.html
│   ├── list_partial.html
│   ├── form.html
│   └── detail.html
└── stock/
    ├── list.html
    └── entry_form.html
```

---

## 🔐 Autenticação

- Login obrigatório em todas as views (`@login_required` ou `LoginRequiredMixin`)
- Usuário único (sem cadastro público — criar usuário via `createsuperuser`)
- Redirecionar para `/login/` se não autenticado
- Após login, redirecionar para `/dashboard/`

---

## 💰 Regras de negócio

1. Ao salvar um `SaleItem`, decrementar automaticamente o estoque via `signals.py`
2. `lucro_liquido` = soma de (unit_sale_price - unit_cost_price) × quantity dos itens de vendas com `paid=True`
3. `total_a_receber` = soma do valor total das vendas com `paid=False`
4. `faturado` = soma do valor total de todas as vendas (pagas + em aberto) no período
5. `recebido` = soma do valor total das vendas com `paid=True` no período
6. `custo` = soma do custo total das vendas pagas no período
7. Estoque baixo = `quantity <= minimum_stock`
8. Ao marcar uma venda como paga, atualizar apenas o campo `paid` sem recriar os itens
9. `unit_cost_price` e `unit_sale_price` em `SaleItem` devem ser **copiados no momento da venda** (snapshot — não referenciar o produto diretamente)
10. Métodos de pagamento aceitos: `pix`, `dinheiro`, `cartao`
11. Status de venda exibido como badge: **Pago** (verde) ou **Aguardando** (amarelo)
12. Dashboard possui filtro de período: **Este mês** (padrão) / **Tudo**
13. Dashboard exibe gráfico de barras "Recebido vs A receber" dos últimos 6 meses (Chart.js)
14. Na tela de Estoque, exibir banner de alerta quando houver produtos com estoque baixo, com link para filtrar apenas esses produtos
15. Na tela de Produtos, exibir badge **BAIXO** (vermelho) nos produtos com estoque baixo
16. **Todas as listas (Vendas, Clientes, Produtos, Estoque) devem ter paginação**

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

---

*This file is the base context for the project. Include it at the start of any new conversation to ensure consistency across development.*

---

## Base model example

All models should inherit common audit fields from a `BaseModel` (code-level English names). User-facing labels should still be provided in Portuguese via `verbose_name` / `verbose_name_plural` and form labels.

```python
from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Product(BaseModel):
    name = models.CharField(max_length=255, verbose_name='Nome')
    category = models.CharField(max_length=255, blank=True, verbose_name='Categoria')
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço de custo')
    resale_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço de revenda')

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'

    def __str__(self):
        return self.name
```