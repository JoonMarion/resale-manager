"""
Management command: seed_demo
Populates the database with realistic Brazilian demo data for pagination testing.

Usage:
    python manage.py seed_demo            # creates default amounts
    python manage.py seed_demo --customers 30 --products 25 --sales 50
    python manage.py seed_demo --clear    # wipe all demo data first
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from customers.models import Customer
from products.models import Product
from sales.models import Sale, SaleItem
from stock.models import Stock


# ──────────────────────────────────────────────────────────────────────────────
# Realistic data pools
# ──────────────────────────────────────────────────────────────────────────────

PRIMEIROS_NOMES = [
    "Ana", "Beatriz", "Camila", "Daniela", "Eduarda", "Fernanda", "Gabriela",
    "Helena", "Isabela", "Juliana", "Karen", "Larissa", "Mariana", "Natália",
    "Olivia", "Patrícia", "Renata", "Sabrina", "Tânia", "Vanessa",
    "Carlos", "Diego", "Eduardo", "Felipe", "Gustavo", "Henrique", "Igor",
    "João", "Lucas", "Marcos", "Nicolas", "Pedro", "Rafael", "Samuel",
    "Thiago", "Vinícius", "Wesley", "Yago", "Zeca", "André",
]

SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira",
    "Alves", "Pereira", "Lima", "Gomes", "Costa", "Ribeiro", "Martins",
    "Carvalho", "Almeida", "Lopes", "Soares", "Fernandes", "Vieira", "Barbosa",
]

BAIRROS = [
    "Centro", "Jardim América", "Vila Nova", "Santa Cruz", "Boa Vista",
    "Parque Industrial", "Residencial das Flores", "Alto da Serra",
    "São Luís", "Bela Vista",
]

CIDADES = ["São Paulo", "Campinas", "Sorocaba", "Jundiaí", "Ribeirão Preto"]

PRODUTOS_VARIEDADES = [
    ("Chinelo Havaianas Slim",          "calçados",    Decimal("12.00"), Decimal("29.90")),
    ("Chinelo Havaianas Top",           "calçados",    Decimal("11.00"), Decimal("27.50")),
    ("Sandália Rasteira Feminina",      "calçados",    Decimal("15.00"), Decimal("39.90")),
    ("Tênis Infantil Colorido",         "calçados",    Decimal("25.00"), Decimal("59.90")),
    ("Camiseta Básica Feminina P",      "vestuário",   Decimal("14.00"), Decimal("34.90")),
    ("Camiseta Básica Feminina M",      "vestuário",   Decimal("14.00"), Decimal("34.90")),
    ("Camiseta Básica Masculina G",     "vestuário",   Decimal("14.00"), Decimal("34.90")),
    ("Bermuda Jeans Masculina 40",      "vestuário",   Decimal("28.00"), Decimal("69.90")),
    ("Legging Suplex Feminina",         "vestuário",   Decimal("18.00"), Decimal("45.00")),
    ("Vestido Floral Verão",            "vestuário",   Decimal("32.00"), Decimal("79.90")),
    ("Blusa Cropped Listrada",          "vestuário",   Decimal("20.00"), Decimal("49.90")),
    ("Short Jeans Feminino",            "vestuário",   Decimal("22.00"), Decimal("54.90")),
    ("Meia Antiderrapante Infantil",    "acessórios",  Decimal("4.00"),  Decimal("9.90")),
    ("Kit 3 Meias Masculinas",          "acessórios",  Decimal("8.00"),  Decimal("18.90")),
    ("Cinto de Couro Sintético",        "acessórios",  Decimal("10.00"), Decimal("24.90")),
    ("Bolsa Transversal Feminina",      "bolsas",      Decimal("35.00"), Decimal("89.90")),
    ("Mochila Infantil Estampada",      "bolsas",      Decimal("28.00"), Decimal("69.90")),
    ("Necessaire Estampada",            "bolsas",      Decimal("12.00"), Decimal("29.90")),
    ("Óculos de Sol Redondo",           "acessórios",  Decimal("18.00"), Decimal("44.90")),
    ("Lenço Estampado Feminino",        "acessórios",  Decimal("6.00"),  Decimal("14.90")),
    ("Brinco Argola Dourado",           "bijuterias",  Decimal("5.00"),  Decimal("12.90")),
    ("Colar Pérola Sintética",          "bijuterias",  Decimal("7.00"),  Decimal("17.90")),
    ("Pulseira Elástica Colorida",      "bijuterias",  Decimal("3.50"),  Decimal("8.90")),
    ("Toalha de Rosto Felpuda",         "casa",        Decimal("9.00"),  Decimal("22.90")),
    ("Jogo de Cama Solteiro",           "casa",        Decimal("42.00"), Decimal("99.90")),
]

METODOS_PAGAMENTO = ["pix", "cash", "card", "other"]


# ──────────────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Popula o banco com dados fictícios realistas para testar paginação."

    def add_arguments(self, parser):
        parser.add_argument("--customers", type=int, default=30,
                            help="Quantidade de clientes a criar (padrão: 30)")
        parser.add_argument("--products",  type=int, default=25,
                            help="Quantidade de produtos a criar (padrão: 25)")
        parser.add_argument("--sales",     type=int, default=50,
                            help="Quantidade de vendas a criar (padrão: 50)")
        parser.add_argument("--clear", action="store_true",
                            help="Remove todos os dados existentes antes de criar")

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write(self.style.WARNING("🗑  Removendo dados existentes..."))
            SaleItem.objects.all().delete()
            Sale.objects.all().delete()
            Stock.objects.all().delete()
            Product.objects.all().delete()
            Customer.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("   Dados removidos.\n"))

        # ── Clientes ─────────────────────────────────────────────────────────
        self.stdout.write("👤  Criando clientes...")
        clientes_criados = []
        nomes_usados = set()

        for i in range(options["customers"]):
            while True:
                nome = f"{random.choice(PRIMEIROS_NOMES)} {random.choice(SOBRENOMES)}"
                if nome not in nomes_usados:
                    nomes_usados.add(nome)
                    break

            slug = nome.lower().replace(" ", ".").replace("ã", "a").replace("é", "e") \
                               .replace("ê", "e").replace("á", "a").replace("í", "i") \
                               .replace("ó", "o").replace("ô", "o").replace("ú", "u") \
                               .replace("ç", "c").replace("â", "a")
            numero = random.randint(10, 99)
            bairro = random.choice(BAIRROS)
            cidade = random.choice(CIDADES)

            c = Customer.objects.create(
                name=nome,
                phone=f"({random.randint(11,99)}) 9{random.randint(1000,9999)}-{random.randint(1000,9999)}",
                email=f"{slug}{numero}@email.com",
                address=f"Rua das {bairro.split()[0]}s, {random.randint(1,999)} — {bairro}, {cidade}",
                notes=random.choice([
                    "Cliente frequente.",
                    "Prefere pagamento via Pix.",
                    "Gosta de novidades em vestuário.",
                    "Compra para revender.",
                    "",
                ]),
            )
            clientes_criados.append(c)

        self.stdout.write(self.style.SUCCESS(f"   {len(clientes_criados)} clientes criados.\n"))

        # ── Produtos + Estoque ────────────────────────────────────────────────
        self.stdout.write("📦  Criando produtos e estoque...")
        produtos_criados = []
        pool = list(PRODUTOS_VARIEDADES)
        random.shuffle(pool)
        qtd_produtos = min(options["products"], len(pool))

        for nome, categoria, preco_compra, preco_venda in pool[:qtd_produtos]:
            p = Product.objects.create(
                name=nome,
                category=categoria,
                purchase_price=preco_compra,
                sale_price=preco_venda,
                min_stock=random.randint(3, 10),
                description=f"Produto da categoria {categoria}. Alta qualidade.",
            )
            estoque_inicial = random.randint(10, 100)
            Stock.objects.create(product=p, quantity=estoque_inicial)
            produtos_criados.append(p)

        self.stdout.write(self.style.SUCCESS(f"   {len(produtos_criados)} produtos criados com estoque.\n"))

        # ── Vendas ────────────────────────────────────────────────────────────
        self.stdout.write("🛒  Criando vendas...")
        agora = timezone.now()
        vendas_criadas = 0

        for i in range(options["sales"]):
            # Distribui as vendas nos últimos 6 meses
            dias_atras = random.randint(0, 180)
            data_venda = agora - timedelta(days=dias_atras)

            cliente = random.choice(clientes_criados) if random.random() > 0.1 else None
            is_paid = random.random() > 0.35

            venda = Sale.objects.create(
                customer=cliente,
                payment_method=random.choice(METODOS_PAGAMENTO),
                is_paid=is_paid,
            )
            # Ajusta a data manualmente após criação (auto_now_add não aceita override direto)
            Sale.objects.filter(pk=venda.pk).update(sale_date=data_venda)

            # Adiciona entre 1 e 4 itens por venda
            qtd_itens = random.randint(1, 4)
            produtos_da_venda = random.sample(produtos_criados, min(qtd_itens, len(produtos_criados)))

            for produto in produtos_da_venda:
                quantidade = random.randint(1, 5)
                SaleItem.objects.create(
                    sale=venda,
                    product=produto,
                    quantity=quantidade,
                    unit_sale_price=produto.sale_price,
                )

            vendas_criadas += 1

        self.stdout.write(self.style.SUCCESS(f"   {vendas_criadas} vendas criadas.\n"))

        self.stdout.write(self.style.SUCCESS(
            "✅  Seed concluído!\n"
            f"   Clientes : {len(clientes_criados)}\n"
            f"   Produtos : {len(produtos_criados)}\n"
            f"   Vendas   : {vendas_criadas}"
        ))
