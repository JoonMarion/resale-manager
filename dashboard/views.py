import json
from datetime import date, datetime, time, timedelta
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


def _parse_date(value):
    """Parse YYYY-MM-DD query param; return date or None."""
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def _aware_start(d):
    """Timezone-aware datetime at start of day."""
    return timezone.make_aware(datetime.combine(d, time.min))


def _aware_end_exclusive(d):
    """Timezone-aware datetime just after end of day (exclusive upper bound)."""
    return timezone.make_aware(datetime.combine(d + timedelta(days=1), time.min))


def _fmt_br(d):
    return d.strftime('%d/%m/%Y')


MONTHS_PT = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']


class DashboardView(ProjectLoginRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        period = self.request.GET.get('period', 'month')
        if period not in ('month', 'year', 'all', 'custom'):
            period = 'month'

        start_param = _parse_date(self.request.GET.get('start'))
        end_param = _parse_date(self.request.GET.get('end'))

        # Custom without a start date falls back to showing the picker only
        custom_ready = period == 'custom' and start_param is not None
        if period == 'custom' and start_param is None:
            # Keep period=custom so the date panel stays open
            pass
        elif period == 'custom' and end_param and end_param < start_param:
            end_param = None

        ctx['period'] = period
        ctx['custom_start'] = start_param.isoformat() if start_param else ''
        ctx['custom_end'] = end_param.isoformat() if end_param else ''
        ctx['custom_ready'] = custom_ready

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

        now = timezone.localtime()
        today = timezone.localdate()
        ctx['today_iso'] = today.isoformat()

        # ── Base queryset (metrics) ──────────────────────────────────────────
        range_start = None
        range_end = None

        if period == 'month':
            range_start = today.replace(day=1)
            range_end = today
            base_qs = SaleItem.objects.filter(sale__sale_date__gte=_aware_start(range_start))
        elif period == 'year':
            range_start = today.replace(month=1, day=1)
            range_end = today
            base_qs = SaleItem.objects.filter(sale__sale_date__gte=_aware_start(range_start))
        elif period == 'custom' and custom_ready:
            range_start = start_param
            range_end = end_param or today
            if range_end > today:
                range_end = today
            base_qs = SaleItem.objects.filter(
                sale__sale_date__gte=_aware_start(range_start),
                sale__sale_date__lt=_aware_end_exclusive(range_end),
            )
        elif period == 'custom':
            # Picker open, no dates yet — show empty metrics
            base_qs = SaleItem.objects.none()
        else:
            base_qs = SaleItem.objects.all()

        if custom_ready:
            start_short = range_start.strftime('%d/%m')
            end_short = range_end.strftime('%d/%m')
            if end_param:
                ctx['period_label'] = f"{start_short}–{end_short}"
            else:
                ctx['period_label'] = f"{start_short}–hoje"
        else:
            ctx['period_label'] = ''

        faturado = base_qs.aggregate(v=Sum(rev_expr))['v'] or Decimal('0')
        recebido = base_qs.filter(sale__is_paid=True).aggregate(v=Sum(rev_expr))['v'] or Decimal('0')
        a_receber = base_qs.filter(sale__is_paid=False).aggregate(v=Sum(rev_expr))['v'] or Decimal('0')
        custo = base_qs.filter(sale__is_paid=True).aggregate(v=Sum(cost_expr))['v'] or Decimal('0')
        lucro_liquido = base_qs.filter(sale__is_paid=True).aggregate(v=Sum(profit_expr))['v'] or Decimal('0')

        ctx.update({
            'faturado_fmt': _brl(faturado),
            'recebido_fmt': _brl(recebido),
            'a_receber_fmt': _brl(a_receber),
            'custo_fmt': _brl(custo),
            'lucro_liquido_fmt': _brl(lucro_liquido),
            'lucro_positivo': lucro_liquido >= 0,
        })

        # ── Chart data (follow period filter) ───────────────────────────────
        use_daily = False
        if period == 'month':
            use_daily = True
            chart_start, chart_end = today.replace(day=1), today
            ctx['chart_subtitle'] = f"por dia — {MONTHS_PT[now.month - 1]}/{now.year}"
        elif period == 'custom' and custom_ready:
            chart_start, chart_end = range_start, range_end
            span_days = (chart_end - chart_start).days + 1
            use_daily = span_days <= 62
            if use_daily:
                ctx['chart_subtitle'] = f"por dia — {_fmt_br(chart_start)} a {_fmt_br(chart_end)}"
            else:
                ctx['chart_subtitle'] = f"por mês — {_fmt_br(chart_start)} a {_fmt_br(chart_end)}"
        elif period == 'custom':
            ctx['chart_data_json'] = json.dumps({'labels': [], 'recebido': [], 'a_receber': []})
            ctx['chart_price_json'] = json.dumps({'labels': [], 'venda': [], 'compra': []})
            ctx['chart_subtitle'] = "selecione o período"
            return ctx
        elif period == 'year':
            chart_start = date(now.year, 1, 1)
            chart_end = today
            ctx['chart_subtitle'] = f"por mês — {now.year}"
        else:  # all
            first_item = SaleItem.objects.order_by('sale__sale_date').first()
            if first_item:
                chart_start = first_item.sale.sale_date.date().replace(day=1)
            else:
                chart_start = date(now.year, now.month, 1)
            chart_end = today
            ctx['chart_subtitle'] = "por mês — todo período"

        if use_daily:
            buckets = [chart_start + timedelta(days=i) for i in range((chart_end - chart_start).days + 1)]
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

            paid_rev = _by_day(base_qs.filter(sale__is_paid=True), rev_expr)
            pend_rev = _by_day(base_qs.filter(sale__is_paid=False), rev_expr)
            all_rev = _by_day(base_qs, rev_expr)
            all_cost = _by_day(base_qs, cost_expr)

            ctx['chart_data_json'] = json.dumps({
                'labels': labels,
                'recebido': [paid_rev.get(d, 0) for d in buckets],
                'a_receber': [pend_rev.get(d, 0) for d in buckets],
            })
            ctx['chart_price_json'] = json.dumps({
                'labels': labels,
                'venda': [all_rev.get(d, 0) for d in buckets],
                'compra': [all_cost.get(d, 0) for d in buckets],
            })
        else:
            # Monthly buckets from chart_start month through chart_end month
            d = chart_start.replace(day=1)
            end_first = chart_end.replace(day=1)
            buckets = []
            while d <= end_first:
                buckets.append(d)
                mn, yr = d.month + 1, d.year
                if mn > 12:
                    mn, yr = 1, yr + 1
                d = date(yr, mn, 1)

            if period == 'year':
                labels = [MONTHS_PT[m.month - 1] for m in buckets]
            else:
                labels = [f"{MONTHS_PT[m.month - 1]}/{str(m.year)[2:]}" for m in buckets]

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

            paid_rev = _by_month(base_qs.filter(sale__is_paid=True), rev_expr)
            pend_rev = _by_month(base_qs.filter(sale__is_paid=False), rev_expr)
            all_rev = _by_month(base_qs, rev_expr)
            all_cost = _by_month(base_qs, cost_expr)

            ctx['chart_data_json'] = json.dumps({
                'labels': labels,
                'recebido': [paid_rev.get(m, 0) for m in buckets],
                'a_receber': [pend_rev.get(m, 0) for m in buckets],
            })
            ctx['chart_price_json'] = json.dumps({
                'labels': labels,
                'venda': [all_rev.get(m, 0) for m in buckets],
                'compra': [all_cost.get(m, 0) for m in buckets],
            })

        return ctx
