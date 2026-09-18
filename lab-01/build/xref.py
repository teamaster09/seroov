# -*- coding: utf-8 -*-
"""Разбиение абзаца на фрагменты для перекрёстных ссылок на рисунки.

Упоминание вида «рисунок N» в тексте превращается в серую перекрёстную
ссылку на закладку рисунка. Возвращает список кортежей:
  ('t', текст)          — обычный фрагмент;
  ('ref', текст, номер) — перекрёстная ссылка на рисунок с этим номером.
"""
import re

REF_RE = re.compile(r'рисунок\s+\d+', re.IGNORECASE)


def split_refs(text, max_fig=999):
    parts = []
    last = 0
    for m in REF_RE.finditer(text):
        num = int(re.search(r'\d+', m.group(0)).group())
        if m.start() > last:
            parts.append(('t', text[last:m.start()]))
        if 1 <= num <= max_fig:
            parts.append(('ref', m.group(0), num))
        else:
            parts.append(('t', m.group(0)))
        last = m.end()
    if last < len(text):
        parts.append(('t', text[last:]))
    return parts
