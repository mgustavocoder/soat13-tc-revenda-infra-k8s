"""Gera docs/arquitetura-seguranca-saga.pdf.

Uso: python3 docs/build_architecture_pdf.py
Requer reportlab 4.x e as fontes DejaVu (pacote fonts-dejavu-core).
"""
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether, ListFlowable, ListItem, PageBreak, Paragraph, Preformatted,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)

OUTPUT = Path(__file__).with_name('arquitetura-seguranca-saga.pdf')
FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')
pdfmetrics.registerFont(TTFont('Sans', FONT_DIR / 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('Sans-Bold', FONT_DIR / 'DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Mono', FONT_DIR / 'DejaVuSansMono.ttf'))
pdfmetrics.registerFontFamily('Sans', normal='Sans', bold='Sans-Bold', italic='Sans', boldItalic='Sans-Bold')

# Paleta
INK = colors.HexColor('#1B2430')
MUTED = colors.HexColor('#5B6573')
NAVY = colors.HexColor('#1F3A5F')
TEAL = colors.HexColor('#2A7F8E')
AMBER = colors.HexColor('#B7791F')
RED = colors.HexColor('#B23B3B')
LINE = colors.HexColor('#C9D1DB')
FILL_NAVY = colors.HexColor('#E7EDF5')
FILL_TEAL = colors.HexColor('#E3F2F3')
FILL_AMBER = colors.HexColor('#FBF1DF')
FILL_GREY = colors.HexColor('#F3F5F8')
FILL_RED = colors.HexColor('#F8E5E5')
CONTENT_WIDTH = A4[0] - 4 * cm

# ---------------------------------------------------------------- estilos
base = ParagraphStyle('base', fontName='Sans', fontSize=9.6, leading=14, textColor=INK, spaceAfter=6)
styles = {
    'body': base,
    'small': ParagraphStyle('small', parent=base, fontSize=8.4, leading=11.5, textColor=MUTED),
    'h1': ParagraphStyle('h1', parent=base, fontName='Sans-Bold', fontSize=17, leading=22, textColor=NAVY,
                         spaceBefore=4, spaceAfter=10),
    'h2': ParagraphStyle('h2', parent=base, fontName='Sans-Bold', fontSize=12, leading=16, textColor=NAVY,
                         spaceBefore=10, spaceAfter=5),
    'cell': ParagraphStyle('cell', parent=base, fontSize=8.4, leading=11, spaceAfter=0),
    'cellb': ParagraphStyle('cellb', parent=base, fontName='Sans-Bold', fontSize=8.4, leading=11, spaceAfter=0,
                            textColor=colors.white),
    'caption': ParagraphStyle('caption', parent=base, fontSize=8, leading=10, textColor=MUTED,
                              alignment=TA_CENTER, spaceBefore=2, spaceAfter=10),
    'code': ParagraphStyle('code', fontName='Mono', fontSize=7.6, leading=9.6, textColor=INK,
                           backColor=FILL_GREY, borderPadding=6, spaceBefore=4, spaceAfter=10),
    'cover_title': ParagraphStyle('ct', parent=base, fontName='Sans-Bold', fontSize=28, leading=34, textColor=NAVY),
    'cover_sub': ParagraphStyle('cs', parent=base, fontSize=13, leading=19, textColor=MUTED),
}


def p(text, style='body'):
    return Paragraph(text, styles[style])


def bullets(items):
    return ListFlowable(
        [ListItem(p(item), leftIndent=12, value='•') for item in items],
        bulletType='bullet', start='•', leftIndent=12, bulletFontName='Sans', bulletColor=TEAL,
    )


def table(rows, widths, header=True):
    data = [[p(str(c), 'cellb' if header and i == 0 else 'cell') for c in row] for i, row in enumerate(rows)]
    t = Table(data, colWidths=[w * CONTENT_WIDTH for w in widths], repeatRows=1 if header else 0)
    style = [
        ('GRID', (0, 0), (-1, -1), 0.4, LINE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, FILL_GREY]),
    ]
    if header:
        style.append(('BACKGROUND', (0, 0), (-1, 0), NAVY))
    t.setStyle(TableStyle(style))
    return t


def code(text):
    return Preformatted(text.strip('\n'), styles['code'])


# ---------------------------------------------------------------- diagramas
def box(d, x, y, w, h, text, fill=FILL_NAVY, stroke=NAVY, size=7.6, bold_first=True, color=INK):
    d.add(Rect(x, y, w, h, rx=4, ry=4, fillColor=fill, strokeColor=stroke, strokeWidth=0.8))
    lines = text.split('\n')
    lead = size * 1.25
    top = y + h / 2 + (len(lines) - 1) * lead / 2 - size * 0.35
    for i, line in enumerate(lines):
        font = 'Sans-Bold' if (bold_first and i == 0) else 'Sans'
        fs = size if i == 0 else size - 0.6
        d.add(String(x + w / 2, top - i * lead, line, fontName=font, fontSize=fs, fillColor=color, textAnchor='middle'))


def arrow(d, x1, y1, x2, y2, label=None, color=MUTED, dashed=False, label_dx=0, label_dy=3, size=6.4,
          anchor='middle'):
    line = Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=0.9)
    if dashed:
        line.strokeDashArray = [3, 2]
    d.add(line)
    import math
    angle = math.atan2(y2 - y1, x2 - x1)
    head = 5
    left = (x2 - head * math.cos(angle - 0.4), y2 - head * math.sin(angle - 0.4))
    right = (x2 - head * math.cos(angle + 0.4), y2 - head * math.sin(angle + 0.4))
    d.add(Polygon([x2, y2, left[0], left[1], right[0], right[1]], fillColor=color, strokeColor=color, strokeWidth=0.5))
    if label:
        for i, text in enumerate(label.split('\n')):
            d.add(String((x1 + x2) / 2 + label_dx, (y1 + y2) / 2 + label_dy - i * (size + 1.5), text,
                         fontName='Sans', fontSize=size, fillColor=color, textAnchor=anchor))


def path(d, points, color=MUTED, dashed=False):
    """Seta em cotovelo: segmentos retos com ponta só no último."""
    for (x1, y1), (x2, y2) in zip(points[:-2], points[1:-1]):
        seg = Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=0.9)
        if dashed:
            seg.strokeDashArray = [3, 2]
        d.add(seg)
    (x1, y1), (x2, y2) = points[-2], points[-1]
    arrow(d, x1, y1, x2, y2, color=color, dashed=dashed)


def label(d, x, y, text, size=7, color=MUTED, bold=False, anchor='start'):
    d.add(String(x, y, text, fontName='Sans-Bold' if bold else 'Sans', fontSize=size, fillColor=color,
                 textAnchor=anchor))


def aws_diagram():
    w, h = CONTENT_WIDTH, 330
    d = Drawing(w, h)
    # Borda pública
    label(d, 0, 318, 'Internet', 7, MUTED, True)
    label(d, w, 318, 'ECR guarda as imagens das 3 aplicações', 6.6, MUTED, anchor='end')
    box(d, 0, 268, 78, 40, 'Cliente HTTP\nx-api-key', FILL_GREY, MUTED)
    box(d, 102, 268, 92, 40, 'API Gateway\nREST regional\nAPI key + throttling', FILL_AMBER, AMBER)
    box(d, 218, 268, 70, 40, 'VPC Link v2\nprivado', FILL_AMBER, AMBER)
    box(d, 312, 268, 82, 40, 'ALB interno\nIngress', FILL_AMBER, AMBER)
    arrow(d, 78, 288, 102, 288, 'HTTPS', size=5.6, label_dy=4)
    arrow(d, 194, 288, 218, 288)
    arrow(d, 288, 288, 312, 288)
    # VPC
    d.add(Rect(0, 0, w, 258, rx=6, ry=6, fillColor=None, strokeColor=LINE, strokeWidth=1, strokeDashArray=[4, 3]))
    label(d, 8, 246, 'VPC privada  •  subnets privadas', 7, MUTED, True)
    # EKS: APIs e workers
    d.add(Rect(10, 100, 330, 136, rx=6, ry=6, fillColor=colors.HexColor('#F7FAFC'), strokeColor=NAVY, strokeWidth=0.9))
    label(d, 18, 226, 'Amazon EKS  •  namespace revenda', 7.2, NAVY, True)
    arrow(d, 330, 268, 330, 236)
    label(d, 336, 250, 'roteamento por path:', 6.4, MUTED)
    label(d, 336, 241, '/api/clientes  /api/vendas  /api/veiculos', 6.4, MUTED)
    box(d, 20, 172, 80, 44, 'clientes\nAPI :3001\n2 réplicas', FILL_NAVY)
    box(d, 140, 172, 85, 44, 'vendas\nAPI :3003\n2 réplicas', FILL_NAVY)
    box(d, 245, 172, 85, 44, 'veiculos\nAPI :3002\n2 réplicas', FILL_NAVY)
    arrow(d, 140, 194, 100, 194, 'HTTP', label_dy=4, size=6)
    box(d, 155, 110, 70, 40, 'vendas-worker\nIRSA', FILL_TEAL, TEAL, size=7)
    box(d, 245, 110, 85, 40, 'veiculos-worker\nIRSA', FILL_TEAL, TEAL, size=7)
    # SQS
    box(d, 20, 22, 100, 36, 'SQS vendas-eventos\n+ DLQ', FILL_TEAL, TEAL, size=7)
    box(d, 135, 22, 110, 36, 'SQS veiculos-eventos\n+ DLQ', FILL_TEAL, TEAL, size=7)
    path(d, [(147, 172), (147, 88), (70, 88), (70, 58)], TEAL)          # vendas API publica
    label(d, 74, 76, 'publica', 6.2, TEAL)
    path(d, [(70, 22), (70, 10), (300, 10), (300, 110)], TEAL)          # veiculos-worker consome
    label(d, 304, 70, 'consome', 6.2, TEAL)
    path(d, [(260, 110), (260, 40), (245, 40)], TEAL)                   # veiculos-worker publica
    label(d, 264, 70, 'publica', 6.2, TEAL)
    arrow(d, 190, 58, 190, 110, color=TEAL)                             # vendas-worker consome
    label(d, 194, 76, 'consome', 6.2, TEAL)
    # RDS + Secrets
    box(d, 362, 182, 112, 36, 'RDS MySQL clientes\nprivado, criptografado', FILL_GREY, MUTED, size=7)
    box(d, 362, 134, 112, 36, 'RDS MySQL veiculos\nprivado, criptografado', FILL_GREY, MUTED, size=7)
    box(d, 362, 86, 112, 36, 'RDS MySQL vendas\nprivado, criptografado', FILL_GREY, MUTED, size=7)
    box(d, 362, 22, 112, 40, 'Secrets Manager\ncredenciais RDS\n(lidas no deploy)', FILL_GREY, MUTED, size=7)
    for y in (200, 152, 108):
        arrow(d, 340, y if y != 108 else 104, 362, y, color=LINE)
    return d

def layers_diagram():
    w, h = CONTENT_WIDTH, 190
    d = Drawing(w, h)
    cx = 150
    d.add(Rect(cx - 145, 6, 290, 178, rx=10, ry=10, fillColor=FILL_AMBER, strokeColor=AMBER))
    d.add(Rect(cx - 105, 26, 210, 120, rx=10, ry=10, fillColor=FILL_TEAL, strokeColor=TEAL))
    d.add(Rect(cx - 62, 46, 124, 62, rx=10, ry=10, fillColor=FILL_NAVY, strokeColor=NAVY))
    label(d, cx, 170, 'infrastructure', 8.4, AMBER, True, 'middle')
    label(d, cx, 159, 'Express • MySQL • SQS • HTTP • worker', 6.8, MUTED, anchor='middle')
    label(d, cx, 132, 'application', 8.4, TEAL, True, 'middle')
    label(d, cx, 121, 'use cases • portas (gateways)', 6.8, MUTED, anchor='middle')
    label(d, cx, 88, 'domain', 8.4, NAVY, True, 'middle')
    label(d, cx, 77, 'entidades • value objects', 6.8, MUTED, anchor='middle')
    label(d, cx, 67, 'erros de domínio', 6.8, MUTED, anchor='middle')
    label(d, cx, 14, 'as dependências apontam sempre para dentro', 6.8, AMBER, anchor='middle')
    # legenda direita
    x = 318
    rows = [
        (NAVY, 'domain', ['Regras puras: Venda (estados),', 'Veiculo (transições da saga),', 'Cliente. Sem dependências.']),
        (TEAL, 'application', ['Casos de uso e portas:', 'VendaRepository, ClientesGateway,', '*EventosPublisher.']),
        (AMBER, 'infrastructure', ['Implementa as portas (MySQL, SQS,', 'HTTP), expõe a API e compõe', 'as dependências (factories).']),
    ]
    for i, (c, title, lines) in enumerate(rows):
        y = 170 - i * 60
        d.add(Rect(x, y - 2, 8, 8, fillColor=c, strokeColor=c))
        label(d, x + 14, y, title, 8, c, True)
        for j, line in enumerate(lines):
            label(d, x + 14, y - 12 - j * 9.5, line, 6.6, INK)
    return d


def saga_sequence():
    steps = [
        ('msg', 0, 1, 'POST /reservar', INK, False), ('note', 1, 'venda RESERVA_PROCESSANDO', NAVY, FILL_NAVY),
        ('msg', 1, 2, 'VENDA_CRIADA', TEAL, False), ('msg', 1, 0, '202 + statusUrl', MUTED, True),
        ('msg', 2, 3, 'VENDA_CRIADA', TEAL, False), ('note', 3, 'veículo RESERVADO', NAVY, FILL_NAVY),
        ('msg', 3, 4, 'VEICULO_RESERVADO', TEAL, False), ('msg', 4, 5, 'VEICULO_RESERVADO', TEAL, False),
        ('note', 5, 'AGUARDANDO_PAGAMENTO', NAVY, FILL_NAVY),
        ('msg', 0, 1, 'POST /confirmar-pagamento', INK, False), ('note', 1, 'PAGAMENTO_PROCESSANDO', NAVY, FILL_NAVY),
        ('msg', 1, 2, 'PAGAMENTO_RECEBIDO', TEAL, False), ('msg', 2, 3, 'PAGAMENTO_RECEBIDO', TEAL, False),
        ('note', 3, 'veículo VENDIDO', NAVY, FILL_NAVY), ('msg', 3, 4, 'VEICULO_VENDIDO', TEAL, False),
        ('msg', 4, 5, 'VEICULO_VENDIDO', TEAL, False), ('note', 5, 'PAGAMENTO_CONFIRMADO', TEAL, FILL_TEAL),
    ]
    msg_gap, note_gap, top = 19, 18, 50
    h = top + sum(msg_gap if st[0] == 'msg' else note_gap for st in steps) + 6
    w = CONTENT_WIDTH
    d = Drawing(w, h)
    lanes = [('Cliente HTTP', FILL_GREY, MUTED), ('Vendas API', FILL_NAVY, NAVY), ('SQS\nvendas-eventos', FILL_TEAL, TEAL),
             ('Veículos\nworker', FILL_NAVY, NAVY), ('SQS\nveiculos-eventos', FILL_TEAL, TEAL), ('Vendas\nworker', FILL_NAVY, NAVY)]
    step = w / len(lanes)
    xs = [step * i + step / 2 for i in range(len(lanes))]
    for (name, fill, stroke), x in zip(lanes, xs):
        box(d, x - 36, h - 32, 72, 30, name, fill, stroke, size=7)
        ln = Line(x, 2, x, h - 32, strokeColor=LINE, strokeWidth=0.8)
        ln.strokeDashArray = [2, 2]
        d.add(ln)
    y = h - top
    for st in steps:
        if st[0] == 'msg':
            _, a, b, text, color, dashed = st
            arrow(d, xs[a], y, xs[b], y, text, color=color, dashed=dashed, label_dy=3)
            y -= msg_gap
        else:
            _, a, text, color, fill = st
            tw = pdfmetrics.stringWidth(text, 'Sans', 6.4) + 10
            d.add(Rect(xs[a] - tw / 2, y - 3, tw, 12, rx=3, ry=3, fillColor=fill, strokeColor=color, strokeWidth=0.6))
            d.add(String(xs[a], y + 0.5, text, fontName='Sans', fontSize=6.4, fillColor=color, textAnchor='middle'))
            y -= note_gap
    return d

def state_machine():
    w, h = CONTENT_WIDTH, 215
    d = Drawing(w, h)
    bw, bh = 116, 30
    pos = {'RP': (0, 160), 'AP': (182, 160), 'PP': (364, 160),
           'RF': (0, 76), 'PF': (182, 76), 'PC': (364, 76), 'CA': (182, 2)}
    names = {
        'RP': ('RESERVA_PROCESSANDO', FILL_NAVY, NAVY), 'AP': ('AGUARDANDO_PAGAMENTO', FILL_NAVY, NAVY),
        'PP': ('PAGAMENTO_PROCESSANDO', FILL_NAVY, NAVY), 'RF': ('RESERVA_FALHOU', FILL_RED, RED),
        'PF': ('PAGAMENTO_FALHOU', FILL_AMBER, AMBER), 'PC': ('PAGAMENTO_CONFIRMADO', FILL_TEAL, TEAL),
        'CA': ('CANCELADA', FILL_GREY, MUTED),
    }
    for k, (x, y) in pos.items():
        n, f, st = names[k]
        box(d, x, y, bw, bh, n, f, st, size=7)
    fs = 6.2
    # entrada
    label(d, 58, 206, 'POST /reservar', fs, MUTED, anchor='middle')
    arrow(d, 58, 202, 58, 190)
    # linha 1
    arrow(d, 116, 175, 182, 175, color=TEAL)
    label(d, 149, 187, 'VEICULO_', fs, TEAL, anchor='middle')
    label(d, 149, 179, 'RESERVADO', fs, TEAL, anchor='middle')
    arrow(d, 298, 175, 364, 175)
    label(d, 331, 187, 'confirmar', fs, INK, anchor='middle')
    label(d, 331, 179, 'pagamento', fs, INK, anchor='middle')
    # falha de reserva
    arrow(d, 58, 160, 58, 106, color=RED)
    label(d, 62, 138, 'VEICULO_RESERVA_FALHOU', fs, RED)
    label(d, 62, 130, 'ou falha ao publicar', fs, RED)
    # pagamento confirmado
    arrow(d, 447, 160, 447, 106, color=TEAL)
    label(d, 443, 136, 'VEICULO_VENDIDO', fs, TEAL, anchor='end')
    # falha de pagamento e nova tentativa
    arrow(d, 380, 160, 298, 98, color=AMBER)
    label(d, 340, 113, 'VEICULO_VENDA_FALHOU', fs, AMBER)
    arrow(d, 222, 106, 222, 160)
    label(d, 226, 133, 'confirmar de novo', fs, INK)
    # cancelamentos
    arrow(d, 260, 76, 260, 32, color=MUTED)
    label(d, 264, 52, 'cancelar', fs, MUTED)
    path(d, [(182, 168), (166, 168), (166, 17), (182, 17)], MUTED)
    label(d, 162, 52, 'cancelar', fs, MUTED, anchor='end')
    label(d, 312, 26, 'CANCELADA publica VENDA_CANCELADA:', 6.6, MUTED)
    label(d, 312, 16, 'veículos libera a reserva (compensação).', 6.6, MUTED)
    return d

def caption(text):
    return p(text, 'caption')


# ---------------------------------------------------------------- página
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont('Sans', 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(2 * cm, 1.2 * cm, 'SOAT13 Revenda — Arquitetura, segurança e Saga')
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f'{doc.page}')
    canvas.setStrokeColor(LINE)
    canvas.line(2 * cm, 1.55 * cm, A4[0] - 2 * cm, 1.55 * cm)
    canvas.restoreState()


def on_cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, A4[1] - 1.1 * cm, A4[0], 1.1 * cm, fill=1, stroke=0)
    canvas.setFillColor(TEAL)
    canvas.rect(0, A4[1] - 1.35 * cm, A4[0], 0.25 * cm, fill=1, stroke=0)
    canvas.restoreState()


# ---------------------------------------------------------------- conteúdo
def build():
    s = []
    s += [Spacer(1, 4.2 * cm),
          p('SOAT13 Revenda', 'cover_title'),
          p('Arquitetura, segurança e Saga coreografada', 'cover_sub'),
          Spacer(1, 0.6 * cm),
          p('Plataforma de revenda de veículos composta por três microsserviços Node.js independentes '
            '(Clientes, Veículos e Vendas) em Amazon EKS, com bancos MySQL isolados em RDS, exposição '
            'pública por API Gateway e integração entre Vendas e Veículos por eventos SQS.'),
          Spacer(1, 0.8 * cm),
          table([
              ['Repositório', 'Responsabilidade'],
              ['soat13-tc-revenda-clientes', 'Cadastro e consulta de clientes'],
              ['soat13-tc-revenda-veiculos', 'Catálogo de veículos e participante da saga (reserva, venda, liberação)'],
              ['soat13-tc-revenda-vendas', 'Reservas e vendas; inicia a saga e reage aos eventos de veículos'],
              ['soat13-tc-revenda-infra-k8s', 'VPC, EKS, ECR, SQS, IRSA, ALB, API Gateway, manifestos e deploy'],
              ['soat13-tc-revenda-infra-db', 'Três instâncias RDS MySQL privadas e credenciais no Secrets Manager'],
          ], [0.36, 0.64]),
          Spacer(1, 1.2 * cm),
          p('Versão do documento: novembro de 2026.', 'small'),
          PageBreak()]

    # 1. Visão geral
    s += [p('1. Visão geral', 'h1'),
          p('Cada serviço é um repositório próprio, com código, dependências, imagem Docker e banco de dados '
            'exclusivos. Nenhum serviço acessa o banco de outro: Vendas consulta Clientes por HTTP interno e '
            'coordena a disponibilidade do veículo com Veículos somente por eventos. As colunas '
            '<font name="Mono">cliente_id</font> e <font name="Mono">veiculo_id</font> de Vendas guardam '
            'identificadores recebidos dos outros serviços, sem chaves estrangeiras entre bancos.'),
          table([
              ['Serviço', 'Porta', 'Banco', 'Processos', 'Integrações'],
              ['Clientes', '3001', 'clientes_db', 'API', 'Nenhuma (é consultado por Vendas)'],
              ['Veículos', '3002', 'veiculos_db', 'API + worker', 'Consome vendas-eventos, publica veiculos-eventos'],
              ['Vendas', '3003', 'vendas_db', 'API + worker',
               'HTTP para Clientes; publica vendas-eventos, consome veiculos-eventos'],
          ], [0.13, 0.08, 0.15, 0.16, 0.48]),
          Spacer(1, 8),
          p('Stack: Node.js 22, Express 5, mysql2, AWS SDK v3 (SQS), testes com <font name="Mono">node:test</font>. '
            'Infraestrutura com Terraform 1.9 e manifestos Kubernetes aplicados pelo script '
            '<font name="Mono">scripts/deploy.sh</font>.'),
          p('2. Arquitetura na AWS', 'h1'),
          KeepTogether([aws_diagram(), caption('Figura 1 — Componentes AWS e fluxo de requisições e eventos.')]),
          table([
              ['Componente', 'Função'],
              ['API Gateway REST', 'Único ponto público. Exige API key (header x-api-key), aplica plano de uso e CORS.'],
              ['VPC Link v2 + ALB interno', 'Ligam o API Gateway ao Ingress do EKS sem expor o ALB à internet.'],
              ['Amazon EKS', 'Executa as três APIs e os dois workers (2 réplicas cada) em nós privados.'],
              ['Amazon SQS', 'Filas standard vendas-eventos e veiculos-eventos, cada uma com DLQ após 5 recebimentos.'],
              ['Amazon RDS MySQL', 'Uma instância privada e criptografada por serviço, acessível só pelo SG dos nós.'],
              ['Secrets Manager', 'Guarda as senhas master geradas pelo RDS; o deploy as copia para Secrets do Kubernetes.'],
              ['ECR', 'Repositório das imagens Docker de cada serviço.'],
          ], [0.28, 0.72]),
          Spacer(1, 10)]

    # 3. Clean Architecture
    s += [p('3. Clean Architecture', 'h1'),
          p('Os três serviços seguem a mesma organização em camadas, inspirada no serviço de referência '
            '<font name="Mono">soat13-tc-ordens</font>. A regra central é a direção das dependências: '
            'a infraestrutura conhece a aplicação, a aplicação conhece o domínio, e o domínio não conhece ninguém.'),
          KeepTogether([layers_diagram(), caption('Figura 2 — Camadas e regra de dependência.')]),
          code('''
src/
├── domain/
│   ├── entities/            Venda | Veiculo | Cliente + value-objects/ (Placa, Cpf, ...)
│   └── errors/              InvalidInput, ResourceNotFound, DuplicateResource, BusinessRule
├── application/
│   ├── gateways/            portas: *Repository, ClientesGateway, *EventosPublisher
│   └── usecases/            Venda[Saga]Usecase | Veiculo[Saga]Usecase | ClienteUsecase
└── infrastructure/
    ├── api/                 app.js (rotas), server.js, http-error-handler.js (erro → HTTP)
    ├── controllers/         controllers, wire-in (HTTP → DTO), controllers-factory
    ├── datasource/          pool MySQL e repositórios Mysql*Repository
    ├── gateways/            ClientesHttpGateway (somente Vendas)
    └── messaging/           SqsProducer, SqsConsumer, saga-consumer-factory, worker.js
'''),
          p('Decisões de projeto', 'h2'),
          bullets([
              '<b>Portas na aplicação, implementações na infraestrutura.</b> Os casos de uso dependem de '
              'interfaces (ex.: <font name="Mono">VendaRepository</font>); <font name="Mono">MysqlVendaRepository</font> '
              'e <font name="Mono">SqsVendaEventosPublisher</font> as implementam. Isso permite testar os casos de uso '
              'com dublês em memória.',
              '<b>Regras no domínio.</b> A entidade <font name="Mono">Venda</font> concentra a máquina de estados e as '
              'mensagens de negócio; <font name="Mono">Veiculo</font> concentra as transições da saga e a regra de que '
              'só a venda dona da reserva pode concluí-la ou liberá-la.',
              '<b>Erros tipados.</b> O domínio lança erros semânticos e só o '
              '<font name="Mono">http-error-handler</font> os traduz para HTTP (400, 404, 409, 503, 500).',
              '<b>Composição explícita.</b> <font name="Mono">controllers-factory</font> e '
              '<font name="Mono">saga-consumer-factory</font> montam o grafo de dependências; '
              '<font name="Mono">server.js</font> e <font name="Mono">worker.js</font> são os únicos pontos que leem '
              'variáveis de ambiente.',
          ]),
          table([
              ['Erro', 'HTTP', 'Exemplo'],
              ['InvalidInputError', '400', 'Placa ou CPF inválido; edição de veículo reservado'],
              ['ResourceNotFoundError', '404', 'Venda, cliente ou veículo inexistente'],
              ['DuplicateResourceError', '409', 'CPF/e-mail/placa já cadastrados; venda ativa para o veículo'],
              ['BusinessRuleError', '409', 'Cancelar venda confirmada; confirmar pagamento em processamento'],
              ['ServiceUnavailableError', '503', 'Fila de eventos ou serviço de clientes indisponível'],
          ], [0.3, 0.1, 0.6]),
          PageBreak()]

    # 4. Saga
    s += [p('4. Saga coreografada', 'h1'),
          p('Uma venda envolve duas transações locais em bancos diferentes: registrar a venda (Vendas) e '
            'reservar/vender o veículo (Veículos). Não há transação distribuída; a consistência é garantida por uma '
            '<b>saga</b>, uma sequência de transações locais encadeadas por eventos, com compensações para desfazer '
            'etapas quando algo falha.'),
          p('Por que coreografia', 'h2'),
          p('Cada serviço publica <i>eventos de domínio</i> na sua própria fila e reage aos eventos do outro, sem '
            'orquestrador central. Nenhum serviço comanda o outro nem conhece as rotas HTTP do outro: Veículos '
            'decide sozinho se o veículo pode ser reservado, e Vendas apenas reage ao resultado. Isso mantém os '
            'serviços desacoplados e permite que cada um evolua e escale de forma independente.'),
          table([
              ['Fila', 'Produtor', 'Consumidor', 'Eventos'],
              ['vendas-eventos', 'Vendas (API e worker)', 'veiculos-worker',
               'VENDA_CRIADA, PAGAMENTO_RECEBIDO, VENDA_CANCELADA'],
              ['veiculos-eventos', 'veiculos-worker', 'vendas-worker',
               'VEICULO_RESERVADO, VEICULO_RESERVA_FALHOU, VEICULO_VENDIDO, VEICULO_VENDA_FALHOU, VEICULO_LIBERADO'],
          ], [0.18, 0.2, 0.17, 0.45]),
          Spacer(1, 8),
          KeepTogether([saga_sequence(), caption('Figura 3 — Caminho feliz da saga: reserva e confirmação de pagamento.')]),
          PageBreak(),
          p('Máquina de estados da venda', 'h2'),
          KeepTogether([state_machine(), caption('Figura 4 — Estados da venda e eventos que provocam cada transição.')]),
          table([
              ['Evento recebido', 'Serviço', 'Transação local', 'Evento publicado'],
              ['VENDA_CRIADA', 'Veículos', 'DISPONIVEL → RESERVADO para a venda',
               'VEICULO_RESERVADO (veiculoId, preço) ou VEICULO_RESERVA_FALHOU (motivo)'],
              ['PAGAMENTO_RECEBIDO', 'Veículos', 'RESERVADO → VENDIDO se a reserva for da venda',
               'VEICULO_VENDIDO ou VEICULO_VENDA_FALHOU'],
              ['VENDA_CANCELADA', 'Veículos', 'RESERVADO → DISPONIVEL se a reserva for da venda', 'VEICULO_LIBERADO'],
              ['VEICULO_RESERVADO', 'Vendas', 'RESERVA_PROCESSANDO → AGUARDANDO_PAGAMENTO',
               'VENDA_CANCELADA se a venda já estiver encerrada'],
              ['VEICULO_RESERVA_FALHOU', 'Vendas', 'RESERVA_PROCESSANDO → RESERVA_FALHOU', '—'],
              ['VEICULO_VENDIDO', 'Vendas', 'PAGAMENTO_PROCESSANDO → PAGAMENTO_CONFIRMADO', '—'],
              ['VEICULO_VENDA_FALHOU', 'Vendas', 'PAGAMENTO_PROCESSANDO → PAGAMENTO_FALHOU', '—'],
          ], [0.3, 0.11, 0.31, 0.28]),
          p('Compensações', 'h2'),
          bullets([
              '<b>Cancelamento:</b> a venda em AGUARDANDO_PAGAMENTO ou PAGAMENTO_FALHOU vai para CANCELADA e publica '
              'VENDA_CANCELADA; Veículos libera a reserva e responde VEICULO_LIBERADO.',
              '<b>Reserva tardia:</b> se VEICULO_RESERVADO chegar para uma venda já encerrada (RESERVA_FALHOU ou '
              'CANCELADA), Vendas publica VENDA_CANCELADA para desfazer a reserva.',
              '<b>Falha ao publicar:</b> a venda volta ao estado anterior (ou vai para RESERVA_FALHOU na reserva) e a '
              'API responde 503, mantendo o banco coerente com o que os outros serviços sabem.',
              '<b>Tentativas esgotadas:</b> na 5ª entrega sem sucesso de VENDA_CRIADA, Veículos desfaz uma reserva '
              'parcial e publica VEICULO_RESERVA_FALHOU; para PAGAMENTO_RECEBIDO publica VEICULO_VENDA_FALHOU. '
              'Assim a venda nunca fica aguardando para sempre; depois a mensagem vai para a DLQ.',
          ]),
          p('Confiabilidade', 'h2'),
          bullets([
              '<b>Idempotência:</b> as filas standard entregam pelo menos uma vez. Vendas só age se a venda estiver no '
              'estado que espera o evento; Veículos guarda <font name="Mono">venda_codigo</font> (a venda dona da '
              'reserva) e, numa entrega repetida, apenas republica o resultado.',
              '<b>Isolamento entre vendas:</b> uma venda não consegue vender nem liberar a reserva de outra; a '
              'restrição <font name="Mono">uq_vendas_veiculo_ativo</font> impede duas vendas ativas para a mesma placa.',
              '<b>Concorrência:</b> todas as gravações usam controle otimista '
              '(<font name="Mono">WHERE status = ?</font>); um conflito devolve a mensagem à fila para nova tentativa.',
              '<b>Mensagens inválidas</b> são descartadas; erros transitórios voltam após o visibility timeout (180 s).',
          ]),
          Spacer(1, 6)]

    # 5. Segurança
    s += [p('5. Segurança', 'h1'),
          table([
              ['Tema', 'Controle aplicado'],
              ['Exposição pública', 'Somente o API Gateway é público. ALB, nós do EKS, RDS e workers ficam em subnets privadas.'],
              ['Autenticação da API', 'API key obrigatória no API Gateway (403 sem a chave). Não é identidade de usuário.'],
              ['Acesso à AWS pelos pods', 'IRSA: um papel por ServiceAccount. vendas só publica em vendas-eventos e consome '
               'veiculos-eventos; veiculos faz o inverso. Nenhuma chave AWS em código ou Secrets.'],
              ['Banco de dados', 'Uma instância por serviço, criptografada, backups de 7 dias, deletion protection, '
               'acesso MySQL só pelo security group dos nós.'],
              ['Credenciais', 'Senhas geradas e gerenciadas pelo RDS no Secrets Manager; lidas pelo deploy sem impressão.'],
              ['Filas', 'Criptografia SSE gerenciada pelo SQS; DLQ com retenção de 14 dias para análise.'],
              ['Estado do Terraform', 'Bucket S3 privado, criptografado e versionado, com lock por arquivo.'],
              ['Aplicação', 'Sanitização XSS, cabeçalho x-powered-by desativado, rotas /internal não roteadas pelo Ingress.'],
              ['Dados pessoais', 'CPF e e-mail ficam apenas em Clientes (e CPF em Vendas para relacionar a operação); '
               'não há dados de cartão nem integração com meio de pagamento.'],
          ], [0.24, 0.76]),
          p('Limitações conhecidas', 'h2'),
          bullets([
              'Não há autorização por usuário, AWS WAF nem rate limit por cliente além do plano de uso da API key.',
              'A conexão entre API Gateway e ALB interno usa HTTP dentro da VPC.',
              'Os Secrets do Kubernetes não usam envelope encryption com KMS; restrinja o RBAC do cluster.',
              'RDS single-AZ por padrão; use Multi-AZ e teste restauração conforme os objetivos de disponibilidade.',
              'Gravar no banco e publicar o evento não é atômico. As compensações cobrem falhas de publicação; um '
              '<i>transactional outbox</i> eliminaria esse risco por completo.',
          ]),
          p('6. Deploy, testes e operação', 'h1'),
          p('O script <font name="Mono">scripts/deploy.sh</font> do repositório infra-k8s executa, em ordem: '
            'terraform apply (EKS, ECR, SQS, IRSA), terraform apply do infra-db, inicialização idempotente dos schemas '
            'com Jobs do Kubernetes, build e push das imagens para o ECR, renderização e aplicação dos manifestos, '
            'espera do rollout e um segundo apply que conecta o API Gateway ao listener do ALB.'),
          table([
              ['Nível', 'Escopo'],
              ['Unitário', 'Entidades e value objects, casos de uso com dublês em memória, consumidor SQS '
               '(retentativas, DLQ e compensação na última tentativa).'],
              ['Integração', 'API Express de cada serviço com repositórios e adaptadores reais sobre drivers simulados; '
               'saga de Vendas pelo consumidor SQS.'],
              ['Ponta a ponta', 'Três APIs e dois workers contra MySQL e SQS (LocalStack) e contra a AWS: caminho feliz, '
               'cancelamento com compensação, falhas de reserva, duplicatas e conflitos.'],
              ['Smoke test', 'scripts/smoke-test.mjs: 403 sem API key, CORS e GET 200 nas rotas principais.'],
          ], [0.18, 0.82]),
          p('Próximos passos sugeridos', 'h2'),
          bullets([
              'Adotar transactional outbox em Vendas e Veículos.',
              'Autenticação por usuário (ex.: Cognito/JWT) e AWS WAF no API Gateway.',
              'Alarmes do CloudWatch para mensagens na DLQ e idade da mensagem mais antiga nas filas.',
          ])]

    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm,
                            bottomMargin=2 * cm, title='SOAT13 Revenda — Arquitetura, segurança e Saga',
                            author='SOAT13 Revenda', subject='Documentação de arquitetura')
    doc.build(s, onFirstPage=on_cover, onLaterPages=on_page)
    print(OUTPUT)


if __name__ == '__main__':
    build()
