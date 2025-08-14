# streamlit_app.py
import json
import base64
import zlib
from datetime import datetime
from typing import Dict, Any, List, Optional

import streamlit as st

# --------- PAGE CONFIG ---------
st.set_page_config(
    page_title="MirrorGarden — ett psykologiskt minispel",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --------- STATE ---------
if "step" not in st.session_state:
    st.session_state.step = 0
if "profile" not in st.session_state:
    st.session_state.profile = {
        "name": "",
        "language": "sv",
        "consent": False,
        "private_mode": True,
        "light_theme": False
    }
if "answers" not in st.session_state:
    st.session_state.answers: Dict[str, Any] = {}
if "started_at" not in st.session_state:
    st.session_state.started_at = datetime.utcnow().isoformat()
if "panic_mode" not in st.session_state:
    st.session_state.panic_mode = False
if "card_index" not in st.session_state:
    st.session_state.card_index = -1

# --------- QUERY PARAM HELPERS (stable API) ---------
def qp_get(name: str, default: Optional[str] = None) -> Optional[str]:
    """Read a query param robustly (handles both str and legacy list)."""
    v = st.query_params.get(name, default)
    if isinstance(v, list):  # legacy safety
        return v[0] if v else default
    return v

def qp_set(params: Dict[str, str], replace: bool = False):
    """Set query params using stable API. Triggers a rerun automatically."""
    if replace:
        st.query_params = {k: str(v) for k, v in params.items()}
    else:
        current = dict(st.query_params)
        current.update({k: str(v) for k, v in params.items()})
        st.query_params = current

def qp_clear():
    st.query_params = {}

# --------- SHARE / REPORT HELPERS ---------
def pack_share_data() -> str:
    """Compress + encode an export pack for a URL param."""
    pack = export_pack()
    raw = json.dumps(pack, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    comp = zlib.compress(raw, level=9)
    tok = base64.urlsafe_b64encode(comp).decode("ascii")
    return tok

def unpack_share_data(tok: str) -> Optional[Dict[str, Any]]:
    try:
        comp = base64.urlsafe_b64decode(tok.encode("ascii"))
        raw = zlib.decompress(comp)
        data = json.loads(raw.decode("utf-8"))
        return data
    except Exception:
        return None

def enter_report_mode_from_query() -> Optional[Dict[str, Any]]:
    if qp_get("mode") == "report" and qp_get("r"):
        data = unpack_share_data(qp_get("r"))
        return data
    return None

# --------- CONTENT DEFINITIONS ---------
SECTIONS = [
    {"id": "intro", "title": "Intro", "emoji": "🌿"},
    {"id": "ground", "title": "Andnings-ankare", "emoji": "🫁"},
    {"id": "timeline", "title": "Livslinje", "emoji": "🧭"},
    {"id": "voices", "title": "Inre röster", "emoji": "🎭"},
    {"id": "boundaries", "title": "Gränslabb", "emoji": "🧱"},
    {"id": "attachment", "title": "Anknytningskompass", "emoji": "🧲"},
    {"id": "values", "title": "Värdekarta", "emoji": "🧡"},
    {"id": "cards", "title": "Reflektionskort", "emoji": "🃏"},
    {"id": "soothing", "title": "Egen trygghetskit", "emoji": "🧰"},
    {"id": "letter", "title": "Brev till mig själv", "emoji": "✍️"},
    {"id": "summary", "title": "Insiktskarta", "emoji": "📜"},
]

BOUNDARY_STATEMENTS = [
    "Jag säger nej utan att förklara mig i situationer där det behövs.",
    "Jag märker tidigt när någon kliver över mina gränser.",
    "Jag tar ansvar för mitt nej, även om andra blir besvikna.",
    "Jag förhandlar när gränser krockar, istället för att ge upp.",
    "Jag vet vad jag behöver för att känna mig trygg i en relation.",
    "Jag sätter tidsgränser när jag hjälper andra.",
    "Jag ber om utrymme när jag är överväldigad.",
    "Jag kan ta emot ett nej utan att ta det personligt.",
]

ATTACHMENT_ITEMS = {
    "Trygg": [
        "Jag känner mig värd kärlek även när saker går fel.",
        "Jag kan vara nära utan att tappa mig själv.",
        "Jag uttrycker behov utan skam."
    ],
    "Ambivalent/Anxious": [
        "Jag blir orolig när svar dröjer.",
        "Jag överanalyserar lätt tonfall och emojis.",
        "Jag söker ofta bekräftelse när jag känner mig osäker."
    ],
    "Undvikande": [
        "Jag behöver mycket egen tid för att känna mig okej.",
        "Jag blir kvävd när någon vill 'definiera' relationen snabbt.",
        "Jag håller ofta känslor för mig själv."
    ],
    "Rädd/Desorganiserad": [
        "Jag vill vara nära men växlar snabbt till att dra mig undan.",
        "Intimitet kan trigga min kamp/flykt-reaktion.",
        "Jag testar andra för att se om de stannar."
    ]
}

VALUES_POOL = [
    "Frihet","Trygghet","Familj","Rättvisa","Humor","Äventyr","Lojalitet","Självrespekt",
    "Mjukhet","Styrka","Ärlighet","Andlighet","Kreativitet","Ansvar","Lärande","Kärlek",
    "Integritet","Gemenskap","Mod","Tillit","Balans","Framgång","Oberoende","Tålamod"
]

SOOTHING_OPTIONS = [
    "Andning: 4-7-8 i 2 minuter",
    "Kropps-scan från huvud till tå",
    "Lugn musik eller favoritdikt",
    "Varm dusch, vätska, något litet att äta",
    "Skriva tre rader: 'Just nu känner jag…,' 'Det betyder…,' 'Jag behöver…'",
    "Meddela en vän: 'Jag vill bara att du lyssnar'",
    "Gå en 10-minuters promenad utan mobil",
    "Byt miljö: öppet fönster, balkong, ute"
]

REFLECTION_CARDS = [
    {"q": "Vilken del av dig förtjänar mer mjukhet just nu?", "mode": "text"},
    {"q": "När kände du dig som mest levande senaste året – vad hände?", "mode": "text"},
    {"q": "Om 'trygghet' var en plats, hur ser den ut och vad hörs där?", "mode": "text"},
    {"q": "Vad är en liten gräns du vill hålla den här veckan?", "mode": "text"},
    {"q": "Vilket av dessa känns mest sant idag?", "mode": "choice",
     "choices": ["Jag behöver vila", "Jag behöver kontakt", "Jag behöver utrymme", "Jag behöver tydlighet"]},
    {"q": "Vilken handling skulle framtida-du tacka dig för ikväll?", "mode": "text"},
    {"q": "Vilken relationell myt vill du släppa?", "mode": "text"},
    {"q": "Vilken mikro-rutin (≤5 min) kan stötta dig dagligen?", "mode": "text"},
]

# --------- THEME (CSS) ---------
def inject_css(light: bool):
    if light:
        bg = "#fafafa"; text="#0b0c10"; card="#ffffff"; border="#e6e6e6"; sub="#444"
    else:
        bg = "#0e1117"; text="#e8e9ec"; card="#0e1117"; border="#262730"; sub="#a6a7ab"
    st.markdown(
        f"""
        <style>
            html, body, [data-testid="stAppViewContainer"] {{
                background: {bg};
                color: {text};
            }}
            .block-container {{padding-top: 1rem; padding-bottom: 2rem; max-width: 720px;}}
            .stButton>button {{border-radius: 14px; padding: 0.7rem 1rem; font-weight: 600;}}
            .stTextInput>div>div>input, .stTextArea textarea {{font-size: 1.05rem;}}
            .question-card {{background: {card}; border: 1px solid {border}; border-radius: 16px; padding: 14px; margin: 10px 0;}}
            .soft {{opacity: 0.92;}}
            .pill {{display:inline-block; padding: 6px 10px; border-radius: 999px; border:1px solid {border};}}
            .muted {{color:{sub}; font-size:0.95rem;}}
            .center {{text-align:center;}}
            .title {{font-size:1.6rem; font-weight:800; line-height:1.2;}}
            .subtitle {{font-size:1.1rem; opacity:0.95;}}
            .disclaimer {{background:{card}; border:1px solid {border}; border-radius:14px; padding:12px;}}
            .tiny {{font-size:0.85rem;}}
            .divider {{height:1px; background:{border}; margin:14px 0;}}
        </style>
        """,
        unsafe_allow_html=True,
    )

# --------- NAV HELPERS ---------
def step_index_by_id(section_id: str) -> int:
    for i, s in enumerate(SECTIONS):
        if s["id"] == section_id:
            return i
    return 0

def go_to(section_id: str):
    st.session_state.step = step_index_by_id(section_id)

def next_step():
    st.session_state.step = min(st.session_state.step + 1, len(SECTIONS) - 1)

def prev_step():
    st.session_state.step = max(st.session_state.step - 1, 0)

# --------- SCORING ---------
def polar_scores() -> Dict[str, float]:
    b_scores = st.session_state.answers.get("boundaries_scores", [4]*len(BOUNDARY_STATEMENTS))
    b_avg = sum(b_scores)/len(b_scores) if b_scores else 0
    a_scores = st.session_state.answers.get("attachment_scores", {})
    a_norm = {k: (sum(v)/len(v) if v else 0) for k, v in a_scores.items()}
    return {
        "Gränser": b_avg,
        "Trygghet": a_norm.get("Trygg", 0),
        "Oro/Anknytning": a_norm.get("Ambivalent/Anxious", 0),
        "Avstånd/Undvikande": a_norm.get("Undvikande", 0),
        "Ambivalens/Rädsla": a_norm.get("Rädd/Desorganiserad", 0)
    }

# --------- EXPORT ---------
def export_pack() -> Dict[str, Any]:
    return {
        "meta": {
            "app": "MirrorGarden",
            "version": "1.2.0",
            "started_at": st.session_state.started_at,
            "exported_at": datetime.utcnow().isoformat(),
        },
        "profile": st.session_state.profile,
        "answers": st.session_state.answers,
        "scores": polar_scores()
    }

def make_markdown_report(data: Optional[Dict[str, Any]] = None) -> str:
    if data is None:
        data = export_pack()
    p = data.get("profile", {})
    scores = data.get("scores", {})
    name = p.get("name") or "Vän"
    vals = data.get("answers", {}).get("top_values", [])
    soothing = data.get("answers", {}).get("soothing_kit", [])
    letter = data.get("answers", {}).get("self_letter", "").strip()
    tl = data.get("answers", {}).get("timeline_points", [])
    highlights = [
        f"- Gränser (självrespekt): **{scores.get('Gränser',0):.1f}/10**",
        f"- Trygghet i närhet: **{scores.get('Trygghet',0):.1f}/10**",
        f"- Oro/Anknytning: **{scores.get('Oro/Anknytning',0):.1f}/10**",
        f"- Avstånd/Undvikande: **{scores.get('Avstånd/Undvikande',0):.1f}/10**",
        f"- Ambivalens/Rädsla: **{scores.get('Ambivalens/Rädsla',0):.1f}/10**",
    ]

    report = f"""# MirrorGarden — Din insiktskarta

Hej {name}, här är en sammanfattning av din resa i appen.

## Huvudpoänger
{chr(10).join(highlights)}

## Dina toppvärden
{", ".join(vals) if vals else "—"}

## Din trygghetskit
{chr(10).join([f"- {x}" for x in soothing]) if soothing else "—"}

## Din livslinje (nedslag)
{chr(10).join([f"- {x}" for x in tl]) if tl else "—"}

## Brev till mig själv
{letter if letter else "—"}

---
*Den här appen är inte vård eller terapi. Om något väcker jobbiga känslor: prata med någon du litar på eller sök stöd.*
"""
    return report

# --------- QUICK EXIT ---------
with st.container():
    col1, col2 = st.columns([1,1])
    with col2:
        if st.button("⚡ Quick Exit", help="Rensar sessionen och visar ofarligt innehåll.", use_container_width=True):
            st.session_state.clear()
            st.session_state.panic_mode = True
            st.rerun()

if st.session_state.panic_mode:
    st.success("Du är trygg här. Andas in i 4 sekunder, håll 7, andas ut 8. Upprepa 3 gånger.")
    st.image("https://picsum.photos/seed/mirror-garden/800/400", caption="En trygg plats.")
    st.stop()

# --------- THEME TOGGLE (reads from stable query param) ---------
theme_q = qp_get("theme", "dark")
if isinstance(theme_q, str):
    st.session_state.profile["light_theme"] = (theme_q == "light")

inject_css(light=st.session_state.profile.get("light_theme", False))

# --------- HEADER ---------
st.markdown(f"<div class='title center'>🌿 MirrorGarden</div>", unsafe_allow_html=True)
st.markdown("<p class='subtitle center soft'>Ett litet, vackert, psykologiskt minispel för självinsikt.<br/>Mobilvänligt. Inget sparas i molnet.</p>", unsafe_allow_html=True)
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# Theme controls
with st.expander("🎛️ Visuella inställningar", expanded=False):
    light = st.toggle("Ljust tema", value=st.session_state.profile.get("light_theme", False))
    st.session_state.profile["light_theme"] = light
    # persist in URL without experimental API
    qp_set({"theme": "light" if light else "dark"})

# --------- PROGRESS ---------
prog = (st.session_state.step + 1) / len(SECTIONS)
st.progress(prog, text=f"Steg {st.session_state.step+1} / {len(SECTIONS)}")

def step_header():
    s = SECTIONS[st.session_state.step]
    st.markdown(f"<div class='pill muted center'>{s['emoji']} {s['title']}</div>", unsafe_allow_html=True)

# --------- RENDERERS ---------
def render_intro():
    step_header()
    st.markdown(
        """
        <div class='disclaimer'>
        <b>Innan vi börjar:</b><br/>
        Detta är en mjuk, guidande upplevelse – inte terapi eller vård. 
        Du bestämmer takten och vad du vill dela. Inget skickas till servern; allt stannar i din webbläsare tills du själv exporterar.
        </div>
        """, unsafe_allow_html=True
    )
    name = st.text_input("Vad vill du bli kallad?", value=st.session_state.profile.get("name",""), placeholder="(valfritt)")
    private = st.toggle("Privat läge (dölj känsliga fält i publika miljöer)", value=st.session_state.profile.get("private_mode", True))
    consent = st.checkbox("Jag förstår och vill gå vidare.", value=st.session_state.profile.get("consent", False))
    st.session_state.profile.update({"name": name.strip(), "private_mode": private, "consent": consent})
    st.info("Tips: Sätt mobilen på 'Stör ej' i 10–15 min.")
    st.button("Starta resan →", on_click=next_step, disabled=not consent, use_container_width=True)

def render_ground():
    step_header()
    st.markdown("**🫁 Andnings-ankare (1 minut)**\n\nSätt en mjuk timer i huvudet. Andas långsamt. Lägg märke till tre saker du ser, hör och känner.", help="Som att landa i kroppen innan vi gräver.")
    three = st.text_area("Skriv 3 saker du märker just nu:", value=st.session_state.answers.get("grounding_notes",""), placeholder="1) ...\n2) ...\n3) ...", height=100)
    st.session_state.answers["grounding_notes"] = three
    st.button("Nästa →", on_click=next_step, use_container_width=True)

def render_timeline():
    step_header()
    st.markdown("**🧭 Livslinje – tre nedslag som format dig.**", help="De kan vara små eller stora. Välj sådant som känns sant.")
    items = st.session_state.answers.get("timeline_points", ["", "", ""])
    if not isinstance(items, list) or len(items) != 3:
        items = ["", "", ""]
    for i in range(3):
        items[i] = st.text_input(f"Nedslag {i+1}", value=items[i], placeholder="t.ex. när jag flyttade hemifrån / ett viktigt beslut / en trygg plats", key=f"tl_{i}")
    st.session_state.answers["timeline_points"] = items
    st.button("Nästa →", on_click=next_step, use_container_width=True)

def render_voices():
    step_header()
    st.markdown("**🎭 Inre röster: Kritiker & Allierad**", help="Skriv ned vad de brukar säga – och låt allieraden svara.")
    c1, c2 = st.columns(2)
    with c1:
        critic = st.text_area("Inre kritiker – vad säger den?", value=st.session_state.answers.get("inner_critic",""), placeholder="t.ex. 'du duger inte'…", height=120)
    with c2:
        ally = st.text_area("Inre allierad – hur svarar den?", value=st.session_state.answers.get("inner_ally",""), placeholder="t.ex. 'jag växer varje dag'…", height=120)
    st.session_state.answers["inner_critic"] = critic
    st.session_state.answers["inner_ally"] = ally
    st.button("Nästa →", on_click=next_step, use_container_width=True)

def render_boundaries():
    step_header()
    st.markdown("**🧱 Gränslabb – skattning 0–10**", help="0 = stämmer inte alls, 10 = stämmer helt.")
    scores = st.session_state.answers.get("boundaries_scores", [5]*len(BOUNDARY_STATEMENTS))
    out = []
    for i, q in enumerate(BOUNDARY_STATEMENTS):
        out.append(st.slider(q, 0, 10, int(scores[i]) if i < len(scores) else 5, key=f"b_{i}"))
    st.session_state.answers["boundaries_scores"] = out
    st.button("Nästa →", on_click=next_step, use_container_width=True)

def render_attachment():
    step_header()
    st.markdown("**🧲 Anknytningskompass – hur ofta stämmer följande?**", help="0 = Aldrig, 10 = Ofta")
    store: Dict[str, List[int]] = st.session_state.answers.get("attachment_scores", {})
    for style, items in ATTACHMENT_ITEMS.items():
        st.markdown(f"**{style}**")
        local = store.get(style, [3]*len(items))
        new_local = []
        for i, it in enumerate(items):
            new_local.append(st.slider(it, 0, 10, int(local[i]) if i < len(local) else 3, key=f"a_{style}_{i}"))
        store[style] = new_local
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.session_state.answers["attachment_scores"] = store
    st.button("Nästa →", on_click=next_step, use_container_width=True)

def render_values():
    step_header()
    st.markdown("**🧡 Värdekarta – välj upp till 6 som känns 'du'**")
    chosen = st.multiselect("Välj dina ord:", VALUES_POOL, default=st.session_state.answers.get("top_values", []), max_selections=6)
    st.session_state.answers["top_values"] = chosen
    why = st.text_area("Varför dessa? Koppla gärna till din livslinje.", value=st.session_state.answers.get("values_why",""), height=120)
    st.session_state.answers["values_why"] = why
    st.button("Nästa →", on_click=next_step, use_container_width=True)

def render_cards():
    step_header()
    st.markdown("**🃏 Reflektionskort**")
    colA, colB = st.columns([2,1])
    with colA:
        if st.button("Dra ett kort 🎴", use_container_width=True):
            st.session_state.card_index = (st.session_state.card_index + 1) % len(REFLECTION_CARDS)
    with colB:
        st.caption("Dra för nytt kort.")

    idx = st.session_state.card_index
    if idx == -1:
        st.info("Tryck på **Dra ett kort** för att börja.")
        return

    card = REFLECTION_CARDS[idx]
    st.markdown(f"<div class='question-card'><b>Fråga:</b><br/>{card['q']}</div>", unsafe_allow_html=True)

    # Answers store
    answers = st.session_state.answers.get("reflection_cards", {})
    if card["mode"] == "text":
        val = st.text_area("Ditt svar:", value=answers.get(str(idx), ""), height=120)
        answers[str(idx)] = val
    elif card["mode"] == "choice":
        choice = st.radio(
            "Välj ett alternativ:",
            card["choices"],
            index=card["choices"].index(answers.get(str(idx), card["choices"][0])) if str(idx) in answers else 0
        )
        answers[str(idx)] = choice
    st.session_state.answers["reflection_cards"] = answers

    st.button("Nästa →", on_click=next_step, use_container_width=True)

def render_soothing():
    step_header()
    st.markdown("**🧰 Trygghetskit – välj 3–5 som brukar hjälpa**")
    chosen = st.multiselect("Snabbhjälp:", SOOTHING_OPTIONS, default=st.session_state.answers.get("soothing_kit", []))
    st.session_state.answers["soothing_kit"] = chosen
    st.button("Nästa →", on_click=next_step, use_container_width=True)

def render_letter():
    step_header()
    st.markdown("**✍️ Brev till mig själv (framtida jag, 6 månader fram)**")
    letter = st.text_area("Skriv fritt:", value=st.session_state.answers.get("self_letter",""), height=180, placeholder="Vad vill du att framtida du ska minnas, när det blåser?")
    st.session_state.answers["self_letter"] = letter
    st.button("Nästa →", on_click=next_step, use_container_width=True)

def render_summary():
    step_header()
    st.markdown("**📜 Din insiktskarta**")
    scores = polar_scores()

    colA, colB = st.columns(2)
    with colA:
        st.metric("Gränser", f"{scores['Gränser']:.1f}/10")
        st.metric("Trygghet", f"{scores['Trygghet']:.1f}/10")
        st.metric("Oro/Anknytning", f"{scores['Oro/Anknytning']:.1f}/10")
    with colB:
        st.metric("Undvikande", f"{scores['Avstånd/Undvikande']:.1f}/10")
        st.metric("Ambivalens/Rädsla", f"{scores['Ambivalens/Rädsla']:.1f}/10")

    st.markdown("**Text-visualisering:**", help="En liten känsla för riktningen.")
    for k, v in scores.items():
        filled = "█" * int(round(v))
        empty = "░" * (10 - int(round(v)))
        st.write(f"{k:>20}: {filled}{empty}  {v:.1f}/10")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Export buttons
    pack = export_pack()
    md = make_markdown_report().encode("utf-8")
    raw = json.dumps(pack, ensure_ascii=False, indent=2).encode("utf-8")
    st.download_button("⬇️ Ladda ned insiktskarta (.md)", data=md, file_name="insiktskarta.md", mime="text/markdown")
    st.download_button("⬇️ Exportera data (.json)", data=raw, file_name="mirror-garden.json", mime="application/json")

    # Share link (no experimental API)
    st.markdown("### Dela som läsbar länk")
    st.caption("Skapar en läsbar 'report'-vy av din insiktskarta. Ingen data sparas – allt ligger inbäddat i länken.")
    if st.button("Skapa delningslänk 🔗", use_container_width=True):
        tok = pack_share_data()
        theme = "light" if st.session_state.profile.get("light_theme") else "dark"
        qp_set({"mode": "report", "r": tok, "theme": theme})
        # Efter uppdatering av query params sker en automatisk rerun och adressraden uppdateras.

    st.info("Klar & vacker. Om något känns mycket – pausa, andas, ta en mjuk promenad. 🌿")
    if st.button("Börja om"):
        st.session_state.clear()
        st.rerun()

# --------- REPORT-ONLY VIEW (if ?mode=report&r=...) ---------
report_data = enter_report_mode_from_query()
if report_data:
    # Apply theme from query
    theme = qp_get("theme", "dark")
    inject_css(light=(theme == "light"))
    st.markdown("<div class='title center'>📜 MirrorGarden — Delad insiktskarta</div>", unsafe_allow_html=True)
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Render read-only report
    st.markdown(make_markdown_report(report_data))
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    if st.button("Öppna i upplevelse-läge →", use_container_width=True):
        qp_clear()
        st.rerun()
    st.stop()

# --------- RENDER ENGINE ---------
current = SECTIONS[st.session_state.step]["id"]
if current == "intro":
    render_intro()
elif current == "ground":
    render_ground()
elif current == "timeline":
    render_timeline()
elif current == "voices":
    render_voices()
elif current == "boundaries":
    render_boundaries()
elif current == "attachment":
    render_attachment()
elif current == "values":
    render_values()
elif current == "cards":
    render_cards()
elif current == "soothing":
    render_soothing()
elif current == "letter":
    render_letter()
elif current == "summary":
    render_summary()
