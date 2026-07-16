"""
generate.py  —  seko2077 profile README
Generates dark.svg + light.svg — the info panel ONLY.
The logo (seko2077.png) is displayed separately in README.md as a plain
markdown <img> which GitHub always renders reliably.
"""

import os, struct, json, urllib.request, base64

HERE        = os.path.dirname(os.path.abspath(__file__))
AVATAR_PATH = os.path.join(HERE, "seko2077.png")

# ── Live stats via GitHub API ───────────────────────────────────────────────
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
        return {"followers": d.get("followers", 0),
                "following": d.get("following", 0),
                "repos":     d.get("public_repos", 0)}
    except Exception as e:
        print(f"[warn] {e}")
        return None

GH_USER = os.environ.get("GH_USER", "seko2077")
stats   = fetch_stats(GH_USER) or {"followers": 3, "following": 7, "repos": 4}
print(f"Stats: {stats}")

# ── Load Font ───────────────────────────────────────────────────────────────
FONT_PATH = os.path.join(HERE, "fonts", "hacked-kerx.ttf")
font_b64 = ""
if os.path.exists(FONT_PATH):
    with open(FONT_PATH, "rb") as f:
        font_b64 = base64.b64encode(f.read()).decode("utf-8")

# ── Config ──────────────────────────────────────────────────────────────────
W     = 1200
H     = 520
LP    = 360   # left card width

CYN = "#22D3EE"
PRP = "#A855F7"
GRN = "#10B981"
ORG = "#FF9900"
RED = "#F05032"
PNK = "#EC4899"

PHRASES = [
    ("wabalabadubdub",                                CYN),
    ("Security Engineer",                             PRP),
    ("Vibe Coder",                                    GRN),
    ("Gamer",                                         ORG),
    ("Dressed to impress but stressed and depressed", RED),
    ("The more we f**k around the more we find out",  PNK),
]

PILLS = [
    ("Python",               "#EAB308", "#CA8A04"),
    ("AWS",                  "#FF9900", "#C2410C"),
    ("Docker",               "#38BDF8", "#0EA5E9"),
    ("PostgreSQL",           "#4F8DC1", "#2C5282"),
    ("Git",                  "#F05032", "#B91C1C"),
    ("Cybersecurity",        "#A855F7", "#7E22CE"),
    ("3D Printing",          "#F472B6", "#DB2777"),
    ("Electronics &amp; Robotics","#34D399","#059669"),
]


# ── CardSwap (phrase cycling) ────────────────────────────────────────────────
def card_swap(phrases, dur_each=3.0):
    total = dur_each * len(phrases)
    out   = ""
    for i, (phrase, col) in enumerate(phrases):
        t0   = i * dur_each
        hold = t0 + dur_each * 0.25
        fade = t0 + dur_each * 0.75
        t1   = (i + 1) * dur_each
        clamp = lambda v: min(max(v, 0.0), 1.0)
        kt  = ";".join(f"{clamp(v/total):.4f}" for v in [0, t0, hold, fade, t1, total])
        tyv = ";".join(f"0,{y}" for y in ["14","14","0","0","-14","-14"])
        out += f"""
    <g opacity="0" font-size="24" font-weight="800"
       font-family="'Courier New',monospace" fill="{col}">
      <animateTransform attributeName="transform" type="translate"
        values="{tyv}" keyTimes="{kt}" dur="{total:.1f}s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0;0;1;1;0;0"
               keyTimes="{kt}" dur="{total:.1f}s" repeatCount="indefinite"/>
      <text y="0">&gt;_ {phrase}</text>
    </g>"""
    return out


# ── Pills ────────────────────────────────────────────────────────────────────
def pills_svg(pills, bg):
    gdef = out = ""
    GAP, PH, PFS = 210, 46, 16
    for i, (label, c0, c1) in enumerate(pills):
        row, col = divmod(i, 3)
        px, py   = col * GAP, row * 64
        w        = max(len(label) * 11 + 38, 110)
        d        = 2.2 + i * 0.35
        gdef += f'<linearGradient id="pg{i}" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="{c0}"/><stop offset="100%" stop-color="{c1}"/></linearGradient>\n    '
        out  += f"""
      <g transform="translate({px},{py})">
        <rect width="{w}" height="{PH}" rx="9" fill="{bg}" stroke="url(#pg{i})" stroke-width="1.8">
          <animate attributeName="stroke-width" values="1.8;3.2;1.8" dur="{d:.1f}s" repeatCount="indefinite"/>
        </rect>
        <text x="{w//2}" y="{PH//2+6}" fill="url(#pg{i})" font-size="{PFS}" font-weight="800"
              text-anchor="middle" font-family="system-ui,-apple-system,sans-serif">{label}</text>
      </g>"""
    return gdef, out


# ── Main SVG generator ───────────────────────────────────────────────────────
def generate_svg(mode):
    dark   = (mode == "dark")
    bg     = "#040810" if dark else "#F0F4F8"
    panel2 = "#070D1A" if dark else "#F1F5F9"
    bdr    = "rgba(34,211,238,0.18)" if dark else "rgba(15,23,42,0.12)"
    bdrB   = "rgba(34,211,238,0.35)" if dark else "rgba(15,23,42,0.25)"
    tpri   = "#E8F4FF" if dark else "#0F172A"
    tmut   = "#4B6080" if dark else "#475569"
    scan_c = "rgba(0,0,0,0.30)" if dark else "rgba(0,0,0,0.04)"

    fol  = stats["followers"]
    fing = stats["following"]
    rep  = stats["repos"]

    pg, ps   = pills_svg(PILLS, bg)
    card_svg = card_swap(PHRASES)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <!-- Accent gradient -->
    <linearGradient id="acc" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%"   stop-color="{CYN}"><animate attributeName="stop-color" values="{CYN};{PRP};{GRN};{CYN}" dur="8s" repeatCount="indefinite"/></stop>
      <stop offset="100%" stop-color="{PRP}"><animate attributeName="stop-color" values="{PRP};{GRN};{CYN};{PRP}" dur="8s" repeatCount="indefinite"/></stop>
    </linearGradient>
    <style>
      @font-face {{
        font-family: 'Hacked';
        src: url('data:font/ttf;charset=utf-8;base64,{font_b64}') format('truetype');
      }}
    </style>
    <!-- Watch Dogs 1 style: monochrome glitch on name -->
    <!-- Layer 1: hard horizontal displacement that fires in bursts -->
    <filter id="wd-glitch" x="-8%" y="-40%" width="116%" height="180%">
      <!-- chromatic aberration: red channel shifted left -->
      <feOffset in="SourceGraphic" dx="-3" dy="0" result="r-shift"/>
      <!-- horizontal slice glitch -->
      <feTurbulence type="fractalNoise" baseFrequency="0.0 0.9" numOctaves="1"
                    seed="3" result="slice-n">
        <animate attributeName="seed" values="3;7;12;3" dur="3s" repeatCount="indefinite"/>
      </feTurbulence>
      <feDisplacementMap in="SourceGraphic" in2="slice-n" scale="0"
                         xChannelSelector="R" yChannelSelector="G" result="sliced">
        <!-- continuous aggressive virus glitch -->
        <animate attributeName="scale"
                 values="12;5;25;0;10;15;0;8;22;5;0;15;8;0;20;12"
                 dur="1.5s" repeatCount="indefinite"/>
      </feDisplacementMap>
      <!-- merge: sliced on top, base behind -->
      <feMerge>
        <feMergeNode in="SourceGraphic"/>
        <feMergeNode in="sliced"/>
      </feMerge>
    </filter>
    <!-- System melting virus glitch for whoami -->
    <filter id="melt-glitch" x="-20%" y="-40%" width="140%" height="180%">
      <!-- chromatic aberration -->
      <feOffset in="SourceGraphic" dx="-4" dy="1" result="shift1"/>
      <feOffset in="SourceGraphic" dx="4" dy="-1" result="shift2"/>
      <feMerge result="split">
        <feMergeNode in="shift1"/>
        <feMergeNode in="shift2"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
      <!-- vertical melt blur -->
      <feGaussianBlur in="split" stdDeviation="0 3" result="melt"/>
      <feTurbulence type="fractalNoise" baseFrequency="0.01 0.2" numOctaves="2" seed="5" result="noise">
        <animate attributeName="seed" values="1;20;40;1" dur="1s" repeatCount="indefinite"/>
      </feTurbulence>
      <feDisplacementMap in="melt" in2="noise" scale="15" xChannelSelector="R" yChannelSelector="G">
        <animate attributeName="scale" values="5;20;5;15;5;25;10;5" dur="1s" repeatCount="indefinite"/>
      </feDisplacementMap>
    </filter>
    <!-- Pill gradients -->
    {pg}
    <!-- Radial glows -->
    <radialGradient id="g-cyn" cx="50%" cy="50%" r="50%">
      <stop offset="0%"   stop-color="{CYN}" stop-opacity="0.28"/>
      <stop offset="100%" stop-color="{CYN}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="g-prp" cx="50%" cy="50%" r="50%">
      <stop offset="0%"   stop-color="{PRP}" stop-opacity="0.20"/>
      <stop offset="100%" stop-color="{PRP}" stop-opacity="0"/>
    </radialGradient>
    <!-- Dot grid -->
    <pattern id="dot-grid" width="28" height="28" patternUnits="userSpaceOnUse">
      <circle cx="14" cy="14" r="0.8" fill="{bdr}"/>
    </pattern>
    <!-- Scanlines -->
    <pattern id="scan" width="1" height="4" patternUnits="userSpaceOnUse">
      <rect width="{W}" height="1.5" fill="{scan_c}"/>
    </pattern>
    <!-- Wave distortion on name text (ASCIIText port) -->
    <filter id="wave" x="-5%" y="-60%" width="110%" height="220%">
      <feTurbulence type="fractalNoise" baseFrequency="0.02 0.12" numOctaves="2" result="n">
        <animate attributeName="baseFrequency" values="0.02 0.12;0.03 0.16;0.02 0.12" dur="5s" repeatCount="indefinite"/>
      </feTurbulence>
      <feDisplacementMap in="SourceGraphic" in2="n" scale="5" xChannelSelector="R" yChannelSelector="G"/>
    </filter>
    <!-- Glow -->
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="5" result="b"/>
      <feComposite in="SourceGraphic" in2="b" operator="over"/>
    </filter>
    <!-- Left panel right-edge fade -->
    <linearGradient id="lp-fade" x1="0" y1="0" x2="1" y2="0">
      <stop offset="75%" stop-color="{panel2}" stop-opacity="1"/>
      <stop offset="100%" stop-color="{panel2}" stop-opacity="0"/>
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="{W}" height="{H}" fill="{bg}"/>
  <rect width="{W}" height="{H}" fill="url(#dot-grid)"/>
  <!-- Ambient orbs -->
  <ellipse cx="{LP//2}" cy="{H//2}" rx="320" ry="280" fill="url(#g-cyn)" opacity="0.9">
    <animate attributeName="rx" values="320;380;320" dur="12s" repeatCount="indefinite"/>
  </ellipse>
  <ellipse cx="{W-180}" cy="{H//2}" rx="360" ry="260" fill="url(#g-prp)" opacity="0.8">
    <animate attributeName="rx" values="360;420;360" dur="10s" repeatCount="indefinite"/>
  </ellipse>
  <!-- Scanlines -->
  <rect width="{W}" height="{H}" fill="url(#scan)"/>
  <!-- Sweep beam (FaultyTerminal) -->
  <rect x="0" y="-3" width="{W}" height="2" fill="{CYN}" opacity="0.05">
    <animate attributeName="y" values="-3;{H+3};-3" dur="7s" repeatCount="indefinite"/>
  </rect>
  <!-- Top accent bar -->
  <rect x="0" y="0" width="{W}" height="4" fill="url(#acc)">
    <animate attributeName="opacity" values="0.7;1;0.7" dur="3s" repeatCount="indefinite"/>
  </rect>

  <!-- ── LEFT CARD ── -->
  <rect x="0" y="0" width="{LP}" height="{H}" fill="{bg}" opacity="0.55"/>
  <rect x="{LP-4}" y="0" width="4" height="{H}" fill="url(#lp-fade)"/>
  <line x1="{LP}" y1="0" x2="{LP}" y2="{H}" stroke="{bdrB}" stroke-width="1.5"/>

  <!-- Name — Watch Dogs 1: Virus glitch sequence -->
  <g font-family="'Hacked', 'Impact', sans-serif" text-anchor="middle" letter-spacing="2">
    
    <!-- State 1: HI, I'M SAIF (0s - 5s) -->
    <text x="{LP//2}" y="80" font-size="48" font-weight="900" fill="#ffffff" filter="url(#wd-glitch)">
      HI, I'M SAIF
      <animate attributeName="opacity" values="1; 1; 0; 0; 1" keyTimes="0; 0.45; 0.451; 0.999; 1" dur="11s" repeatCount="indefinite"/>
    </text>

    <!-- State 2: whoami (5s - 8s) -->
    <text x="{LP//2}" y="80" font-size="48" font-weight="900" fill="#00FF00" filter="url(#melt-glitch)">
      whoami
      <animate attributeName="opacity" values="0; 0; 1; 1; 0; 0" keyTimes="0; 0.45; 0.451; 0.726; 0.727; 1" dur="11s" repeatCount="indefinite"/>
    </text>

    <!-- State 3: S A I F (8s - 11s) -->
    <text x="{LP//2}" y="80" font-size="56" font-weight="900" fill="#CC0000" filter="url(#wd-glitch)">
      S A I F
      <animate attributeName="opacity" values="0; 0; 1; 1; 0" keyTimes="0; 0.726; 0.727; 0.999; 1" dur="11s" repeatCount="indefinite"/>
    </text>

  </g>
  <!-- ctOS bracket decorators -->
  <text x="{LP//2 - 140}" y="70" font-family="'Courier New',monospace"
        font-size="22" fill="#ffffff" opacity="0.25" font-weight="400">[</text>
  <text x="{LP//2 + 126}" y="70" font-family="'Courier New',monospace"
        font-size="22" fill="#ffffff" opacity="0.25" font-weight="400">]</text>

  <text x="{LP//2}" y="106" text-anchor="middle"
        font-family="'Courier New',monospace"
        font-size="18" fill="{CYN}" font-weight="700" letter-spacing="2"
        filter="url(#glow)">@seko2077</text>

  <text x="{LP//2}" y="130" text-anchor="middle"
        font-family="system-ui,-apple-system,sans-serif"
        font-size="14" fill="{tmut}">&#127757; Earth C-137</text>

  <line x1="28" y1="150" x2="{LP-28}" y2="150" stroke="{bdrB}" stroke-width="1"/>

  <!-- Stats — evenly centered in thirds of LP and pushed down to vertical center -->
  <g font-family="system-ui,-apple-system,sans-serif" text-anchor="middle">
    <g transform="translate({LP//6}, 290)">
      <text font-size="44" font-weight="900" fill="{CYN}" filter="url(#glow)">{fol}</text>
      <text y="36" font-size="13" fill="{tmut}">followers</text>
    </g>
    <g transform="translate({LP//2}, 290)">
      <text font-size="44" font-weight="900" fill="{PRP}" filter="url(#glow)">{fing}</text>
      <text y="36" font-size="13" fill="{tmut}">following</text>
    </g>
    <g transform="translate({LP*5//6}, 290)">
      <text font-size="44" font-weight="900" fill="{GRN}" filter="url(#glow)">{rep}</text>
      <text y="36" font-size="13" fill="{tmut}">repos</text>
    </g>
  </g>

  <!-- Live badge -->
  <g transform="translate({LP//2 - 65}, {H - 52})">
    <rect width="130" height="28" rx="14" fill="{bg}" stroke="{bdrB}" stroke-width="1"/>
    <circle cx="18" cy="14" r="4" fill="{GRN}">
      <animate attributeName="opacity" values="0.4;1;0.4" dur="2s" repeatCount="indefinite"/>
    </circle>
    <text x="68" y="18.5" text-anchor="middle" font-size="12"
          font-family="'Courier New',monospace" fill="{tmut}">live · 6h refresh</text>
  </g>

  <!-- ── RIGHT PANEL ── -->
  <g transform="translate({LP + 44}, 32)">

    <!-- CardSwap phrases -->
    {card_svg}

    <!-- Bio -->
    <g transform="translate(0, 46)" font-size="17" fill="{tmut}"
       font-family="system-ui,-apple-system,sans-serif">
      <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.6s" begin="0.3s" fill="freeze"/>
        <text y="0"><tspan fill="{CYN}" font-family="'Courier New',monospace" font-weight="700">&#9733;</tspan>
          <tspan font-weight="700" fill="{tpri}"> Focus: </tspan>Security Engineering &amp; Breaking Things</text></g>
      <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.6s" begin="0.8s" fill="freeze"/>
        <text y="32"><tspan fill="{PRP}" font-family="'Courier New',monospace" font-weight="700">&#9733;</tspan>
          <tspan font-weight="700" fill="{tpri}"> Learning: </tspan>Red-teaming, Cloud Security, CTFs</text></g>
      <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.6s" begin="1.3s" fill="freeze"/>
        <text y="64"><tspan fill="{GRN}" font-family="'Courier New',monospace" font-weight="700">&#9733;</tspan>
          <tspan font-weight="700" fill="{tpri}"> Off-duty: </tspan>Gaming &amp; vibing to music</text></g>
      <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.6s" begin="1.8s" fill="freeze"/>
        <text y="96"><tspan fill="{ORG}" font-family="'Courier New',monospace" font-weight="700">&#9733;</tspan>
          <tspan font-weight="700" fill="{tpri}"> Bio: </tspan>Just a humble stranger &#128591;</text></g>
    </g>

    <!-- Arsenal -->
    <g transform="translate(0, 210)" opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.8s" begin="2.2s" fill="freeze"/>
      <line x1="0" y1="-6" x2="820" y2="-6" stroke="{bdr}" stroke-width="0.8"/>
      <text font-size="13" font-weight="700" fill="{CYN}"
            font-family="'Courier New',monospace" letter-spacing="5">ARSENAL</text>
      <g transform="translate(0, 18)">{ps}</g>
    </g>

    <!-- GitHub link -->
    <g transform="translate(0, {H - 52})" opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.8s" begin="2.8s" fill="freeze"/>
      <line x1="0" y1="0" x2="820" y2="0" stroke="{bdrB}" stroke-width="1"/>
      <g transform="translate(0, 18)" font-family="'Courier New',monospace" font-size="14">
        <circle cx="8" cy="-1" r="5" fill="{GRN}" filter="url(#glow)">
          <animate attributeName="opacity" values="0.5;1;0.5" dur="2s" repeatCount="indefinite"/>
        </circle>
        <text x="22" y="0" fill="{tmut}">github.com/<tspan fill="{CYN}" font-weight="700">seko2077</tspan></text>
      </g>
    </g>

  </g>

</svg>"""

    out = os.path.join(HERE, f"seko6_{mode}.svg")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"  wrote {out}  ({W}x{H})")


generate_svg("dark")
generate_svg("light")
print("Done.")
