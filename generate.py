"""
generate.py  —  seko2077 profile README
All three asset effects ported to pure SVG/SMIL (no JS, works on GitHub):
  • FaultyTerminal → feTurbulence + feDisplacementMap glitch + scanline grid
  • ASCIIText      → hue-rotating gradient + wave-displacement on name text
  • CardSwap       → SMIL card-stack animation on the typing phrases
"""

import base64, os, struct

HERE        = os.path.dirname(os.path.abspath(__file__))
AVATAR_PATH = os.path.join(HERE, "seko2077.png")

with open(AVATAR_PATH, "rb") as f:
    AVATAR_B64 = base64.b64encode(f.read()).decode()

# PNG natural dimensions
with open(AVATAR_PATH, "rb") as f:
    f.read(12)
    IMG_W = struct.unpack(">I", f.read(4))[0]
    IMG_H = struct.unpack(">I", f.read(4))[0]

# ── Live stats (GitHub Actions injects these via env vars) ──────────────────
import json, urllib.request
def fetch_stats(user):
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        return None
    try:
        req = urllib.request.Request(
            f"https://api.github.com/users/{user}",
            headers={"Authorization": f"Bearer {token}",
                     "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
        return {"followers": d.get("followers",0),
                "following": d.get("following",0),
                "repos":     d.get("public_repos",0)}
    except Exception as e:
        print(f"[warn] {e}")
        return None

GH_USER = os.environ.get("GH_USER", "seko2077")
stats   = fetch_stats(GH_USER) or {"followers":3,"following":7,"repos":2}
print(f"Stats: {stats}")

# ── Layout ──────────────────────────────────────────────────────────────────
W       = 1200                          # canvas width
LOGO_H  = round(W * IMG_H / IMG_W)     # exact pixel height → zero crop
INFO_H  = 520                           # info strip height
SVG_H   = LOGO_H + INFO_H
LP      = 360                           # left card width inside info strip

# ── Colours ─────────────────────────────────────────────────────────────────
CYN   = "#22D3EE"
PRP   = "#A855F7"
GRN   = "#10B981"
ORG   = "#FF9900"
RED   = "#F05032"
PNK   = "#EC4899"

PILLS = [
    ("Python",        "#EAB308","#CA8A04"),
    ("AWS",           "#FF9900","#C2410C"),
    ("Docker",        "#38BDF8","#0EA5E9"),
    ("PostgreSQL",    "#4F8DC1","#2C5282"),
    ("Git",           "#F05032","#B91C1C"),
    ("Cybersecurity", "#A855F7","#7E22CE"),
]

# CardSwap phrases — each phrase is a "card" that cycles in/out
PHRASES = [
    ("wabalabadubdub",                               CYN),
    ("Security Engineer",                            PRP),
    ("Vibe Coder",                                   GRN),
    ("Gamer",                                        ORG),
    ("Dressed to impress but stressed and depressed", RED),
    ("The more we f**k around the more we find out", PNK),
]

# ── SVG builder ──────────────────────────────────────────────────────────────
def card_swap_defs_and_svg(phrases, dur_each=3.0):
    """
    CardSwap port: each phrase fades+slides in, holds, slides out. SMIL only.
    """
    n     = len(phrases)
    total = dur_each * n
    texts = ""
    for i, (phrase, col) in enumerate(phrases):
        t_in   = i * dur_each
        t_hold = t_in + dur_each * 0.25
        t_out  = t_in + dur_each * 0.75
        t_end  = (i + 1) * dur_each
        kt = ";".join(f"{v/total:.4f}" for v in [0, t_in, t_hold, t_out, t_end, total])
        op = "0;0;1;1;0;0"
        ty = "14;14;0;0;-14;-14"   # y-translate values
        tx = "0;0;0;0;0;0"          # x stays 0
        translate_vals = ";".join(f"0,{y}" for y in ty.split(";"))
        texts += f"""
    <g opacity="0" font-size="22" font-weight="800" font-family="'Courier New',monospace"
       fill="{col}">
      <animateTransform attributeName="transform" type="translate"
        values="{translate_vals}" keyTimes="{kt}"
        dur="{total:.1f}s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="{op}" keyTimes="{kt}"
               dur="{total:.1f}s" repeatCount="indefinite"/>
      <text y="0">&gt;_ {phrase}</text>
    </g>"""
    return texts

def pill_svg(pills, bg, gap=205, ph=46, pfs=16):
    gdef = out = ""
    for i,(label,c0,c1) in enumerate(pills):
        row,col = divmod(i,3)
        px,py   = col*gap, row*64
        w       = max(len(label)*11+38,110)
        d       = 2.2+i*0.35
        gdef += f'<linearGradient id="pg{i}" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="{c0}"/><stop offset="100%" stop-color="{c1}"/></linearGradient>\n    '
        out  += f"""
      <g transform="translate({px},{py})">
        <rect width="{w}" height="{ph}" rx="9" fill="{bg}" stroke="url(#pg{i})" stroke-width="1.8">
          <animate attributeName="stroke-width" values="1.8;3.2;1.8" dur="{d:.1f}s" repeatCount="indefinite"/>
          <animate attributeName="opacity" values="0.85;1;0.85" dur="{d+0.5:.1f}s" repeatCount="indefinite"/>
        </rect>
        <text x="{w//2}" y="{ph//2+6}" fill="url(#pg{i})" font-size="{pfs}" font-weight="800"
              text-anchor="middle" font-family="system-ui,-apple-system,sans-serif">{label}</text>
      </g>"""
    return gdef, out

# ── The terminal digit-grid (FaultyTerminal port, pure SVG) ─────────────────
def faulty_terminal_grid(x0, y0, cols, rows, cell=22):
    """
    Render a matrix of hex characters that individually blink on/off,
    mimicking the FaultyTerminal digit grid with staggered animation.
    """
    chars = list("0123456789ABCDEF░▒▓")
    out   = ""
    for r in range(rows):
        for c in range(cols):
            idx   = (r * cols + c * 7 + r * 3) % len(chars)
            ch    = chars[idx]
            cx    = x0 + c * cell
            cy    = y0 + r * cell
            dur   = 1.5 + ((r*cols+c) % 17) * 0.15
            delay = ((r*7 + c*3) % 23) * 0.2
            alpha = max(0.05, 0.4 - (r + c) * 0.015)
            out  += f'<text x="{cx}" y="{cy}" font-size="11" fill="{GRN}" opacity="0" font-weight="400">'
            out  += f'<animate attributeName="opacity" values="0;{alpha:.2f};0" keyTimes="0;0.5;1" dur="{dur:.2f}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
            out  += f'{ch}</text>\n'
    return out


def generate_svg(mode):
    dark   = (mode == "dark")
    bg     = "#040810" if dark else "#F0F4F8"
    panel  = "#0A1020" if dark else "#FFFFFF"
    panel2 = "#070D1A" if dark else "#F1F5F9"
    bdr    = "rgba(34,211,238,0.18)" if dark else "rgba(15,23,42,0.12)"
    bdrB   = "rgba(34,211,238,0.35)" if dark else "rgba(15,23,42,0.25)"
    tpri   = "#E8F4FF" if dark else "#0F172A"
    tmut   = "#4B6080" if dark else "#475569"
    scan_c = "rgba(0,0,0,0.32)" if dark else "rgba(0,0,0,0.04)"

    fol  = stats["followers"]
    fing = stats["following"]
    rep  = stats["repos"]

    pg, ps   = pill_svg(PILLS, bg)
    card_svg = card_swap_defs_and_svg(PHRASES)

    # FaultyTerminal grid — appears in background of logo area
    ft_grid = faulty_terminal_grid(10, 20, 28, 16) if dark else ""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {W} {SVG_H}" width="{W}" height="{SVG_H}">

  <!-- ============================================================
       DEFS
  ============================================================ -->
  <defs>

    <!-- Accent cycling gradient -->
    <linearGradient id="acc" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%"   stop-color="{CYN}"><animate attributeName="stop-color"
        values="{CYN};{PRP};{GRN};{CYN}" dur="8s" repeatCount="indefinite"/></stop>
      <stop offset="100%" stop-color="{PRP}"><animate attributeName="stop-color"
        values="{PRP};{GRN};{CYN};{PRP}" dur="8s" repeatCount="indefinite"/></stop>
    </linearGradient>

    <!-- ASCIIText port: hue-rotating gradient for the name -->
    <linearGradient id="ascii-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%"   stop-color="{CYN}"/>
      <stop offset="33%"  stop-color="{PRP}"/>
      <stop offset="66%"  stop-color="{GRN}"/>
      <stop offset="100%" stop-color="{ORG}"/>
    </linearGradient>

    <!-- Pill gradients -->
    {pg}

    <!-- Radial glows -->
    <radialGradient id="g-cyn" cx="50%" cy="50%" r="50%">
      <stop offset="0%"   stop-color="{CYN}" stop-opacity="0.30"/>
      <stop offset="100%" stop-color="{CYN}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="g-prp" cx="50%" cy="50%" r="50%">
      <stop offset="0%"   stop-color="{PRP}" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="{PRP}" stop-opacity="0"/>
    </radialGradient>

    <!-- FaultyTerminal: noise + scanline grid pattern -->
    <pattern id="scanline" width="1" height="4" patternUnits="userSpaceOnUse">
      <rect width="{W}" height="1.5" fill="{scan_c}"/>
    </pattern>
    <pattern id="dot-grid" width="28" height="28" patternUnits="userSpaceOnUse">
      <circle cx="14" cy="14" r="0.8" fill="{bdr}"/>
    </pattern>

    <!-- FaultyTerminal: glitch displacement filter (animated turbulence) -->
    <filter id="glitch" x="-5%" y="-5%" width="110%" height="110%">
      <feTurbulence type="fractalNoise" baseFrequency="0.04 0.0" numOctaves="1"
                    seed="2" result="noise">
        <animate attributeName="baseFrequency"
                 values="0.04 0.0;0.08 0.0;0.02 0.0;0.04 0.0"
                 dur="0.3s" repeatCount="indefinite"/>
        <animate attributeName="seed"
                 values="2;5;8;2" dur="4s" repeatCount="indefinite"/>
      </feTurbulence>
      <feDisplacementMap in="SourceGraphic" in2="noise"
                         scale="0" xChannelSelector="R" yChannelSelector="G" result="d">
        <!-- glitch fires briefly every ~6 seconds -->
        <animate attributeName="scale"
                 values="0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;0;14;0;0;10;0;0"
                 dur="6s" repeatCount="indefinite"/>
      </feDisplacementMap>
      <feComposite in="d" in2="SourceGraphic" operator="over"/>
    </filter>

    <!-- FaultyTerminal: phosphor bloom on the logo -->
    <filter id="bloom" x="-8%" y="-8%" width="116%" height="116%">
      <feGaussianBlur stdDeviation="6" result="blur"/>
      <feBlend in="SourceGraphic" in2="blur" mode="screen"/>
    </filter>

    <!-- ASCIIText: wave distortion on text -->
    <filter id="wave-text" x="-5%" y="-50%" width="110%" height="200%">
      <feTurbulence type="fractalNoise" baseFrequency="0.02 0.15" numOctaves="2" result="n">
        <animate attributeName="baseFrequency"
                 values="0.02 0.15;0.03 0.18;0.02 0.15" dur="4s" repeatCount="indefinite"/>
      </feTurbulence>
      <feDisplacementMap in="SourceGraphic" in2="n" scale="4"
                         xChannelSelector="R" yChannelSelector="G"/>
    </filter>

    <!-- Glow filters -->
    <filter id="glow-sm" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="5" result="b"/>
      <feComposite in="SourceGraphic" in2="b" operator="over"/>
    </filter>
    <filter id="glow-lg" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="14" result="b"/>
      <feComposite in="SourceGraphic" in2="b" operator="over"/>
    </filter>

    <!-- Fade at logo bottom -->
    <linearGradient id="logo-fade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="60%" stop-color="{bg}" stop-opacity="0"/>
      <stop offset="100%" stop-color="{bg}" stop-opacity="1"/>
    </linearGradient>

    <!-- Bottom panel left fade -->
    <linearGradient id="lp-fade" x1="0" y1="0" x2="1" y2="0">
      <stop offset="70%" stop-color="{panel2}" stop-opacity="1"/>
      <stop offset="100%" stop-color="{panel2}" stop-opacity="0"/>
    </linearGradient>

  </defs>

  <!-- ============================================================
       BACKGROUND
  ============================================================ -->
  <rect width="{W}" height="{SVG_H}" fill="{bg}"/>
  <rect width="{W}" height="{SVG_H}" fill="url(#dot-grid)"/>

  <!-- ambient orbs -->
  <ellipse cx="{W//2}" cy="{LOGO_H//2}" rx="580" ry="260" fill="url(#g-cyn)" opacity="0.9">
    <animate attributeName="rx" values="580;640;580" dur="14s" repeatCount="indefinite"/>
    <animate attributeName="ry" values="260;300;260" dur="10s" repeatCount="indefinite"/>
  </ellipse>
  <ellipse cx="{W-100}" cy="{LOGO_H+INFO_H//2}" rx="340" ry="200" fill="url(#g-prp)" opacity="0.8">
    <animate attributeName="rx" values="340;400;340" dur="12s" repeatCount="indefinite"/>
  </ellipse>

  <!-- scanlines everywhere -->
  <rect width="{W}" height="{SVG_H}" fill="url(#scanline)"/>

  <!-- beam sweep (FaultyTerminal horizontal scan) -->
  <rect x="0" y="-4" width="{W}" height="2" fill="{CYN}" opacity="0.05">
    <animate attributeName="y" values="-4;{SVG_H+4};-4" dur="8s" repeatCount="indefinite"/>
  </rect>

  <!-- ============================================================
       LOGO (FaultyTerminal backdrop + phosphor bloom + glitch)
  ============================================================ -->

  <!-- FaultyTerminal digit grid behind logo -->
  {'<g font-family="Courier New,monospace" opacity="0.22">' + ft_grid + '</g>' if dark else ''}

  <!-- The logo itself — full bleed, zero crop -->
  <image href="data:image/png;base64,{AVATAR_B64}"
         x="0" y="0" width="{W}" height="{LOGO_H}"
         preserveAspectRatio="xMidYMid meet"
         filter="url(#glitch)"/>

  <!-- Phosphor bloom copy (FaultyTerminal glow effect) -->
  <image href="data:image/png;base64,{AVATAR_B64}"
         x="0" y="0" width="{W}" height="{LOGO_H}"
         preserveAspectRatio="xMidYMid meet"
         filter="url(#bloom)" opacity="0.25"/>

  <!-- bottom shadow into info strip -->
  <rect x="0" y="{LOGO_H-100}" width="{W}" height="100" fill="url(#logo-fade)"/>

  <!-- top accent line -->
  <rect x="0" y="0" width="{W}" height="4" fill="url(#acc)">
    <animate attributeName="opacity" values="0.7;1;0.7" dur="3s" repeatCount="indefinite"/>
  </rect>

  <!-- corner brackets (hacker aesthetic) -->
  <g stroke="{CYN}" stroke-width="3" fill="none" opacity="0.7"
     filter="url(#glow-sm)">
    <polyline points="0,28 0,0 28,0"/>
    <polyline points="{W-28},0 {W},0 {W},28"/>
    <polyline points="0,{LOGO_H-28} 0,{LOGO_H} 28,{LOGO_H}"/>
    <polyline points="{W-28},{LOGO_H} {W},{LOGO_H} {W},{LOGO_H-28}"/>
  </g>

  <!-- ONLINE indicator -->
  <circle cx="18" cy="18" r="6" fill="{GRN}" filter="url(#glow-sm)">
    <animate attributeName="r"       values="5;7;5"   dur="1.8s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.6;1;0.6" dur="1.8s" repeatCount="indefinite"/>
  </circle>
  <text x="30" y="23" font-family="'Courier New',monospace" font-size="12"
        fill="{GRN}" font-weight="700" letter-spacing="2">ONLINE</text>

  <!-- divider -->
  <line x1="0" y1="{LOGO_H}" x2="{W}" y2="{LOGO_H}"
        stroke="url(#acc)" stroke-width="2" opacity="0.5"/>

  <!-- ============================================================
       INFO STRIP
  ============================================================ -->
  <rect x="0" y="{LOGO_H}" width="{W}" height="{INFO_H}" fill="{panel2}" opacity="0.94"/>

  <!-- ── LEFT CARD (ASCIIText-style name) ── -->
  <g transform="translate(0,{LOGO_H})">
    <rect width="{LP}" height="{INFO_H}" fill="{bg}" opacity="0.55"/>
    <!-- right edge glow -->
    <rect x="{LP-4}" y="0" width="4" height="{INFO_H}" fill="url(#lp-fade)" opacity="0.6"/>
    <line x1="{LP}" y1="0" x2="{LP}" y2="{INFO_H}" stroke="{bdrB}" stroke-width="1.5"/>

    <!-- ASCIIText port: name with hue-rotating gradient + wave filter -->
    <text x="{LP//2}" y="72" text-anchor="middle"
          font-family="system-ui,-apple-system,sans-serif"
          font-size="34" font-weight="900"
          fill="url(#ascii-grad)" filter="url(#wave-text)">
      Hi, I'm Saif &#x1F44B;
      <!-- hue rotation animation (ASCIIText hue effect) -->
      <animateTransform attributeName="transform" type="skewX"
                        values="0;0.3;0;-0.3;0" dur="6s" repeatCount="indefinite"/>
    </text>

    <text x="{LP//2}" y="108" text-anchor="middle"
          font-family="'Courier New',monospace"
          font-size="18" fill="{CYN}" font-weight="700" letter-spacing="2.5"
          filter="url(#glow-sm)">@seko2077</text>

    <text x="{LP//2}" y="134" text-anchor="middle"
          font-family="system-ui,-apple-system,sans-serif"
          font-size="15" fill="{tmut}">&#127757; Earth C-137</text>

    <line x1="28" y1="154" x2="{LP-28}" y2="154" stroke="{bdrB}" stroke-width="1"/>

    <!-- live stats -->
    <g font-family="system-ui,-apple-system,sans-serif" text-anchor="middle">
      <g transform="translate({LP//4 - 14}, 172)">
        <text font-size="40" font-weight="900" fill="{CYN}" filter="url(#glow-sm)">{fol}</text>
        <text y="32" font-size="13" fill="{tmut}">followers</text>
      </g>
      <g transform="translate({LP//2}, 172)">
        <text font-size="40" font-weight="900" fill="{PRP}" filter="url(#glow-sm)">{fing}</text>
        <text y="32" font-size="13" fill="{tmut}">following</text>
      </g>
      <g transform="translate({LP*3//4 + 14}, 172)">
        <text font-size="40" font-weight="900" fill="{GRN}" filter="url(#glow-sm)">{rep}</text>
        <text y="32" font-size="13" fill="{tmut}">repos</text>
      </g>
    </g>

    <!-- live badge -->
    <g transform="translate({LP//2 - 65}, {INFO_H - 58})">
      <rect width="130" height="28" rx="14" fill="{bg}" stroke="{bdrB}" stroke-width="1"/>
      <circle cx="18" cy="14" r="4" fill="{GRN}">
        <animate attributeName="opacity" values="0.4;1;0.4" dur="2s" repeatCount="indefinite"/>
      </circle>
      <text x="68" y="18.5" text-anchor="middle" font-size="12"
            font-family="'Courier New',monospace" fill="{tmut}">live · 6h refresh</text>
    </g>
  </g>

  <!-- ── RIGHT PANEL ── -->
  <g transform="translate({LP + 44}, {LOGO_H + 32})">

    <!-- CardSwap: cycling phrase stack -->
    <g transform="translate(0, 0)" clip-path="none">
      {card_svg}
    </g>

    <!-- bio lines -->
    <g transform="translate(0, 42)" font-size="17" fill="{tmut}"
       font-family="system-ui,-apple-system,sans-serif">
      <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.6s" begin="0.4s" fill="freeze"/>
        <text y="0">
          <tspan fill="{CYN}" font-family="'Courier New',monospace" font-weight="700">&#9733;</tspan>
          <tspan font-weight="700" fill="{tpri}"> Focus: </tspan>Security Engineering &amp; Breaking Things
        </text>
      </g>
      <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.6s" begin="0.9s" fill="freeze"/>
        <text y="34">
          <tspan fill="{PRP}" font-family="'Courier New',monospace" font-weight="700">&#9733;</tspan>
          <tspan font-weight="700" fill="{tpri}"> Learning: </tspan>Red-teaming, Cloud Security, CTFs
        </text>
      </g>
      <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.6s" begin="1.4s" fill="freeze"/>
        <text y="68">
          <tspan fill="{GRN}" font-family="'Courier New',monospace" font-weight="700">&#9733;</tspan>
          <tspan font-weight="700" fill="{tpri}"> Off-duty: </tspan>Gaming &amp; vibing to music
        </text>
      </g>
      <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.6s" begin="1.9s" fill="freeze"/>
        <text y="102">
          <tspan fill="{ORG}" font-family="'Courier New',monospace" font-weight="700">&#9733;</tspan>
          <tspan font-weight="700" fill="{tpri}"> Bio: </tspan>Just a humble stranger &#128591;
        </text>
      </g>
    </g>

    <!-- ARSENAL -->
    <g transform="translate(0, 200)" opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.8s" begin="2.2s" fill="freeze"/>
      <text font-size="13" font-weight="700" fill="{CYN}"
            font-family="'Courier New',monospace" letter-spacing="5">ARSENAL</text>
      <line x1="90" y1="-6" x2="830" y2="-6" stroke="{bdr}" stroke-width="0.8"/>
      <g transform="translate(0,16)">{ps}</g>
    </g>

    <!-- GitHub link -->
    <g transform="translate(0, {INFO_H - 60})" opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.8s" begin="3s" fill="freeze"/>
      <line x1="0" y1="0" x2="830" y2="0" stroke="{bdrB}" stroke-width="1"/>
      <g transform="translate(0,18)" font-family="'Courier New',monospace" font-size="14">
        <circle cx="8" cy="-1" r="5" fill="{GRN}" filter="url(#glow-sm)">
          <animate attributeName="opacity" values="0.5;1;0.5" dur="2s" repeatCount="indefinite"/>
        </circle>
        <text x="22" y="0" fill="{tmut}">github.com/<tspan fill="{CYN}" font-weight="700">seko2077</tspan></text>
      </g>
    </g>

  </g>

</svg>"""

    out = os.path.join(HERE, f"{mode}.svg")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"  wrote {out}  ({W}x{SVG_H})")


generate_svg("dark")
generate_svg("light")
print("Done.")
