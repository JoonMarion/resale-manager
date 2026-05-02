import json
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncMonth, TruncDay
from django.utils import timezone
from django.views.generic import TemplateView

from sales.models import SaleItem
from users.mixins import ProjectLoginRequiredMixin


def _brl(val):
    """Format Decimal as R$ X.XXX,XX."""
    f = f"{float(val):,.2f}"
    return "R$ " + f.replace(",", "\u00a7").replace(".", ",").replace("\u00a7", ".")


MONTHS_PT = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']


class DashboardView(ProjectLoginRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        period = self.request.GET.get('period', 'month')
        if period not in ('month', 'year', 'all'):
            period = 'month'
        ctx['period'] = period

        rev_expr = ExpressionWrapper(
            F('unit_sale_price') * F('quantity'),
            output_field=DecimalField(max_digits=14, decimal_places=2)
        )
        cost_expr = ExpressionWrapper(
            F('product__purchase_price') * F('quantity'),
            output_field=DecimalField(max_digits=14, decimal_places=2)
        )
        profit_expr = ExpressionWrapper(
            (F('unit_sale_price') - F('product__purchase_price')) * F('quantity'),
            output_field=DecimalField(max_digits=14, decimal_places=2)
        )

        now = timezone.now()

        # ── Base queryset (metrics) ──────────────────────────────────────────
        if period == 'month':
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            base_qs = SaleItem.objects.filter(sale__sale_date__gte=start)
        elif period == 'year':
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            base_qs = SaleItem.objects.filter(sale__sale_date__gte=start)
        else:
            base_qs = SaleItem.objects.all()

        faturado      = base_qs.aggregate(v=Sum(rev_expr))['v'] or Decimal('0')
        recebido      = base_qs.filter(sale__is_paid=True).aggregate(v=Sum(rev_expr))['v'] or Decimal('0')
        a_receber     = base_qs.filter(sale__is_paid=False).aggregate(v=Sum(rev_expr))['v'] or Decimal('0')
        custo         = base_qs.filter(sale__is_paid=True).aggregate(v=Sum(cost_expr))['v'] or Decimal('0')
        lucro_liquido = base_qs.filter(sale__is_paid=True).aggregate(v=Sum(profit_expr))['v'] or Decimal('0')

        ctx.update({
            'faturado_fmt':      _brl(faturado),
            'recebido_fmt':      _brl(recebido),
            'a_receber_fmt':     _brl(a_receber),
            'custo_fmt':         _brl(custo),
            'lucro_liquido_fmt': _brl(lucro_liquido),
            'lucro_positivo':    lucro_liquido >= 0,
        })

        # ── Chart data (follow period filter) ───────────────────────────────
        if period == 'month':
            # Daily buckets for current month up to today
            today = now.date()
            first = today.replace(day=1)
            buckets = [first + timedelta(days=i) for i in range((today - first).days + 1)]
            labels = [d.strftime('%d/%m') for d in buckets]

            def _by_day(qs, expr):
                return {
                    row['day'].date(): float(row['total'] or 0)
                    for row in (
                        qs.annotate(day=TruncDay('sale__sale_date'))
                          .values('day')
                          .annotate(total=Sum(expr))
                          .order_by('day')
                    )
                }

            paid_rev   = _by_day(base_qs.filter(sale__is_paid=True), rev_expr)
            pend_rev   = _by_day(base_qs.filter(sale__is_paid=False), rev_expr)
            all_rev    = _by_day(base_qs, rev_expr)
            all_cost   = _by_day(base_qs, cost_expr)

            ctx['chart_data_json']  = json.dumps({'labels': labels, 'recebido': [paid_rev.get(d, 0) for d in buckets], 'a_receber': [pend_rev.get(d, 0) for d in buckets]})
            ctx['chart_price_json'] = json.dumps({'labels': labels, 'venda': [all_rev.get(d, 0) for d in buckets], 'compra': [all_cost.get(d, 0) for d in buckets]})
            ctx['chart_subtitle']   = f"por dia — {MONTHS_PT[now.month - 1]}/{now.year}"

        else:
            # Monthly buckets
            if period == 'year':
                buckets = [date(now.year, m, 1) for m in range(1, now.month + 1)]
                labels  = [MONTHS_PT[m.month - 1] for m in buckets]
                ctx['chart_subtitle'] = f"por mês — {now.year}"
            else:  # all
                first_item = SaleItem.objects.order_by('sale__sale_date').first()
                if first_item:
                    d = first_item.sale.sale_date.date().replace(day=1)
                else:
                    d = date(now.year, now.month, 1)
                today_first = date(now.year, now.month, 1)
                buckets = []
                while d <= today_first:
                    buckets.append(d)
                    mn, yr = d.month + 1, d.year
                    if mn > 12:
                        mn, yr = 1, yr + 1
                    d = date(yr, mn, 1)
                labels = [f"{MONTHS_PT[m.month - 1]}/{str(m.year)[2:]}" for m in buckets]
                ctx['chart_subtitle'] = "por mês — todo período"

            def _by_month(qs, expr):
                return {
                    row['month'].date().replace(day=1): float(row['total'] or 0)
                    for row in (
                        qs.annotate(month=TruncMonth('sale__sale_date'))
                          .values('month')
                          .annotate(total=Sum(expr))
                          .order_by('month')
                    )
                }

            paid_rev  = _by_month(base_qs.filter(sale__is_paid=True), rev_expr)
            pend_rev  = _by_month(base_qs.filter(sale__is_paid=False), rev_expr)
            all_rev   = _by_month(base_qs, rev_expr)
            all_cost  = _by_month(base_qs, cost_expr)

            ctx['chart_data_json']  = json.dumps({'labels': labels, 'recebido': [paid_rev.get(m, 0) for m in buckets], 'a_receber': [pend_rev.get(m, 0) for m in buckets]})
            ctx['chart_price_json'] = json.dumps({'labels': labels, 'venda': [all_rev.get(m, 0) for m in buckets], 'compra': [all_cost.get(m, 0) for m in buckets]})

        return ctx
