#!/usr/bin/env python3
"""Apply the OneTen v5 layer to the built pages in place.

Usage: python3 patch.py <site dir>
Safe to run again: every inserted block is replaced, never duplicated.
Adds: motion.css/motion.js, meta description, lang, SEO text, photo blocks,
and the compact "Подход" block on the home pages.
"""
import html
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from content import DESC, GALLERY, MANAGER, PAGES, SEO, TEAM  # noqa: E402

PAD = 'max-width:1560px;margin:0 auto;padding:0 clamp(16px,4vw,64px)'
CHIP = ("display:inline-flex;align-self:flex-start;align-items:center;min-height:30px;padding:0 14px;border-radius:999px;"
        "background:var(--c-f6f6fd);box-shadow:inset 0 0 0 1px var(--c-b6b9e6);font:700 11px/1 'Onest',sans-serif;"
        "letter-spacing:1.6px;text-transform:uppercase;color:var(--c-3a46b8)")
H2 = "margin:0;font:400 clamp(29px,3.96vw,55px)/1.04 'Onest',sans-serif;letter-spacing:-0.035em;text-wrap:balance;padding-bottom:.08em"
LEAD = "margin:0;max-width:640px;font:500 18px/28px 'Onest',sans-serif;color:var(--c-3b467e);text-wrap:pretty"


def section(kind, label, inner, pad='padding:clamp(44px,5.5vw,76px) 0'):
    return (f'<section data-lv-added="{kind}" data-screen-label="{label}" style="position:relative;{pad}">\n'
            f'  <div style="{PAD};display:flex;flex-direction:column;gap:22px">{inner}</div>\n</section>\n')


def head(chip, h2, lead=None):
    out = f'<div data-r style="{CHIP}">{chip}</div><h2 data-clip style="{H2}">{h2}</h2>'
    if lead:
        out += f'<p data-r data-d="100" style="{LEAD}">{lead}</p>'
    return out


SITE = Path('.')


def photo(slot_id, placeholder, ratio='4/5'):
    # a file assets/people/<slot id>.jpg (or .png/.webp) in the site dir fills the slot
    src = next((f'assets/people/{slot_id}{ext}' for ext in ('.jpg', '.png', '.webp')
                if (SITE / 'assets' / 'people' / f'{slot_id}{ext}').exists()), None)
    src_attr = f' src="{src}"' if src else ''
    return ('<div style="padding:6px;border-radius:28px;background:rgba(var(--r-f6f6fd),.5);box-shadow:inset 0 0 0 1px var(--c-b6b9e6)">'
            f'<div style="position:relative;aspect-ratio:{ratio};border-radius:22px;background:var(--c-c6c8ef);overflow:hidden">'
            f'<image-slot id="{slot_id}" shape="rect" placeholder="{placeholder}"{src_attr}></image-slot></div></div>')


def team_block(page):
    _, chip, h2, lead, people = TEAM[page]
    cards = ''.join(
        '<div data-s style="display:flex;flex-direction:column;gap:16px;min-width:0">' + photo(sid, ph) +
        '<div style="display:flex;flex-direction:column;gap:4px;padding:0 6px">'
        f'<span style="font:500 14px/20px \'Onest\',sans-serif;color:var(--c-3a46b8)">{role}</span>'
        '<span style="font:700 21px/1.25 \'Onest\',sans-serif">Фамилия Имя</span></div></div>'
        for sid, ph, role in people)
    grid = f'<div data-stagger style="margin-top:14px;display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,240px),1fr));gap:28px">{cards}</div>'
    return section('team', 'Команда проекта', head(chip, h2, lead) + grid)


def gallery_block():
    _, chip, h2, items = GALLERY
    cards = ''.join(
        '<div data-s style="display:flex;flex-direction:column;gap:14px;min-width:0">' + photo(sid, ph, '4/3') +
        f'<span style="padding:0 6px;font:600 17px/1.3 \'Onest\',sans-serif">{cap}</span></div>'
        for sid, ph, cap in items)
    grid = f'<div data-stagger style="margin-top:14px;display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:28px">{cards}</div>'
    return section('gallery', 'Офис', head(chip, h2) + grid)


def manager_block():
    sid, ph, role, text = MANAGER
    btn = ("display:inline-flex;align-items:center;gap:10px;min-height:52px;padding:0 24px;border-radius:999px;"
           "font:700 16px/1 'Onest',sans-serif;text-decoration:none;transition:background-color .3s,color .3s")
    card = ('<div data-r style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:clamp(24px,4vw,56px);'
            'align-items:center;padding:clamp(16px,2vw,24px);border-radius:36px;background:var(--c-ececfb);box-shadow:inset 0 0 0 1px var(--c-b6b9e6)">'
            f'<div style="max-width:340px;width:100%">{photo(sid, ph)}</div>'
            '<div style="display:flex;flex-direction:column;gap:14px;min-width:0;padding:0 clamp(4px,1vw,12px) 8px">'
            f'<span style="font:500 15px/20px \'Onest\',sans-serif;color:var(--c-3a46b8)">{role}</span>'
            '<span style="font:800 clamp(26px,2.6vw,36px)/1.1 \'Onest\',sans-serif;letter-spacing:-0.02em">Фамилия Имя</span>'
            f'<p style="margin:0;max-width:460px;font:400 17px/27px \'Onest\',sans-serif;color:var(--c-3b467e)">{text}</p>'
            '<div style="display:flex;flex-wrap:wrap;gap:10px;margin-top:8px">'
            f'<a href="tel:+74959736699" style="{btn};background:var(--c-061e70);color:var(--c-ffffff)" style-hover="background:var(--c-3a46b8)">+7 (495) 973-66-99</a>'
            f'<a href="https://t.me/Uspehms" style="{btn};background:var(--c-f6f6fd);color:var(--c-061e70);box-shadow:inset 0 0 0 1px var(--c-b6b9e6)" style-hover="background:var(--c-ffffff)">Написать в Telegram</a>'
            '</div></div></div>')
    return section('manager', 'Менеджер', head('Ваш менеджер', 'С вами <b style="font-weight:800">свяжется</b>') + card)


def seo_block(page):
    chip, h2, parts = SEO[page]
    body = ''
    for h3, p in parts:
        if h3:
            body += f'<h3 style="margin:0 0 10px;break-after:avoid;font:800 20px/1.3 \'Onest\',sans-serif;letter-spacing:-0.01em">{h3}</h3>'
        body += f'<p style="margin:0 0 22px;font:400 17px/28px \'Onest\',sans-serif;color:var(--c-3b467e);text-wrap:pretty">{p}</p>'
    inner = (f'<div data-r data-lv-seo style="display:flex;flex-direction:column;gap:22px;padding:clamp(28px,4vw,56px);'
             'border-radius:clamp(28px,3vw,40px);background:rgba(var(--r-f6f6fd),.55);box-shadow:inset 0 0 0 1px var(--c-b6b9e6)">'
             f'<div style="{CHIP}">{chip}</div><h2 style="{H2};max-width:24ch">{h2}</h2>'
             f'<div style="columns:2 340px;column-gap:clamp(32px,4vw,72px);margin-top:6px">{body}</div></div>')
    return section('seo', 'SEO-текст', inner)


APPROACH = '''<section id="approach" data-theme="dark" data-screen-label="02 Подход" style="position:relative;color:var(--c-f2f2fd)">
  <div data-pin data-approach-pin style="position:relative;height:175vh">
    <div data-approach-stick style="position:sticky;top:0;height:100vh;overflow:hidden;display:flex;align-items:center">
      <div data-pin-orb style="position:absolute;left:86%;top:58%;width:74vmin;height:74vmin;border-radius:50%;background:radial-gradient(circle at 34% 28%,var(--g-dfe3ff) 0%,var(--g-7a88f4) 26%,var(--g-3d4aa8) 58%,var(--g-0b1450) 100%);transform:translate3d(-50%,-50%,0) scale(.6);opacity:.6;pointer-events:none"></div>
      <div style="position:relative;max-width:1560px;width:100%;margin:0 auto;padding:clamp(76px,10vh,104px) clamp(16px,4vw,64px) clamp(16px,3vh,36px);display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:clamp(28px,4.5vw,88px);align-items:center">
        <div style="display:flex;flex-direction:column;gap:clamp(12px,2.2vh,22px);min-width:0">
          <div style="font:700 12px/16px 'Onest',sans-serif;letter-spacing:1.2px;text-transform:uppercase;color:var(--c-a3b0fa)">Подход</div>
          <h2 data-scrub style="margin:0;max-width:21ch;font:400 clamp(24px,min(3.1vw,5.4vh),44px)/1.1 'Onest',sans-serif;letter-spacing:-0.035em">
            <span data-sw style="font-weight:800">Стабильный</span> <span data-sw style="font-weight:800">поток</span> <span data-sw style="font-weight:800">заявок</span> <span data-sw>без</span> <span data-sw>Ваших</span> <span data-sw>усилий!</span> <span data-sw>Ваша</span> <span data-sw>задача</span> <span data-sw>—</span> <span data-sw>только</span> <span data-sw>закрывать</span> <span data-sw>сделки</span>
          </h2>
          <p data-pin-tail style="margin:0;max-width:540px;font:500 clamp(15px,min(1.3vw,2.3vh),18px)/1.5 'Onest',sans-serif;color:var(--c-b7bce8)"><a href="OneTen%20Process.dc.html" style="color:var(--c-f2f2fd);text-decoration:underline;text-decoration-color:var(--c-7a88f4);text-underline-offset:5px" style-hover="color:var(--c-a3b0fa)">Вам не нужно нанимать штат, учиться или контролировать процесс — просто получайте Клиентов. Как мы работаем →</a></p>
          <p data-r style="margin:clamp(4px,1.2vh,12px) 0 0;max-width:600px;font:400 clamp(16px,min(1.45vw,2.5vh),21px)/1.45 'Onest',sans-serif;color:var(--c-f2f2fd);text-wrap:pretty">Если Вы уже запускали SEO, рекламу или работали с маркетинговыми агентствами без результата, то с высокой вероятностью проблема была не в инструментах.</p>
          <p data-r data-d="120" style="margin:0;max-width:560px;font:400 clamp(14px,min(1.1vw,2vh),16px)/1.6 'Onest',sans-serif;color:var(--c-b7bce8);text-wrap:pretty">Большинство подрядчиков выполняют набор работ, но не строят стратегию привлечения клиентов. Поэтому бизнес получает отчёты, позиции и трафик, но не получает стабильный поток заявок.</p>
        </div>
        <div style="display:flex;flex-direction:column;gap:clamp(14px,2.2vh,22px);min-width:0;max-width:560px;justify-self:end;width:100%">
          <div style="position:relative">
            <div data-draw style="position:absolute;left:33px;top:34px;bottom:34px;width:2px;background:var(--c-7a88f4)"></div>
            <div data-stagger style="position:relative;display:flex;flex-direction:column;gap:clamp(8px,1.4vh,12px)">
              <div data-s style="display:flex;align-items:center;gap:16px;padding:10px 22px 10px 10px;border-radius:28px;background:var(--c-142063);border:1px solid var(--c-26337f)">
                <span style="display:grid;place-items:center;width:48px;height:48px;border-radius:999px;background:var(--c-1b2580);font:800 16px/1 'Onest',sans-serif;color:var(--c-a3b0fa);flex:none">01</span>
                <span style="font:500 clamp(16px,min(1.3vw,2.3vh),19px)/1.3 'Onest',sans-serif">Стратегия роста</span>
              </div>
              <div data-s style="display:flex;align-items:center;gap:16px;padding:10px 22px 10px 10px;border-radius:28px;background:var(--c-142063);border:1px solid var(--c-26337f)">
                <span style="display:grid;place-items:center;width:48px;height:48px;border-radius:999px;background:var(--c-1b2580);font:800 16px/1 'Onest',sans-serif;color:var(--c-a3b0fa);flex:none">02</span>
                <span style="font:500 clamp(16px,min(1.3vw,2.3vh),19px)/1.3 'Onest',sans-serif">Точки роста бизнеса</span>
              </div>
              <div data-s style="display:flex;align-items:center;gap:16px;padding:10px 22px 10px 10px;border-radius:28px;background:var(--c-d8d8f4);color:var(--c-061e70);box-shadow:0 30px 60px -20px rgba(var(--r-7a88f4),.45)">
                <span style="display:grid;place-items:center;width:48px;height:48px;border-radius:999px;background:var(--c-5b6ae0);font:800 16px/1 'Onest',sans-serif;color:var(--c-ffffff);flex:none">03</span>
                <span style="font:500 clamp(16px,min(1.3vw,2.3vh),19px)/1.3 'Onest',sans-serif">Инструменты продвижения</span>
              </div>
            </div>
          </div>
          <p data-r data-d="200" style="margin:0;font:400 clamp(14px,min(1.1vw,2vh),16px)/1.6 'Onest',sans-serif;color:var(--c-b7bce8);text-wrap:pretty">Мы начинаем работу с разработки стратегии роста, определяем точки роста бизнеса и только после этого подключаем инструменты продвижения.</p>
        </div>
      </div>
    </div>
  </div>
</section>
'''


def section_start(s, label):
    i = s.find(f'data-screen-label="{label}"')
    if i < 0:
        raise SystemExit(f'no section {label}')
    return s.rfind('<section', 0, i)


def insert_before(s, pos, block):
    return s[:pos] + block + s[pos:]


def strip_added(s):
    while True:
        i = s.find('<section data-lv-added="')
        if i < 0:
            return s
        j = s.find('</section>', i) + len('</section>\n')
        s = s[:i] + s[j:]


def put_tag(s, tag_id, tag, content, after_id, after_tag):
    """Insert or replace <tag id=tag_id>content</tag> right after the element with id=after_id."""
    new = f'<{tag} id="{tag_id}">{content}</{tag}>'
    m = re.search(rf'<{tag} id="{tag_id}">.*?</{tag}>', s, re.S)
    if m:
        return s[:m.start()] + new + s[m.end():]
    a = s.find(f'<{after_tag} id="{after_id}"')
    b = s.find(f'</{after_tag}>', a) + len(f'</{after_tag}>')
    return s[:b] + new + s[b:]


def patch(path, page, css, js):
    s = path.read_text(encoding='utf-8')
    s = s.replace('<html>', '<html lang="ru">', 1)
    meta = f'<meta name="description" content="{html.escape(DESC[page], quote=True)}">'
    if '<meta name="description"' in s[:s.find('</head>')]:
        s = re.sub(r'<meta name="description" content="[^"]*">', meta, s, count=1)
    else:
        s = s.replace('<meta name="viewport" content="width=device-width, initial-scale=1">',
                      '<meta name="viewport" content="width=device-width, initial-scale=1">\n' + meta, 1)
    s = put_tag(s, 'lv-css2', 'style', css, 'lv-css', 'style')
    s = put_tag(s, 'lv-js2', 'script', js, 'lv-js', 'script')

    s = strip_added(s)
    if page == 'home':
        a = s.find('<section id="approach"')
        b = s.find('<section', a + 10)
        s = s[:a] + APPROACH + '\n  ' + s[b:]
    if page in TEAM:
        s = insert_before(s, section_start(s, TEAM[page][0]), team_block(page))
    if page == 'about':
        s = insert_before(s, section_start(s, GALLERY[0]), gallery_block())
    contact = s.find('<section id="contact"')
    blocks = (manager_block() if page == 'contacts' else '') + seo_block(page)
    s = insert_before(s, contact, blocks)
    path.write_text(s, encoding='utf-8')

    # every theme variable used must exist on this page
    themes = s[s.find('<style id="lv-themes">'):s.find('</style>', s.find('<style id="lv-themes">'))]
    used = set(re.findall(r'var\(--([cgr])-([0-9a-f]{6})\)', css + js + team_and_seo_text(s)))
    used |= {('r', h) for h in re.findall(r'rgba\(var\(--r-([0-9a-f]{6})\)', css + js)}
    missing = sorted(f'--{k}-{h}' for k, h in used if f'--{k}-{h}:' not in themes)
    return missing


def team_and_seo_text(s):
    return ''.join(m.group(0) for m in re.finditer(r'<section data-lv-added=.*?</section>', s, re.S))


def main():
    global SITE
    site = SITE = Path(sys.argv[1])
    css = (HERE / 'motion.css').read_text(encoding='utf-8')
    js = (HERE / 'motion.js').read_text(encoding='utf-8')
    for f in sorted(site.glob('OneTen *.dc.html')):
        page = PAGES[f.name[len('OneTen '):-len('.dc.html')]]
        miss = patch(f, page, css, js)
        print(f'{f.name}: ok' + (f'  MISSING VARS {miss}' if miss else ''))


if __name__ == '__main__':
    main()
