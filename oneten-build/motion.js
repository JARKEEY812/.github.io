/* OneTen motion layer v5. Adds scroll and touch motion on top of lv-js.
   Every pass is idempotent: it marks what it touched and skips it next time. */
(() => {
  const RM = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const FINE = matchMedia('(hover: hover) and (pointer: fine)').matches;
  const CHECK = 'M5 12.5l4.2 4.2L19 7';
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const transparent = c => c === 'transparent' || /rgba\(.*,\s*0\)$/.test(c);
  const isRound = (n, min, max) => {
    const w = n.offsetWidth, h = n.offsetHeight;
    return w >= min && w <= max && Math.abs(w - h) < 3 && parseFloat(getComputedStyle(n).borderTopLeftRadius) >= w / 2 - 1;
  };
  const once = (cb, opts) => {
    if (RM || !('IntersectionObserver' in window)) return el => cb(el);
    const io = new IntersectionObserver(es => es.filter(e => e.isIntersecting)
      .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)
      .forEach((e, i) => { io.unobserve(e.target); cb(e.target, i); }), opts);
    return el => io.observe(el);
  };

  /* 1. touch: focus the card in the middle band of the screen */
  const touchIO = !FINE && !RM && 'IntersectionObserver' in window &&
    new IntersectionObserver(es => es.forEach(e => e.target.classList.toggle('lv-touch-on', e.isIntersecting)),
      { rootMargin: '-42% 0px -42% 0px' });
  function passTouch() {
    if (!touchIO) return;
    $$('[data-dc-tpl],[data-card],[data-tilt]').forEach(n => {
      if (n.dataset.lvt || n.closest('.lv-tcard') || n.closest('nav,header,form,footer')) return;
      const w = n.offsetWidth, h = n.offsetHeight;
      if (w < 140 || h < 100 || h > 720) return;
      const cs = getComputedStyle(n);
      if (parseFloat(cs.borderTopLeftRadius) < 14) return;
      if (transparent(cs.backgroundColor) && cs.backgroundImage === 'none') return;
      if (cs.position === 'fixed' || cs.position === 'sticky') return;
      n.dataset.lvt = '1';
      n.classList.add('lv-tcard');
      touchIO.observe(n);
    });
  }

  /* 2. steps: round badges 01..09 light up in reading order, a vertical line fills */
  let steps = [], lines = [];
  function passSteps() {
    $$('span,div').forEach(b => {
      if (b.dataset.lvn || b.children.length || !/^0[1-9]$/.test(b.textContent.trim())) return;
      if (!isRound(b, 36, 64) || b.closest('nav,footer')) return;
      b.dataset.lvn = '1';
      b.classList.add('lv-num');
      steps.push(b);
      // a 2-3px absolute line next to the list
      let box = b.parentElement;
      for (let i = 0; i < 5 && box; i++, box = box.parentElement) {
        const ln = [...box.children].find(c => c !== b && c.offsetWidth <= 3 && c.offsetHeight > 120 && getComputedStyle(c).position === 'absolute');
        if (ln) {
          if (!ln.dataset.lvl && !ln.querySelector('[data-sfy]')) {
            ln.dataset.lvl = '1';
            if (getComputedStyle(ln).overflow === 'visible') ln.style.overflow = 'hidden';
            const f = document.createElement('span'); f.className = 'lv-line-fill'; ln.appendChild(f);
            lines.push({ ln, f });
          }
          break;
        }
      }
    });
  }

  /* 4. timeline years */
  let years = [];
  function passYears() {
    $$('[data-screen-label="История"] [data-par]').forEach(y => {
      if (y.dataset.lvy || !/\d{4}|Сегодня/.test(y.textContent)) return;
      y.dataset.lvy = '1'; y.classList.add('lv-year'); years.push(y);
    });
  }

  let ticking = false;
  function onScroll() {
    if (ticking) return; ticking = true;
    requestAnimationFrame(() => {
      ticking = false;
      const line = innerHeight * 0.62;
      steps.forEach(b => { const r = b.getBoundingClientRect(); b.classList.toggle('lv-num-on', r.height > 0 && r.top + r.height / 2 < line); });
      lines.forEach(({ ln, f }) => { const r = ln.getBoundingClientRect(); const p = Math.min(1, Math.max(0, (line - r.top) / Math.max(1, r.height))); f.style.setProperty('--lp', p.toFixed(3)); });
      years.forEach(y => { const r = y.getBoundingClientRect(); y.classList.toggle('lv-year-on', r.top + r.height / 2 < innerHeight * 0.6 && r.bottom > innerHeight * 0.15); });
    });
  }

  /* 3. comparison: cross rows and check rows come in pairs */
  const cmpObs = once(grid => {
    const rows = grid.__lvRows || [];
    rows.forEach(r => r.classList.add('lv-in'));
  }, { threshold: 0.2 });
  function passCompare() {
    $$('section').forEach(sec => {
      if (sec.dataset.lvcmp) return;
      const cross = $$('span', sec).filter(s => !s.children.length && s.textContent.trim() === '×' && isRound(s, 20, 36));
      if (cross.length < 2) return;
      const checks = $$('svg', sec).filter(v => { const p = v.querySelector('path'); return p && p.getAttribute('d') === CHECK; }).map(v => v.closest('span'));
      const rowOf = b => b && b.parentElement;
      const left = cross.map(rowOf), right = checks.map(rowOf).filter(Boolean);
      if (!right.length) return;
      sec.dataset.lvcmp = '1';
      const rows = [];
      const n = Math.max(left.length, right.length);
      for (let i = 0; i < n; i++) {
        [[left[i], '-14px', 0], [right[i], '14px', 140]].forEach(([r, dx, extra]) => {
          if (!r) return;
          r.classList.add('lv-cmp-row');
          r.style.setProperty('--cx', dx);
          r.style.setProperty('--cd', (i * 240 + extra) + 'ms');
          r.querySelectorAll('svg').forEach(v => { v.classList.add('lv-chk', 'lv-cmp-chk'); v.style.setProperty('--kd', (i * 240 + extra + 200) + 'ms'); });
          rows.push(r);
        });
      }
      const grid = left[0].closest('[data-stagger]') || sec;
      // the check marks inside comparison rows draw together with their row
      const marks = rows.flatMap(r => $$('.lv-cmp-chk', r));
      grid.__lvRows = rows.concat(marks);
      cmpObs(grid);
    });
  }

  /* 6. every other check mark draws when it scrolls in */
  const chkObs = once((v, i) => {
    v.style.setProperty('--kd', (i * 130) + 'ms');
    v.classList.add('lv-in');
    const b = v.__lvBadge; if (b) { b.style.setProperty('--kd', (i * 130) + 'ms'); b.classList.add('lv-in'); }
  }, { threshold: 0.9 });
  function passChecks() {
    $$('svg').forEach(v => {
      if (v.dataset.lvk2 || v.classList.contains('lv-cmp-chk')) return;
      const p = v.querySelector('path');
      if (!p || p.getAttribute('d') !== CHECK || v.closest('.lv-ill,.lv-sw')) return;
      v.dataset.lvk2 = '1';
      v.classList.add('lv-chk');
      const b = v.closest('span');
      if (b && b !== v && isRound(b, 18, 48)) { b.classList.add('lv-chk-b'); v.__lvBadge = b; }
      chkObs(v);
    });
  }

  /* 5. niche icons pop in one after another */
  const icoObs = once((card, i) => {
    card.querySelectorAll('.lv-nico').forEach(ic => { ic.style.setProperty('--nd', (i * 80) + 'ms'); ic.classList.add('lv-in'); });
  }, { threshold: 0.4 });
  function passNiches() {
    $$('[data-tilt],[data-s]').forEach(card => {
      if (card.dataset.lvni) return;
      const ic = card.querySelector('svg[viewBox="0 0 256 256"]');
      if (!ic || card.offsetHeight > 360 || card.closest('nav,footer')) return;
      // cards in a sideways slider may never cross the viewport vertically: leave them as is
      const r = card.getBoundingClientRect();
      if (r.left < -2 || r.right > innerWidth + 2) { card.dataset.lvni = '1'; return; }
      card.dataset.lvni = '1';
      ic.classList.add('lv-nico');
      icoObs(card);
    });
  }

  /* 7. plain numbers in report and result cards count up */
  const NUM = /^([+−-]?)(\d{1,3}(?:[\s  ]?\d{3})*)(\s?(?:₽|%))?$/;
  const cntObs = once(el => {
    const m = el.__lvNum; if (!m) return;
    const [sign, digits, unit] = m, to = +digits.replace(/\D/g, ''), sep = (digits.match(/[\s  ]/) || [' '])[0];
    const fmt = v => sign + String(Math.round(v)).replace(/\B(?=(\d{3})+(?!\d))/g, to >= 10000 || /\D/.test(digits) ? sep : '') + (unit || '');
    const t0 = performance.now(), dur = 1400;
    const step = now => { const k = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - k, 3); el.textContent = fmt(to * e); if (k < 1) requestAnimationFrame(step); else el.textContent = el.__lvOrig; };
    requestAnimationFrame(step);
  }, { threshold: 0.6 });
  function passCounts() {
    $$('[data-screen-label="Отчёт"] span,[data-screen-label="Результат"] span,[data-screen-label="Достижения"] span').forEach(s => {
      if (s.dataset.lvcn || s.children.length || s.closest('[data-count]') || s.hasAttribute('data-count')) return;
      const t = s.textContent.trim(), m = t.match(NUM);
      if (!m || parseFloat(getComputedStyle(s).fontSize) < 20) return;
      const n = +m[2].replace(/\D/g, '');
      if (n < 2 || (n >= 1990 && n <= 2035 && !m[1] && !m[3])) return; // skip years
      s.dataset.lvcn = '1';
      s.__lvNum = [m[1], m[2], m[3]]; s.__lvOrig = t;
      if (!RM) { s.style.fontVariantNumeric = 'tabular-nums'; s.textContent = m[1] + '0' + (m[3] || ''); }
      cntObs(s);
    });
  }

  /* 8. FAQ: outline the open card */
  function syncFaq() {
    $$('#faq [data-s]').forEach(c => {
      c.classList.add('lv-faq');
      const g = [...c.children].find(x => x.tagName === 'DIV' && /grid-template-rows/.test(x.getAttribute('style') || ''));
      c.classList.toggle('lv-faq-open', !!g && /(^|[^0])1fr/.test(g.style.gridTemplateRows));
    });
  }

  /* 9. covers zoom on hover, horizontal lists drag with the mouse */
  function passCovers() {
    $$('[data-card]').forEach(c => {
      if (c.dataset.lvcv) return; c.dataset.lvcv = '1';
      $$('*', c).forEach(n => { if (n.offsetWidth >= 90 && /radial-gradient/.test(getComputedStyle(n).backgroundImage)) n.classList.add('lv-cov'); });
    });
  }
  function passDrag() {
    if (!FINE) return;
    $$('div').forEach(d => {
      if (d.dataset.lvdr) return;
      const cs = getComputedStyle(d);
      if (!/(auto|scroll)/.test(cs.overflowX) || cs.position === 'fixed' || d.scrollWidth <= d.clientWidth + 40 || d.offsetHeight < 120) return;
      d.dataset.lvdr = '1'; d.classList.add('lv-drag');
      let x0 = 0, s0 = 0, on = false, moved = 0;
      d.addEventListener('pointerdown', e => { if (e.pointerType !== 'mouse' || e.button) return; on = true; moved = 0; x0 = e.clientX; s0 = d.scrollLeft; });
      addEventListener('pointermove', e => { if (!on) return; const dx = e.clientX - x0; moved = Math.max(moved, Math.abs(dx)); if (moved > 6) { d.classList.add('lv-dragging'); d.scrollLeft = s0 - dx; } });
      addEventListener('pointerup', () => { if (!on) return; on = false; setTimeout(() => d.classList.remove('lv-dragging'), 0); });
      d.addEventListener('click', e => { if (moved > 6) { e.preventDefault(); e.stopPropagation(); } }, true);
    });
  }

  /* 10. contacts map and 11. empty photo slots */
  const MAP = `<svg viewBox="0 0 600 420" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <rect class="m-block" x="0" y="0" width="600" height="420" style="opacity:.55"/>
    <path class="m-river" d="M-20 330 C120 280 200 360 320 300 S520 200 640 240"/>
    <rect class="m-park" x="40" y="40" width="150" height="110" rx="18"/><rect class="m-park" x="430" y="290" width="140" height="100" rx="18"/>
    <path class="m-road" d="M0 190H600M250 0V420M0 60L600 380"/>
    <path class="m-road2" d="M0 120H600M0 260H600M120 0V420M380 0V420M500 0V420M60 420L420 0"/>
    <g transform="translate(300 200)">
      <circle class="m-ring" r="22"/><circle class="m-ring" r="22" style="animation-delay:1.3s"/>
      <g class="m-drop"><path class="m-pin" d="M0 0c-18-22-28-36-28-50a28 28 0 0 1 56 0c0 14-10 28-28 50z"/><circle class="m-dot" cx="0" cy="-50" r="10"/></g>
      <g transform="translate(36 -92)"><rect class="m-tag" width="150" height="42" rx="21"/><text class="m-label" x="20" y="26">OneTen · Москва</text></g>
    </g></svg>`;
  function passSlots() {
    $$('image-slot').forEach(sl => {
      const box = sl.parentElement; if (!box) return;
      const empty = !sl.getAttribute('src');
      if (sl.id === 'contacts-map') {
        let m = box.querySelector(':scope > .lv-map');
        if (empty && !m) { if (getComputedStyle(box).position === 'static') box.style.position = 'relative'; m = document.createElement('div'); m.className = 'lv-map'; m.innerHTML = MAP; box.appendChild(m); }
        if (!empty && m) m.remove();
        return;
      }
      box.classList.toggle('lv-ph', empty && !RM);
    });
  }

  function run() {
    passTouch(); passSteps(); passYears(); passCompare(); passChecks(); passNiches();
    passCounts(); passCovers(); passDrag(); passSlots(); syncFaq(); onScroll();
  }
  function start() {
    if (!document.querySelector('h1')) return void setTimeout(start, 250);
    setTimeout(run, 700);
    addEventListener('scroll', onScroll, { passive: true });
    addEventListener('resize', onScroll, { passive: true });
    document.addEventListener('click', e => { if (e.target instanceof Element && e.target.closest('#faq')) setTimeout(syncFaq, 30); });
    let t;
    new MutationObserver(() => { clearTimeout(t); t = setTimeout(run, 520); })
      .observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['src'] });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
