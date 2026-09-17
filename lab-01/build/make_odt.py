#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка отчёта ЛР1 в формате ODT — по ГОСТ 7.32-2017, оформление 1:1 по образцам.

Параметры:
  * Times New Roman, 14 пт
  * полуторный межстрочный интервал (150%)
  * выравнивание основного текста по ширине, абзацный отступ 1,25 см
  * поля: левое 3 см, правое 1,5 см, верхнее 2 см, нижнее 2 см
  * нумерация страниц внизу по центру (титульный лист не нумеруется)
  * каждый структурный элемент (РЕФЕРАТ, СОДЕРЖАНИЕ, ВВЕДЕНИЕ и т.п.) с нового листа,
    по центру, прописными, полужирным
  * подписи к рисункам — по центру, под рисунком: «Рисунок N – ...»
  * название таблицы — слева над таблицей: «Таблица N – ...»
  * заголовки разделов — с абзацного отступа, полужирным
  * заголовки подразделов — с абзацного отступа, полужирным, разреженный на 3 пт
"""
import os
import sys
from PIL import Image
from odf.opendocument import OpenDocumentText
from odf.style import (
    Style, TextProperties, ParagraphProperties, PageLayout, PageLayoutProperties,
    MasterPage, FontFace, GraphicProperties, TableColumnProperties,
    TableProperties, TableCellProperties, FooterStyle, HeaderStyle,
    PageLayoutProperties as PLP
)
from odf.style import Footer, Header
from odf.text import P, Span, PageNumber, S
from odf.draw import Frame, Image as DImage, TextBox
from odf.table import Table, TableColumn, TableRow, TableCell
from odf import teletype

BASE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(BASE)
SHOTS = os.path.join(LAB, 'screenshots')
OUTDIR = os.path.join(LAB, 'report')
OUTNAME = 'Отчёт_ЛР1_Установка_РОСА_на_VMware.odt'

sys.path.insert(0, BASE)
import content

# ----------- параметры страницы -----------
PAGE = dict(width=21.0, height=29.7,
            mleft=3.0, mright=1.5, mtop=2.0, mbottom=2.0,
            indent=1.25, size=14, lead_pct=150, img_width=15.0)
FONT = 'Times New Roman'


def cm(v):
    return '{:g}cm'.format(v)


def pt(v):
    return '{:g}pt'.format(v)


def pct(v):
    return '%d%%' % v


def img_dims(path, width_cm):
    with Image.open(path) as im:
        w, h = im.size
    return width_cm, width_cm * h / w


# ----------- вспомогательные генераторы стилей -----------
def mk_style(doc, name, family, parent=None, props=(), auto=False):
    target = doc.automaticstyles if auto else doc.styles
    s = Style(name=name, family=family)
    if parent:
        s.setAttribute('parentstylename', parent)
    for p in props:
        s.addElement(p)
    target.addElement(s)
    return s


def tp(doc, name, *, size=PAGE['size'], bold=False, italic=False, spacing=None,
       color='#000000', parent=None, auto=False):
    kw = dict(fontname=FONT, fontfamily="'%s'" % FONT,
              fontfamilygeneric='roman', fontpitch='variable',
              fontsize=pt(size), color=color)
    if bold:
        kw['fontweight'] = 'bold'
        kw['fontweightasian'] = 'bold'
        kw['fontweightcomplex'] = 'bold'
    if italic:
        kw['fontstyle'] = 'italic'
        kw['fontstyleasian'] = 'italic'
        kw['fontstylecomplex'] = 'italic'
    if spacing:
        kw['letterspacing'] = pt(spacing)
    el = TextProperties(**kw)
    return mk_style(doc, name, 'text' if family_tp else 'paragraph',
                    parent=parent, props=[el], auto=auto)


family_tp = False  # переключение — не используется, TextProperties добавляются как вложенные


def build():
    os.makedirs(OUTDIR, exist_ok=True)
    doc = OpenDocumentText()

    # -------- декларация шрифта --------
    ff = FontFace(name=FONT, fontfamily=FONT, fontfamilygeneric='roman',
                  fontpitch='variable')
    doc.fontfacedecls.addElement(ff)

    # -------- макеты страниц --------
    # Первая (титульная) без номера
    pl_cover = PageLayout(name='PL_Cover')
    pl_cover.addElement(PageLayoutProperties(
        pagewidth=cm(PAGE['width']), pageheight=cm(PAGE['height']),
        margintop=cm(PAGE['mtop']), marginbottom=cm(PAGE['mbottom']),
        marginleft=cm(PAGE['mleft']), marginright=cm(PAGE['mright']),
        printorientation='portrait', writingmode='lr-tb'))
    doc.automaticstyles.addElement(pl_cover)

    # Последующие страницы — с номером
    pl_main = PageLayout(name='PL_Main')
    pl_main.addElement(PageLayoutProperties(
        pagewidth=cm(PAGE['width']), pageheight=cm(PAGE['height']),
        margintop=cm(PAGE['mtop']), marginbottom=cm(PAGE['mbottom']),
        marginleft=cm(PAGE['mleft']), marginright=cm(PAGE['mright']),
        printorientation='portrait', writingmode='lr-tb'))
    doc.automaticstyles.addElement(pl_main)

    # -------- мастер-страницы --------
    # Титульный лист — без колонтитула
    mp_cover = MasterPage(name='MP_Cover', pagelayoutname='PL_Cover')
    doc.masterstyles.addElement(mp_cover)

    # Основная часть — footer с номером страницы по центру
    mp_main = MasterPage(name='MP_Main', pagelayoutname='PL_Main')
    footer = Footer()
    f_style_name = 'FooterP'
    fp = P(stylename=f_style_name)
    fspan = Span(stylename='FooterT')
    fspan.addElement(PageNumber(selectpage='current'))
    fp.addElement(fspan)
    footer.addElement(fp)
    mp_main.addElement(footer)
    doc.masterstyles.addElement(mp_main)

    # -------- стили --------
    def add_pstyle(name, *, parent=None, auto=False, **p):
        pp_kw = dict(textalign=p.get('align', 'justify'),
                     textindent=cm(p.get('indent', PAGE['indent'])),
                     margintop=p.get('before', '0cm'),
                     marginbottom=p.get('after', '0cm'),
                     marginleft=p.get('left', '0cm'),
                     marginright='0cm',
                     linespacing=p.get('lead', pt(21)))
        if p.get('keepnext'):
            pp_kw['keepwithnext'] = 'always'
        if p.get('pagebreak'):
            pp_kw['breakbefore'] = 'page'
        if 'masterpage' in p:
            pp_kw['masterpagename'] = p['masterpage']
        # vertical-align для ячеек
        if 'valign' in p:
            pp_kw['verticalalign'] = p['valign']

        tp_kw = dict(fontname=FONT, fontfamily="'%s'" % FONT,
                     fontfamilygeneric='roman', fontpitch='variable',
                     fontsize=pt(p.get('size', PAGE['size'])),
                     color=p.get('color', '#000000'))
        if p.get('bold'):
            tp_kw['fontweight'] = 'bold'
        if p.get('italic'):
            tp_kw['fontstyle'] = 'italic'
        if p.get('spacing'):
            tp_kw['letterspacing'] = pt(p['spacing'])
        if p.get('sizeasian'):
            tp_kw['fontsizeasian'] = pt(p['sizeasian'])
        if p.get('boldasian') or p.get('bold'):
            tp_kw['fontweightasian'] = 'bold'

        s = Style(name=name, family='paragraph')
        if parent:
            s.setAttribute('parentstylename', parent)
        if 'masterpage' in p:
            s.setAttribute('masterpagename', p['masterpage'])
        s.addElement(ParagraphProperties(**pp_kw))
        s.addElement(TextProperties(**tp_kw))
        if auto:
            doc.automaticstyles.addElement(s)
        else:
            doc.styles.addElement(s)
        return s

    # ---------- обычный текст ----------
    add_pstyle('Normal', align='justify', indent=PAGE['indent'],
               before='0cm', after='0cm')
    # по центру без отступа (для рисунков)
    add_pstyle('Center', align='center', indent=0, before='0.2cm',
               after='0cm', keepnext=True)
    # подпись к рисунку
    add_pstyle('FigCaption', align='center', indent=0, before='0.2cm',
               after=pt(21), keepnext=True)
    # название таблицы
    add_pstyle('TabCaption', align='left', indent=0, before='0.4cm',
               after='0.2cm', keepnext=True)
    # список (тире)
    add_pstyle('DashList', align='justify', indent=PAGE['indent'],
               before='0cm', after='0cm')
    # список источников
    add_pstyle('Refs', align='justify', indent=PAGE['indent'],
               before='0cm', after='0cm')
    # заголовок раздела (1 Название)
    add_pstyle('H1', align='left', indent=PAGE['indent'],
               before='0cm', after=pt(21), keepnext=True, bold=True)
    # заголовок подраздела (1.1) — разреженный на 3 пт
    add_pstyle('H2', align='left', indent=PAGE['indent'],
               before='0cm', after=pt(21), keepnext=True, bold=True,
               spacing=3)
    # заголовок структурного элемента (ВВЕДЕНИЕ и т.п.) — с новой стр, по центру, жирный
    add_pstyle('Struct', align='center', indent=0, before='0cm',
               after=pt(21), keepnext=True, bold=True, pagebreak=True)
    # заголовок первого структурного элемента (РЕФЕРАТ) — с новой стр и новым masterpage
    s_first = Style(name='FirstStruct', family='paragraph', masterpagename='MP_Main')
    s_first.addElement(ParagraphProperties(
        textalign='center', textindent='0cm', margintop='0cm',
        marginbottom=pt(21), keepwithnext='always', breakbefore='page',
        linespacing=pt(21)))
    s_first.addElement(TextProperties(fontname=FONT, fontfamily="'%s'" % FONT,
                                       fontfamilygeneric='roman',
                                       fontpitch='variable',
                                       fontsize=pt(PAGE['size']),
                                       fontweight='bold', color='#000000'))
    doc.automaticstyles.addElement(s_first)

    # стиль footer
    s_footer = Style(name='FooterP', family='paragraph')
    s_footer.addElement(ParagraphProperties(textalign='center', textindent='0cm',
                                             linespacing=pt(14)))
    s_footer.addElement(TextProperties(fontname=FONT, fontfamily="'%s'" % FONT,
                                        fontfamilygeneric='roman',
                                        fontpitch='variable',
                                        fontsize=pt(PAGE['size'])))
    doc.styles.addElement(s_footer)
    s_footer_t = Style(name='FooterT', family='text')
    s_footer_t.addElement(TextProperties(fontname=FONT, fontfamily="'%s'" % FONT,
                                          fontsize=pt(PAGE['size'])))
    doc.styles.addElement(s_footer_t)

    # Стили титульного листа
    def cover_style(name, *, bold=False, italic=False, size=14, lead=18, center=True):
        s = Style(name=name, family='paragraph', masterpagename='MP_Cover')
        kw = dict(textalign='center' if center else 'left',
                  textindent='0cm', margintop='0pt', marginbottom='0pt',
                  linespacing=pt(lead))
        s.addElement(ParagraphProperties(**kw))
        s.addElement(TextProperties(
            fontname=FONT, fontfamily="'%s'" % FONT, fontfamilygeneric='roman',
            fontpitch='variable', fontsize=pt(size),
            fontweight='bold' if bold else 'normal',
            fontstyle='italic' if italic else 'normal',
            color='#000000'))
        doc.styles.addElement(s)
        return s

    cover_style('CV')
    cover_style('CVb', bold=True)
    cover_style('CVbig', bold=True, size=18, lead=22)
    cover_style('CVi', italic=True, size=12, lead=15)
    # первый параграф титула — переключает на титульную master-page
    s_cover_first = Style(name='CoverFirst', family='paragraph', masterpagename='MP_Cover')
    s_cover_first.addElement(ParagraphProperties(
        textalign='center', textindent='0cm', margintop='0pt', marginbottom='0pt',
        linespacing=pt(18), breakafter='page'))
    s_cover_first.addElement(TextProperties(fontname=FONT, fontfamily="'%s'" % FONT,
                                             fontsize=pt(14), fontweight='bold'))
    doc.automaticstyles.addElement(s_cover_first)

    # Стили ячеек таблицы
    s_cell_p = Style(name='CellP', family='paragraph')
    s_cell_p.addElement(ParagraphProperties(textalign='left', textindent='0cm',
                                             margintop='3pt', marginbottom='3pt',
                                             marginleft='4pt', marginright='4pt',
                                             linespacing=pt(14)))
    s_cell_p.addElement(TextProperties(fontname=FONT, fontfamily="'%s'" % FONT,
                                        fontsize=pt(12)))
    doc.styles.addElement(s_cell_p)
    s_cell_pb = Style(name='CellPb', family='paragraph')
    s_cell_pb.addElement(ParagraphProperties(textalign='left', textindent='0cm',
                                              margintop='3pt', marginbottom='3pt',
                                              marginleft='4pt', marginright='4pt',
                                              linespacing=pt(14)))
    s_cell_pb.addElement(TextProperties(fontname=FONT, fontfamily="'%s'" % FONT,
                                         fontsize=pt(12), fontweight='bold'))
    doc.styles.addElement(s_cell_pb)

    # Рамка рисунка — без обводки, центрирована
    s_frame = Style(name='ImgFrame', family='graphic')
    s_frame.addElement(GraphicProperties(stroke='none', fill='none', wrap='none',
                                          horizontalpos='center',
                                          horizontalrel='paragraph',
                                          verticalpos='top', verticalrel='paragraph'))
    doc.automaticstyles.addElement(s_frame)

    # -------- сборка документа --------
    body = doc.text
    fig_no = [0]
    toc_styles_made = set()

    def add_fig(fname, caption):
        fig_no[0] += 1
        p = P(stylename='Center')
        path = os.path.join(SHOTS, fname)
        w_cm, h_cm = img_dims(path, PAGE['img_width'])
        fr = Frame(width=cm(w_cm), height=cm(h_cm))
        fr.setAttribute('stylename', s_frame.getAttribute('name'))
        fr.addElement(DImage(href=doc.addPicture(path)))
        p.addElement(fr)
        body.addElement(p)
        body.addElement(P(stylename='FigCaption',
                          text='Рисунок %d – %s' % (fig_no[0], caption)))

    def add_table(spec):
        body.addElement(P(stylename='TabCaption', text=spec['caption']))
        tbl = Table(name=spec['caption'])
        # рамка вокруг таблицы
        st = Style(name='tbl%d' % id(spec), family='table')
        st.addElement(TableProperties(width=cm(16.5), align='margins'))
        doc.automaticstyles.addElement(st)
        tbl.setAttribute('stylename', st)
        widths = ('5.5cm', '11.0cm')
        for w in widths:
            col = TableColumn()
            cs = Style(name='col%d%s' % (id(spec), w), family='table-column')
            cs.addElement(TableColumnProperties(columnwidth=w))
            doc.automaticstyles.addElement(cs)
            col.setAttribute('stylename', cs)
            tbl.addElement(col)
        # Заголовок
        hcs = Style(name='hc%d' % id(spec), family='table-cell')
        hcs.addElement(TableCellProperties(border='0.5pt solid #000000',
                                            paddingleft='0.1cm', paddingright='0.1cm',
                                            paddingtop='0.1cm', paddingbottom='0.1cm',
                                            verticalalign='middle'))
        doc.automaticstyles.addElement(hcs)
        cs = Style(name='cc%d' % id(spec), family='table-cell')
        cs.addElement(TableCellProperties(border='0.5pt solid #000000',
                                           paddingleft='0.1cm', paddingright='0.1cm',
                                           paddingtop='0.1cm', paddingbottom='0.1cm',
                                           verticalalign='middle'))
        doc.automaticstyles.addElement(cs)
        hr = TableRow()
        for val in spec['head']:
            cell = TableCell(stylename='hc%d' % id(spec))
            cell.addElement(P(stylename='CellPb', text=val))
            hr.addElement(cell)
        tbl.addElement(hr)
        for r in spec['rows']:
            tr = TableRow()
            for v in r:
                c = TableCell(stylename='cc%d' % id(spec))
                c.addElement(P(stylename='CellP', text=v))
                tr.addElement(c)
            tbl.addElement(tr)
        body.addElement(tbl)

    # ---- титульный лист ----
    first = True
    for line in content.TITLE:
        txt = line['t'] or ' '
        sz = line.get('sz', 14)
        if line.get('b') and sz == 18:
            st = 'CVbig'
        elif line.get('b'):
            st = 'CVb'
        elif line.get('i'):
            st = 'CVi'
        else:
            st = 'CV'
        if first:
            body.addElement(P(stylename='CoverFirst', text=txt))
            first = False
        else:
            body.addElement(P(stylename=st, text=txt))
        gap = line.get('gap', 0)
        if gap:
            n = max(1, int(gap // 18))
            for _ in range(n):
                body.addElement(P(stylename=st, text=' '))

    # ---- подсчёт для реферата ----
    n_figs = sum(1 for b in content.SECTIONS if b[0] == 'fig')
    n_tables = sum(1 for b in content.SECTIONS if b[0] == 'table')
    counts = dict(pages=27, figs=n_figs, tables=n_tables, sources=len(content.REFS))

    def fmt(t):
        try:
            return t.format(**counts)
        except Exception:
            return t

    first_struct = True
    for block in content.SECTIONS:
        k = block[0]
        if k == 'h1c':
            name = block[1]
            if first_struct:
                body.addElement(P(stylename='FirstStruct', text=name))
                first_struct = False
            else:
                body.addElement(P(stylename='Struct', text=name))
        elif k == 'h1':
            body.addElement(P(stylename='H1', text=block[1]))
        elif k == 'h2':
            body.addElement(P(stylename='H2', text=block[1]))
        elif k == 'p':
            body.addElement(P(stylename='Normal', text=fmt(block[1])))
        elif k == 'list':
            for item in block[1]:
                body.addElement(P(stylename='DashList', text='– ' + item))
        elif k == 'refs':
            for i, item in enumerate(block[1], 1):
                body.addElement(P(stylename='Refs', text='%d %s' % (i, item)))
        elif k == 'toc':
            # Структура содержания вручную с отточиями
            toc_items = [
                (0, 'ВВЕДЕНИЕ'),
                (0, '1 Операционная система «РОСА» и особенности установки дистрибутивов семейства Red Hat'),
                (1, '1.1 Общие сведения об операционной системе «РОСА»'),
                (1, '1.2 Особенности установки дистрибутивов семейства Red Hat'),
                (1, '1.3 Режимы сетевого взаимодействия виртуальных машин в VMware Workstation'),
                (0, '2 Используемое программное обеспечение и параметры виртуальной машины'),
                (0, '3 Создание виртуальной машины'),
                (0, '4 Установка операционной системы'),
                (0, 'ЗАКЛЮЧЕНИЕ'),
                (0, 'СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ'),
            ]
            for lvl, t in toc_items:
                style = 'Toc1' if lvl == 0 else 'Toc2'
                # стиль для СОДЕРЖАНИЯ создадим на лету
                sn = 'Toc%d' % lvl
                if sn not in toc_styles_made:
                    st = Style(name=sn, family='paragraph')
                    st.addElement(ParagraphProperties(
                        textalign='left', textindent='0cm',
                        marginleft=cm(lvl * 0.5),
                        margintop='0cm', marginbottom='0cm',
                        linespacing=pt(21)))
                    st.addElement(TextProperties(fontname=FONT, fontfamily="'%s'" % FONT,
                                                  fontsize=pt(PAGE['size'])))
                    doc.styles.addElement(st)
                    toc_styles_made.add(sn)
                body.addElement(P(stylename=sn, text=t))
        elif k == 'fig':
            add_fig(block[1], block[2])
        elif k == 'table':
            add_table(block[1])

    out_path = os.path.join(OUTDIR, OUTNAME)
    doc.save(out_path)
    print('ODT:', out_path)


if __name__ == '__main__':
    build()
