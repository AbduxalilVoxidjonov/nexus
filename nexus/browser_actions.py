"""Brauzer boshqaruvi (Safari / Google Chrome) — AppleScript + sahifa ichidagi JavaScript.

Barcha JavaScript kodi AppleScript satr literali ichida yuboriladi, shuning uchun
`js_to_applescript()` orqali escaping qilinadi (`\\` → `\\\\`, `"` → `\\"`).
Safari uchun Develop → "Allow JavaScript from Apple Events", Chrome uchun
View → Developer → "Allow JavaScript from Apple Events" yoqilgan bo'lishi shart.
"""

from __future__ import annotations

import json
import re
from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import quote_plus

from nexus.macos_actions import _as_str, run_applescript

Result = tuple[bool, str]
Runner = Callable[[str], Awaitable[Result]]

BROWSERS = {
    "safari": "Safari",
    "chrome": "Google Chrome",
}

SEARCH_ENGINES = {
    "google": "https://www.google.com/search?q={q}",
    "duckduckgo": "https://duckduckgo.com/?q={q}",
    "bing": "https://www.bing.com/search?q={q}",
    "youtube": "https://www.youtube.com/results?search_query={q}",
}

JS_PERMISSION_HINT = (
    "Brauzerda Apple Events orqali JavaScript o'chirilgan. Safari: Develop menyusi → "
    '"Allow JavaScript from Apple Events"; Chrome: View → Developer → '
    '"Allow JavaScript from Apple Events" ni yoqing.'
)


# ---------------------------------------------------------------------------
# Yordamchilar
# ---------------------------------------------------------------------------
def js_to_applescript(js: str) -> str:
    """JS matnini AppleScript qo'shtirnoqli literal ichiga qo'yish uchun escaping (qo'shtirnoqsiz)."""
    return js.replace("\\", "\\\\").replace('"', '\\"')


def normalize_browser(browser: str | None) -> str | None:
    b = (browser or "").strip().lower()
    if b in ("", "default"):
        return None
    if b in ("google chrome", "chrome", "gc"):
        return "chrome"
    if b == "safari":
        return "safari"
    return None


def app_name(browser: str) -> str:
    return BROWSERS[browser]


def normalize_url(url: str) -> str:
    u = (url or "").strip()
    if not u:
        return "about:blank"
    if re.match(r"^[a-z][a-z0-9+.-]*://", u, re.IGNORECASE) or u.startswith(("about:", "file:", "mailto:")):
        return u
    if " " in u or ("." not in u and "localhost" not in u):
        return SEARCH_ENGINES["google"].format(q=quote_plus(u))
    return "https://" + u


def _js_error(out: str) -> str:
    if "JavaScript" in out or "javascript" in out:
        return JS_PERMISSION_HINT + f" ({out})"
    return out


def _parse_json(out: str) -> Any:
    try:
        return json.loads(out)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Tab / oyna boshqaruvi
# ---------------------------------------------------------------------------
class BrowserController:
    """Tab ochish/yopish, URL olish, tab almashtirish, reload, ro'yxat."""

    def __init__(self, run: Runner | None = None) -> None:
        self._run: Runner = run or run_applescript

    def _check(self, browser: str) -> str | None:
        return None if browser in BROWSERS else f"Noma'lum brauzer: {browser} (safari yoki chrome)"

    async def open_url(self, browser: str, url: str) -> Result:
        if (err := self._check(browser)) is not None:
            return False, err
        target = _as_str(normalize_url(url))
        if browser == "safari":
            script = (
                'tell application "Safari"\n'
                "  activate\n"
                "  if (count of windows) = 0 then\n"
                f"    make new document with properties {{URL:{target}}}\n"
                "  else\n"
                f"    tell front window to set current tab to (make new tab with properties {{URL:{target}}})\n"
                "  end if\n"
                "end tell"
            )
        else:
            script = (
                'tell application "Google Chrome"\n'
                "  activate\n"
                "  if (count of windows) = 0 then make new window\n"
                f"  tell front window to make new tab with properties {{URL:{target}}}\n"
                "end tell"
            )
        ok, out = await self._run(script)
        if not ok:
            return False, f"{app_name(browser)}: sahifani ochib bo'lmadi: {out}"
        return True, f"{app_name(browser)} da ochildi: {normalize_url(url)}"

    async def close_current_tab(self, browser: str) -> Result:
        if (err := self._check(browser)) is not None:
            return False, err
        if browser == "safari":
            script = 'tell application "Safari" to close current tab of front window'
        else:
            script = 'tell application "Google Chrome" to close active tab of front window'
        ok, out = await self._run(script)
        return (True, "Joriy tab yopildi") if ok else (False, f"Tabni yopib bo'lmadi: {out}")

    async def current_page(self, browser: str) -> Result:
        if (err := self._check(browser)) is not None:
            return False, err
        if browser == "safari":
            script = (
                'tell application "Safari"\n'
                "  set t to current tab of front window\n"
                '  return (name of t) & "\\n" & (URL of t)\n'
                "end tell"
            )
        else:
            script = (
                'tell application "Google Chrome"\n'
                "  set t to active tab of front window\n"
                '  return (title of t) & "\\n" & (URL of t)\n'
                "end tell"
            )
        ok, out = await self._run(script)
        if not ok:
            return False, f"Joriy sahifani aniqlab bo'lmadi: {out}"
        title, _, url = out.partition("\n")
        return True, f"{title.strip()} — {url.strip()}"

    async def current_url(self, browser: str) -> Result:
        ok, out = await self.current_page(browser)
        if not ok:
            return ok, out
        return True, out.rsplit(" — ", 1)[-1]

    async def switch_to_tab(self, browser: str, keyword: str) -> Result:
        if (err := self._check(browser)) is not None:
            return False, err
        kw = _as_str((keyword or "").strip())
        if kw == '""':
            return False, "Qidiruv so'zi bo'sh"
        if browser == "safari":
            script = (
                'tell application "Safari"\n'
                f"  set kw to {kw}\n"
                "  repeat with w in windows\n"
                "    repeat with t in tabs of w\n"
                "      if (name of t contains kw) or (URL of t contains kw) then\n"
                "        set current tab of w to t\n"
                "        set index of w to 1\n"
                "        activate\n"
                "        return name of t\n"
                "      end if\n"
                "    end repeat\n"
                "  end repeat\n"
                '  return ""\n'
                "end tell"
            )
        else:
            script = (
                'tell application "Google Chrome"\n'
                f"  set kw to {kw}\n"
                "  repeat with w in windows\n"
                "    set i to 0\n"
                "    repeat with t in tabs of w\n"
                "      set i to i + 1\n"
                "      if (title of t contains kw) or (URL of t contains kw) then\n"
                "        set active tab index of w to i\n"
                "        set index of w to 1\n"
                "        activate\n"
                "        return title of t\n"
                "      end if\n"
                "    end repeat\n"
                "  end repeat\n"
                '  return ""\n'
                "end tell"
            )
        ok, out = await self._run(script)
        if not ok:
            return False, f"Tab almashtirib bo'lmadi: {out}"
        if not out.strip():
            return False, f"'{keyword}' so'ziga mos tab topilmadi"
        return True, f"Tabga o'tildi: {out.strip()}"

    async def reload(self, browser: str) -> Result:
        if (err := self._check(browser)) is not None:
            return False, err
        if browser == "safari":
            script = (
                'tell application "Safari"\n'
                "  set t to current tab of front window\n"
                "  set URL of t to (URL of t)\n"
                "end tell"
            )
        else:
            script = 'tell application "Google Chrome" to reload active tab of front window'
        ok, out = await self._run(script)
        return (True, "Sahifa yangilandi") if ok else (False, f"Yangilab bo'lmadi: {out}")

    async def list_tabs(self, browser: str, limit: int = 30) -> Result:
        if (err := self._check(browser)) is not None:
            return False, err
        title_prop = "name" if browser == "safari" else "title"
        script = (
            f'tell application "{app_name(browser)}"\n'
            "  set acc to {}\n"
            "  set n to 0\n"
            "  repeat with w in windows\n"
            "    repeat with t in tabs of w\n"
            "      set n to n + 1\n"
            f"      if n > {int(limit)} then exit repeat\n"
            f'      set end of acc to (n as text) & ". " & ({title_prop} of t) & " — " & (URL of t)\n'
            "    end repeat\n"
            "  end repeat\n"
            '  set AppleScript\'s text item delimiters to "\\n"\n'
            "  return acc as text\n"
            "end tell"
        )
        ok, out = await self._run(script)
        if not ok:
            return False, f"Tablar ro'yxatini olib bo'lmadi: {out}"
        return True, out.strip() or "Ochiq tablar yo'q"

    async def set_current_url(self, browser: str, url: str) -> Result:
        """Joriy tabda URL ni almashtiradi (yangi tab ochmasdan)."""
        if (err := self._check(browser)) is not None:
            return False, err
        target = _as_str(normalize_url(url))
        tab = "current tab" if browser == "safari" else "active tab"
        script = f'tell application "{app_name(browser)}" to set URL of {tab} of front window to {target}'
        ok, out = await self._run(script)
        return (True, f"O'tildi: {normalize_url(url)}") if ok else (False, f"O'tib bo'lmadi: {out}")


# ---------------------------------------------------------------------------
# DOM / JavaScript
# ---------------------------------------------------------------------------
class BrowserDOMController:
    """Sahifa ichida JavaScript bajarish: scroll, click, matn olish."""

    def __init__(self, run: Runner | None = None) -> None:
        self._run: Runner = run or run_applescript

    @staticmethod
    def build_script(browser: str, js: str) -> str:
        escaped = js_to_applescript(js)
        if browser == "safari":
            return f'tell application "Safari" to do JavaScript "{escaped}" in current tab of front window'
        return (
            f'tell application "Google Chrome" to execute active tab of front window javascript "{escaped}"'
        )

    async def execute_js(self, browser: str, js: str) -> Result:
        if browser not in BROWSERS:
            return False, f"Noma'lum brauzer: {browser} (safari yoki chrome)"
        ok, out = await self._run(self.build_script(browser, js))
        if not ok:
            return False, _js_error(out)
        return True, out

    async def scroll_page(self, browser: str, direction: str = "down", pixels: int = 600) -> Result:
        d = (direction or "down").lower()
        px = int(pixels or 600)
        if d == "top":
            js = "window.scrollTo({top:0,behavior:'smooth'}); 'top'"
        elif d == "bottom":
            js = "window.scrollTo({top:document.body.scrollHeight,behavior:'smooth'}); 'bottom'"
        elif d == "up":
            js = f"window.scrollBy({{top:-{px},behavior:'smooth'}}); 'up'"
        elif d == "down":
            js = f"window.scrollBy({{top:{px},behavior:'smooth'}}); 'down'"
        else:
            return False, f"Noma'lum yo'nalish: {direction} (up|down|top|bottom)"
        ok, out = await self.execute_js(browser, js)
        labels = {"top": "Sahifa boshiga", "bottom": "Sahifa oxiriga", "up": "Yuqoriga", "down": "Pastga"}
        return (True, f"{labels[d]} aylantirildi") if ok else (False, out)

    async def scroll_to(self, browser: str, position: str | int) -> Result:
        if isinstance(position, str) and position.lower() in ("top", "bottom"):
            return await self.scroll_page(browser, position.lower())
        try:
            y = int(position)
        except (TypeError, ValueError):
            return False, "Pozitsiya son yoki top/bottom bo'lishi kerak"
        ok, out = await self.execute_js(browser, f"window.scrollTo({{top:{y},behavior:'smooth'}}); {y}")
        return (True, f"{y}px pozitsiyaga o'tildi") if ok else (False, out)

    async def click_element(self, browser: str, selector: str) -> Result:
        sel = json.dumps((selector or "").strip())
        if sel == '""':
            return False, "Selektor bo'sh"
        js = (
            "(function(){"
            f"var el=document.querySelector({sel});"
            "if(!el){return 'notfound';}"
            "el.scrollIntoView({block:'center'});"
            "el.click();"
            "return 'clicked:'+(el.innerText||el.value||el.tagName).trim().slice(0,80);"
            "})()"
        )
        ok, out = await self.execute_js(browser, js)
        if not ok:
            return False, out
        if out.strip() == "notfound":
            return False, f"Element topilmadi: {selector}"
        return True, f"Bosildi: {out.replace('clicked:', '', 1)}"

    async def click_by_text(self, browser: str, text: str, tag: str | None = None) -> Result:
        needle = (text or "").strip()
        if not needle:
            return False, "Matn bo'sh"
        tags = (
            tag or ""
        ).strip() or "button, a, [role=button], input[type=submit], input[type=button], summary, label"
        js = (
            "(function(){"
            f"var q={json.dumps(needle.lower())};"
            f"var nodes=Array.from(document.querySelectorAll({json.dumps(tags)}));"
            "var vis=function(e){var r=e.getBoundingClientRect();return r.width>0&&r.height>0;};"
            "var txt=function(e){return ((e.innerText||e.value||e.getAttribute('aria-label')||e.title||'')+'').trim().toLowerCase();};"
            "var el=nodes.find(function(e){return vis(e)&&txt(e)===q;})"
            "||nodes.find(function(e){return vis(e)&&txt(e).indexOf(q)>=0;})"
            "||nodes.find(function(e){return txt(e).indexOf(q)>=0;});"
            "if(!el){return 'notfound';}"
            "el.scrollIntoView({block:'center'});"
            "el.click();"
            "return 'clicked:'+txt(el).slice(0,80);"
            "})()"
        )
        ok, out = await self.execute_js(browser, js)
        if not ok:
            return False, out
        if out.strip() == "notfound":
            return False, f"'{text}' matnli element topilmadi"
        return True, f"Bosildi: {out.replace('clicked:', '', 1)}"

    async def get_page_text_summary(self, browser: str, max_chars: int = 1500) -> Result:
        n = max(200, min(int(max_chars or 1500), 8000))
        js = (
            "(function(){"
            "var main=document.querySelector('main, article, [role=main]')||document.body;"
            "var t=(main.innerText||'').replace(/\\s+\\n/g,'\\n').replace(/\\n{3,}/g,'\\n\\n').trim();"
            f"return JSON.stringify({{title:document.title,url:location.href,text:t.slice(0,{n}),total:t.length}});"
            "})()"
        )
        ok, out = await self.execute_js(browser, js)
        if not ok:
            return False, out
        data = _parse_json(out)
        if not isinstance(data, dict):
            return True, out[:n]
        more = f" … (jami {data.get('total')} belgi)" if (data.get("total") or 0) > n else ""
        return True, f"{data.get('title', '')}\n{data.get('url', '')}\n\n{data.get('text', '')}{more}"

    async def get_page_links(self, browser: str, limit: int = 30) -> Result:
        lim = max(1, min(int(limit or 30), 200))
        js = (
            "(function(){"
            "var seen={};var out=[];"
            "var as=Array.from(document.querySelectorAll('a[href]'));"
            "for(var i=0;i<as.length;i++){var a=as[i];var h=a.href;var t=(a.innerText||a.title||'').trim();"
            "if(!t||!h||h.indexOf('javascript:')===0||seen[h]){continue;}seen[h]=1;"
            "out.push({text:t.slice(0,80),href:h});"
            f"if(out.length>={lim}){{break;}}}}"
            "return JSON.stringify(out);"
            "})()"
        )
        ok, out = await self.execute_js(browser, js)
        if not ok:
            return False, out
        data = _parse_json(out)
        if not isinstance(data, list):
            return True, out
        lines = [f"{i + 1}. {d.get('text')} — {d.get('href')}" for i, d in enumerate(data)]
        return True, "\n".join(lines) if lines else "Havolalar topilmadi"


# ---------------------------------------------------------------------------
# YouTube
# ---------------------------------------------------------------------------
class YouTubeController:
    """YouTube pleyerini `document.querySelector('video')` orqali boshqaradi."""

    def __init__(self, dom: BrowserDOMController | None = None) -> None:
        self.dom = dom or BrowserDOMController()

    @staticmethod
    def _wrap(body: str) -> str:
        return "(function(){var v=document.querySelector('video');if(!v){return 'novideo';}" + body + "})()"

    async def _exec(self, browser: str, body: str, success: str) -> Result:
        ok, out = await self.dom.execute_js(browser, self._wrap(body))
        if not ok:
            return False, out
        if out.strip() == "novideo":
            return False, "Sahifada video topilmadi (YouTube video sahifasi ochiq emas)"
        return True, success.format(out=out.strip())

    async def toggle_play(self, browser: str) -> Result:
        return await self._exec(
            browser,
            "if(v.paused){v.play();return 'playing';}else{v.pause();return 'paused';}",
            "Video: {out}",
        )

    async def play(self, browser: str) -> Result:
        return await self._exec(browser, "v.play();return 'playing';", "Video ijro etilmoqda")

    async def pause(self, browser: str) -> Result:
        return await self._exec(browser, "v.pause();return 'paused';", "Video pauza qilindi")

    async def seek(self, browser: str, seconds: float) -> Result:
        try:
            s = float(seconds)
        except (TypeError, ValueError):
            return False, "Sekundlar son bo'lishi kerak"
        body = (
            f"var t=v.currentTime+({s});"
            "if(t<0){t=0;}if(v.duration&&t>v.duration){t=v.duration;}"
            "v.currentTime=t;return Math.round(t);"
        )
        direction = "oldinga" if s >= 0 else "orqaga"
        return await self._exec(browser, body, f"{abs(int(s))} soniya {direction}: {{out}}s")

    async def seek_to(self, browser: str, seconds: float) -> Result:
        try:
            s = max(0.0, float(seconds))
        except (TypeError, ValueError):
            return False, "Sekundlar son bo'lishi kerak"
        return await self._exec(
            browser, f"v.currentTime={s};return Math.round(v.currentTime);", "O'tildi: {out}s"
        )

    async def restart(self, browser: str) -> Result:
        return await self._exec(browser, "v.currentTime=0;v.play();return 'ok';", "Video boshidan boshlandi")

    async def set_player_volume(self, browser: str, level: float) -> Result:
        try:
            lvl = max(0.0, min(100.0, float(level)))
        except (TypeError, ValueError):
            return False, "Ovoz 0..100 oralig'ida bo'lishi kerak"
        body = f"v.volume={lvl / 100:.3f};v.muted=false;return Math.round(v.volume*100);"
        return await self._exec(browser, body, "Pleyer ovozi: {out}%")

    async def toggle_mute(self, browser: str) -> Result:
        return await self._exec(
            browser, "v.muted=!v.muted;return v.muted?'muted':'unmuted';", "Pleyer: {out}"
        )

    async def set_playback_rate(self, browser: str, rate: float) -> Result:
        try:
            r = max(0.25, min(4.0, float(rate)))
        except (TypeError, ValueError):
            return False, "Tezlik son bo'lishi kerak (0.25..4)"
        return await self._exec(browser, f"v.playbackRate={r};return v.playbackRate;", "Tezlik: {out}x")

    async def toggle_fullscreen(self, browser: str) -> Result:
        body = (
            "var b=document.querySelector('.ytp-fullscreen-button');"
            "if(b){b.click();return 'ok';}"
            "if(document.fullscreenElement){document.exitFullscreen();}else{v.requestFullscreen();}return 'ok';"
        )
        return await self._exec(browser, body, "To'liq ekran almashtirildi")

    async def toggle_subtitles(self, browser: str) -> Result:
        body = (
            "var b=document.querySelector('.ytp-subtitles-button');"
            "if(!b){return 'nobutton';}b.click();return b.getAttribute('aria-pressed')==='true'?'on':'off';"
        )
        ok, out = await self._exec(browser, body, "{out}")
        if not ok:
            return False, out
        if out == "nobutton":
            return False, "Subtitr tugmasi topilmadi"
        return True, "Subtitrlar yoqildi" if out == "on" else "Subtitrlar o'chirildi"

    async def next_video(self, browser: str) -> Result:
        body = "var b=document.querySelector('.ytp-next-button');if(!b){return 'nobutton';}b.click();return 'ok';"
        ok, out = await self._exec(browser, body, "{out}")
        if not ok:
            return False, out
        if out == "nobutton":
            return False, "Keyingi video tugmasi topilmadi"
        return True, "Keyingi videoga o'tildi"

    async def get_video_info(self, browser: str) -> Result:
        body = (
            "var h=document.querySelector('h1.ytd-watch-metadata, h1.title, #title h1');"
            "return JSON.stringify({title:(h?h.innerText:document.title).trim(),"
            "current:Math.round(v.currentTime),duration:Math.round(v.duration||0),paused:v.paused,"
            "volume:Math.round(v.volume*100),muted:v.muted,rate:v.playbackRate,url:location.href});"
        )
        ok, out = await self._exec(browser, body, "{out}")
        if not ok:
            return False, out
        d = _parse_json(out)
        if not isinstance(d, dict):
            return True, out
        state = "pauza" if d.get("paused") else "ijroda"
        return True, (
            f"{d.get('title')} — {_fmt_time(d.get('current', 0))}/{_fmt_time(d.get('duration', 0))}, "
            f"{state}, ovoz {d.get('volume')}%{' (o‘chirilgan)' if d.get('muted') else ''}, tezlik {d.get('rate')}x"
        )


def _fmt_time(secs: Any) -> str:
    try:
        s = int(secs)
    except (TypeError, ValueError):
        return "?"
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


# ---------------------------------------------------------------------------
# Qidiruv natijalari bo'ylab navigatsiya
# ---------------------------------------------------------------------------
_RESULT_SELECTORS = [
    "div#search div.g h3",
    "div#rso h3",  # Google
    "article h2 a",
    "a[data-testid='result-title-a']",  # DuckDuckGo
    "li.b_algo h2 a",  # Bing
    "ytd-video-renderer a#video-title",
    "a#video-title",  # YouTube natijalari
]

_EXTRACT_JS = """
(function(){
  var sels=%(sels)s; var limit=%(limit)d;
  var links=[]; var seen={};
  for (var s=0;s<sels.length;s++){
    var nodes=document.querySelectorAll(sels[s]);
    for (var i=0;i<nodes.length;i++){
      var n=nodes[i];
      var a=(n.tagName==='A')?n:(n.closest('a')||n.querySelector('a'));
      if(!a||!a.href||seen[a.href]){continue;}
      var r=a.getBoundingClientRect(); if(r.width===0&&r.height===0){continue;}
      seen[a.href]=1; links.push({a:a,label:n});
      if(links.length>=limit){break;}
    }
    if(links.length>=limit){break;}
  }
  var old=document.querySelectorAll('.nexus-voice-badge');
  for (var k=0;k<old.length;k++){old[k].remove();}
  var out=[];
  for (var j=0;j<links.length;j++){
    var idx=j+1; var a=links[j].a; var lab=links[j].label;
    a.setAttribute('data-voice-index', String(idx));
    var b=document.createElement('span');
    b.className='nexus-voice-badge'; b.textContent='#'+idx;
    b.style.cssText='display:inline-block;margin-right:8px;padding:1px 7px;border-radius:10px;'
      +'background:#00ffc8;color:#000;font:bold 12px/18px -apple-system,sans-serif;'
      +'box-shadow:0 0 8px #00ffc8;vertical-align:middle;';
    var host=(lab.tagName==='A')?lab:lab; host.insertBefore(b, host.firstChild);
    out.push({index:idx,title:(a.innerText||lab.innerText||'').replace(/^#\\d+\\s*/,'').trim().slice(0,120),url:a.href});
  }
  return JSON.stringify(out);
})()
"""


class SearchNavigationController:
    """Google/DuckDuckGo/Bing/YouTube natijalarini raqamlab, ovoz bilan ochishga tayyorlaydi."""

    def __init__(
        self, dom: BrowserDOMController | None = None, tabs: BrowserController | None = None
    ) -> None:
        self.dom = dom or BrowserDOMController()
        self.tabs = tabs or BrowserController()

    async def highlight_and_extract_results(self, browser: str, limit: int = 10) -> tuple[bool, list[dict]]:
        lim = max(1, min(int(limit or 10), 30))
        js = _EXTRACT_JS % {"sels": json.dumps(_RESULT_SELECTORS), "limit": lim}
        ok, out = await self.dom.execute_js(browser, js)
        if not ok:
            return False, [{"error": out}]
        data = _parse_json(out)
        if not isinstance(data, list):
            return False, [{"error": f"Natijalarni o'qib bo'lmadi: {out[:200]}"}]
        return True, data

    async def get_results_text(self, browser: str, limit: int = 10) -> Result:
        ok, data = await self.highlight_and_extract_results(browser, limit)
        if not ok:
            return False, str(data[0].get("error") if data else "Xato")
        if not data:
            return False, "Qidiruv natijalari topilmadi (qidiruv sahifasi ochiqmi?)"
        lines = [f"#{d['index']}: {d['title']} — {d['url']}" for d in data]
        return True, "\n".join(lines)

    async def _open(self, browser: str, item: dict, new_tab: bool) -> Result:
        url = item.get("url") or ""
        if not url:
            return False, "Natija URL manzili yo'q"
        if new_tab:
            ok, out = await self.tabs.open_url(browser, url)
        else:
            ok, out = await self.tabs.set_current_url(browser, url)
        if not ok:
            return False, out
        return True, f"#{item.get('index')} ochildi: {item.get('title')}"

    async def open_result_by_index(self, browser: str, index: int, new_tab: bool = False) -> Result:
        try:
            idx = int(index)
        except (TypeError, ValueError):
            return False, "Indeks son bo'lishi kerak"
        if idx < 1:
            return False, "Indeks 1 dan boshlanadi"
        ok, data = await self.highlight_and_extract_results(browser, max(idx, 10))
        if not ok:
            return False, str(data[0].get("error") if data else "Xato")
        for item in data:
            if item.get("index") == idx:
                return await self._open(browser, item, new_tab)
        return False, f"#{idx} natija topilmadi (jami {len(data)} ta)"

    async def open_result_by_match(self, browser: str, keyword: str, new_tab: bool = False) -> Result:
        kw = (keyword or "").strip().lower()
        if not kw:
            return False, "Kalit so'z bo'sh"
        ok, data = await self.highlight_and_extract_results(browser, 20)
        if not ok:
            return False, str(data[0].get("error") if data else "Xato")
        words = [w for w in re.split(r"\W+", kw) if w]
        best: dict | None = None
        best_score = 0
        for item in data:
            hay = f"{item.get('title', '')} {item.get('url', '')}".lower()
            score = (10 if kw in hay else 0) + sum(1 for w in words if w in hay)
            if score > best_score:
                best, best_score = item, score
        if best is None:
            return False, f"'{keyword}' ga mos natija topilmadi"
        return await self._open(browser, best, new_tab)

    async def navigate_page(self, browser: str, direction: str = "next") -> Result:
        d = (direction or "next").lower()
        if d in ("next", "keyingi", "oldinga"):
            sels = [
                "a#pnnext",
                "a[aria-label='Next page']",
                "a.sb_pagN",
                "button#more-results",
                ".result--more__btn",
            ]
            label = "Keyingi sahifa"
        elif d in ("prev", "previous", "oldingi", "orqaga"):
            sels = ["a#pnprev", "a[aria-label='Previous page']", "a.sb_pagP"]
            label = "Oldingi sahifa"
        else:
            return False, f"Noma'lum yo'nalish: {direction} (next|prev)"
        js = (
            "(function(){"
            f"var sels={json.dumps(sels)};"
            "for(var i=0;i<sels.length;i++){var el=document.querySelector(sels[i]);"
            "if(el){el.scrollIntoView({block:'center'});el.click();return 'ok';}}"
            "return 'notfound';})()"
        )
        ok, out = await self.dom.execute_js(browser, js)
        if not ok:
            return False, out
        if out.strip() != "ok":
            return False, f"{label} tugmasi topilmadi"
        return True, f"{label}ga o'tildi"


# ---------------------------------------------------------------------------
# Qidiruv maydoniga yozish
# ---------------------------------------------------------------------------
_INPUT_SELECTORS = [
    "textarea[name='q']",
    "input[name='q']",
    "input#searchbox_input",
    "input#sb_form_q",
    "input#search",
    "input[name='search_query']",
    "input[name='search']",
    "input[name='query']",
    "input[type='search']",
    "input[role='combobox']",
    "input[aria-label*='search' i]",
    "input[placeholder*='search' i]",
    "input[placeholder*='qidir' i]",
    "input[placeholder*='поиск' i]",
    "textarea[aria-label*='search' i]",
    "input[type='text']",
]

_TYPE_JS = """
(function(){
  var sels=%(sels)s; var q=%(query)s; var submit=%(submit)s;
  var vis=function(e){var r=e.getBoundingClientRect();return r.width>0&&r.height>0&&!e.disabled;};
  var el=null;
  for(var i=0;i<sels.length&&!el;i++){
    var nodes=document.querySelectorAll(sels[i]);
    for(var j=0;j<nodes.length;j++){ if(vis(nodes[j])){el=nodes[j];break;} }
  }
  if(!el){return 'notfound';}
  el.focus();
  var proto=(el.tagName==='TEXTAREA')?window.HTMLTextAreaElement.prototype:window.HTMLInputElement.prototype;
  var desc=Object.getOwnPropertyDescriptor(proto,'value');
  if(desc&&desc.set){desc.set.call(el,q);}else{el.value=q;}
  el.dispatchEvent(new Event('input',{bubbles:true}));
  el.dispatchEvent(new Event('change',{bubbles:true}));
  if(!submit){return 'typed';}
  var opts={key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true,cancelable:true};
  el.dispatchEvent(new KeyboardEvent('keydown',opts));
  el.dispatchEvent(new KeyboardEvent('keypress',opts));
  el.dispatchEvent(new KeyboardEvent('keyup',opts));
  var f=el.form||el.closest('form');
  if(f){ if(f.requestSubmit){f.requestSubmit();}else{f.submit();} return 'submitted:form'; }
  var btn=document.querySelector('button[aria-label*="search" i], button[type="submit"], #search-icon-legacy, button#search-button, yt-searchbox button');
  if(btn){btn.click();return 'submitted:button';}
  return 'typed:nosubmit';
})()
"""


class SearchInputController:
    """Sahifadagi qidiruv maydonini topib, so'rov yozadi va yuboradi."""

    def __init__(self, dom: BrowserDOMController | None = None) -> None:
        self.dom = dom or BrowserDOMController()

    async def type_query_and_search(self, browser: str, query: str, auto_submit: bool = True) -> Result:
        q = (query or "").strip()
        if not q:
            return False, "So'rov bo'sh"
        js = _TYPE_JS % {
            "sels": json.dumps(_INPUT_SELECTORS),
            "query": json.dumps(q),
            "submit": "true" if auto_submit else "false",
        }
        ok, out = await self.dom.execute_js(browser, js)
        if not ok:
            return False, out
        status = out.strip()
        if status == "notfound":
            return False, "Sahifada qidiruv maydoni topilmadi"
        if status.startswith("submitted"):
            return True, f"Qidirildi: {q}"
        if status == "typed:nosubmit":
            return True, f"Yozildi (yuborish tugmasi topilmadi): {q}"
        return True, f"Yozildi: {q}"

    async def clear_search_input(self, browser: str) -> Result:
        js = _TYPE_JS % {"sels": json.dumps(_INPUT_SELECTORS), "query": '""', "submit": "false"}
        ok, out = await self.dom.execute_js(browser, js)
        if not ok:
            return False, out
        if out.strip() == "notfound":
            return False, "Sahifada qidiruv maydoni topilmadi"
        return True, "Qidiruv maydoni tozalandi"


# ---------------------------------------------------------------------------
# To'g'ridan-to'g'ri qidiruv (eng ishonchli yo'l)
# ---------------------------------------------------------------------------
def build_search_url(query: str, engine: str = "google") -> str | None:
    tpl = SEARCH_ENGINES.get((engine or "google").lower())
    if tpl is None:
        return None
    return tpl.format(q=quote_plus((query or "").strip()))


async def web_search(
    browser: str, query: str, engine: str = "google", tabs: BrowserController | None = None
) -> Result:
    q = (query or "").strip()
    if not q:
        return False, "Qidiruv so'rovi bo'sh"
    url = build_search_url(q, engine)
    if url is None:
        return False, f"Noma'lum qidiruv tizimi: {engine} (google|duckduckgo|bing|youtube)"
    ctrl = tabs or BrowserController()
    ok, out = await ctrl.open_url(browser, url)
    if not ok:
        return False, out
    return True, f"{(engine or 'google').capitalize()} da qidirildi: {q}"


__all__ = [
    "BROWSERS",
    "SEARCH_ENGINES",
    "BrowserController",
    "BrowserDOMController",
    "SearchInputController",
    "SearchNavigationController",
    "YouTubeController",
    "build_search_url",
    "js_to_applescript",
    "normalize_browser",
    "normalize_url",
    "web_search",
]
