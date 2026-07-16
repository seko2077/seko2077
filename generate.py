"""
generate.py
-----------
Run locally:  python generate.py          → uses fallback stats
Run in CI:    GH_TOKEN=xxx GH_USER=seko2077 python generate.py
              → fetches real follower/following/repo count from GitHub API
"""

import base64, os, json, urllib.request, struct

# ── paths ───────────────────────────────────────────────────────────────────
HERE        = os.path.dirname(os.path.abspath(__file__))
AVATAR_PATH = os.path.join(HERE, "seko2077.png")

with open(AVATAR_PATH, "rb") as f:
    AVATAR_B64 = base64.b64encode(f.read()).decode()

# ── read real PNG size ───────────────────────────────────────────────────────
with open(AVATAR_PATH, "rb") as f:
    f.read(12)          # signature + IHDR length + "IHDR"
    IMG_W = struct.unpack(">I", f.read(4))[0]
    IMG_H = struct.unpack(">I", f.read(4))[0]
IMG_RATIO = IMG_W / IMG_H   # used to size the logo box without cropping

# ── fetch live GitHub stats (only in CI where GH_TOKEN is set) ──────────────
def fetch_github_stats(user):
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        return None
    try:
        req = urllib.request.Request(
            f"https://api.github.com/users/{user}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        return {
            "followers": data.get("followers", 0),
            "following": data.get("following", 0),
            "repos":     data.get("public_repos", 0),
        }
    except Exception as e:
        print(f"[warn] GitHub API error: {e}")
        return None

GH_USER = os.environ.get("GH_USER", "seko2077")
stats   = fetch_github_stats(GH_USER) or {"followers": 3, "following": 7, "repos": 2}
print(f"Stats: {stats}")

# ── config ───────────────────────────────────────────────────────────────────
PHRASES = [
    "wabalabadubdub",
    "Security Engineer",
    "Vibe Coder",
    "Gamer",
    "Dressed to impress but stressed and depressed",
    "The more we f**k around the more we find out",
]
CHAR_W = 10

ACCENT  = "#22D3EE"
ACCENT2 = "#A855F7"
ACCENT3 = "#10B981"
RED     = "#F05032"
ORANGE  = "#FF9900"
PINK    = "#EC4899"

W     = 1100
PAD   = 0            # logo flush to edges — full bleed
LOGO_H = round(W / IMG_RATIO)   # exact height so zero cropping

BOT_H  = 230
SVG_H  = LOGO_H + BOT_H
LP_BOT = 260         # left name card width in bottom strip

PILLS = [
    ("Python",        "#EAB308", "#CA8A04"),
    ("AWS",           "#FF9900", "#C2410C"),
    ("Docker",        "#38BDF8", "#0EA5E9"),
    ("PostgreSQL",    "#4F8DC1", "#2C5282"),
    ("Git",           "#F05032", "#B91C1C"),
    ("Cybersecurity", "#A855F7", "#7E22CE"),
]


# ── helpers ──────────────────────────────────────────────────────────────────
def typing_section(phrases, colors, dur=20):
    clamp = lambda v: min(max(v, 0.0), 1.0)
    n, step = len(phrases), 1.0 / len(phrases)
    defs = texts = ""
    for i, phrase in enumerate(phrases):
        t0, tf, tc, t1 = i*step, i*step+step*0.55, i*step+step*0.80, (i+1)*step
        kts = ";".join(f"{clamp(x):.4f}" for x in [0, t0, tf, tc, t1, 1.0])
        pw  = max(len(phrase) * CHAR_W + 12, 80)
        col = colors[i % len(colors)]
        defs  += f"""
    <clipPath id="tp{i}">
      <rect x="0" y="-22" height="32" width="0">
        <animate attributeName="width" values="0;0;{pw};{pw};0;0"
                 keyTimes="{kts}" dur="{dur}s" repeatCount="indefinite"/>
      </rect>
    </clipPath>"""
        texts += f'\n      <text fill="{col}" clip-path="url(#tp{i})">{phrase}</text>'
    return defs, texts


def build_pills(pills, bg):
    gdef = out = ""
    for i, (label, c0, c1) in enumerate(pills):
        row, col = divmod(i, 3)
        px, py = col * 185, row * 46
        w = max(len(label) * 9 + 28, 90)
        d = 2.2 + i * 0.35
        gdef += f'<linearGradient id="pg{i}" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="{c0}"/><stop offset="100%" stop-color="{c1}"/></linearGradient>\n    '
        out  += f"""
      <g transform="translate({px},{py})">
        <rect width="{w}" height="32" rx="6" fill="{bg}" stroke="url(#pg{i})" stroke-width="1.5">
          <animate attributeName="stroke-width" values="1.5;2.8;1.5" dur="{d:.1f}s" repeatCount="indefinite"/>
        </rect>
        <text x="{w//2}" y="21" fill="url(#pg{i})" font-size="13" font-weight="700"
              text-anchor="middle" font-family="system-ui,-apple-system,sans-serif">{label}</text>
      </g>"""
    return gdef, out


# ── SVG generator ────────────────────────────────────────────────────────────
def generate_svg(mode):
    dark   = (mode == "dark")
    bg     = "#060A10" if dark else "#F0F4F8"
    panel  = "#0D1421" if dark else "#FFFFFF"
    panel2 = "#080E1A" if dark else "#F1F5F9"
    border = "rgba(34,211,238,0.18)" if dark else "rgba(15,23,42,0.12)"
    bordB  = "rgba(34,211,238,0.30)" if dark else "rgba(15,23,42,0.22)"
    tpri   = "#E2F0FF" if dark else "#0F172A"
    tmut   = "#64748B" if dark else "#475569"
    scan_c = "rgba(0,0,0,0.28)" if dark else "rgba(0,0,0,0.04)"

    type_defs, type_texts = typing_section(PHRASES, [ACCENT, ACCENT2, ACCENT3, ORANGE, RED, PINK])
    pill_gdef, pill_svg   = build_pills(PILLS, bg)

    fol  = stats["followers"]
    fing = stats["following"]
    rep  = stats["repos"]

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {W} {SVG_H}" width="{W}" height="{SVG_H}">
  <defs>
    <linearGradient id="acc" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{ACCENT}">
        <animate attributeName="stop-color" values="{ACCENT};{ACCENT2};{ACCENT3};{ACCENT}" dur="8s" repeatCount="indefinite"/>
      </stop>
      <stop offset="100%" stop-color="{ACCENT2}">
        <animate attributeName="stop-color" values="{ACCENT2};{ACCENT3};{ACCENT};{ACCENT2}" dur="8s" repeatCount="indefinite"/>
      </stop>
    </linearGradient>
    <radialGradient id="orb1" cx="50%" cy="50%" r="50%">
      <stop offset="0%"   stop-color="{ACCENT}"  stop-opacity="0.25"/>
      <stop offset="100%" stop-color="{ACCENT}"  stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="orb2" cx="50%" cy="50%" r="50%">
      <stop offset="0%"   stop-color="{ACCENT2}" stop-opacity="0.20"/>
      <stop offset="100%" stop-color="{ACCENT2}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="logo-shadow" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="{bg}" stop-opacity="0"/>
      <stop offset="100%" stop-color="{bg}" stop-opacity="1"/>
    </linearGradient>
    <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
      <path d="M 30 0 L 0 0 0 30" fill="none" stroke="{border}" stroke-width="0.5"/>
    </pattern>
    <pattern id="scan" width="1" height="4" patternUnits="userSpaceOnUse">
      <rect width="{W}" height="1.5" fill="{scan_c}"/>
    </pattern>
    <filter id="noise-f">
      <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch" result="n"/>
      <feColorMatrix type="matrix" values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 0.06 0" in="n"/>
      <feBlend in="SourceGraphic" mode="overlay"/>
    </filter>
    <filter id="glow-sm" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="4" result="b"/>
      <feComposite in="SourceGraphic" in2="b" operator="over"/>
    </filter>
    {pill_gdef}
    {type_defs}
  </defs>

  <!-- background + grid -->
  <rect width="{W}" height="{SVG_H}" fill="{bg}"/>
  <rect width="{W}" height="{SVG_H}" fill="url(#grid)"/>

  <!-- ambient glow -->
  <ellipse cx="{W//2}" cy="{LOGO_H//2}" rx="520" ry="230" fill="url(#orb1)" opacity="0.9">
    <animate attributeName="rx" values="520;570;520" dur="12s" repeatCount="indefinite"/>
  </ellipse>
  <ellipse cx="{W-150}" cy="{LOGO_H + BOT_H//2}" rx="300" ry="140" fill="url(#orb2)" opacity="0.8">
    <animate attributeName="rx" values="300;350;300" dur="10s" repeatCount="indefinite"/>
  </ellipse>

  <!-- scanlines -->
  <rect width="{W}" height="{SVG_H}" fill="url(#scan)"/>
  <!-- sweep beam -->
  <rect x="0" y="-4" width="{W}" height="2" fill="{ACCENT}" opacity="0.06">
    <animate attributeName="y" values="-4;{SVG_H+4};-4" dur="7s" repeatCount="indefinite"/>
  </rect>

  <!-- ░░ TOP: FULL-BLEED LOGO (no clip, perfect aspect ratio) ░░ -->
  <image href="data:image/png;base64,{AVATAR_B64}"
         x="0" y="0" width="{W}" height="{LOGO_H}"
         preserveAspectRatio="xMidYMid meet"/>

  <!-- bottom shadow fade -->
  <rect x="0" y="{LOGO_H - 80}" width="{W}" height="80" fill="url(#logo-shadow)"/>

  <!-- top accent bar -->
  <rect x="0" y="0" width="{W}" height="3" fill="url(#acc)">
    <animate attributeName="opacity" values="0.6;1;0.6" dur="3s" repeatCount="indefinite"/>
  </rect>

  <!-- corner brackets -->
  <g stroke="{ACCENT}" stroke-width="2.5" fill="none" opacity="0.75">
    <polyline points="0,22 0,0 22,0"/>
    <polyline points="{W-22},0 {W},0 {W},22"/>
    <polyline points="0,{LOGO_H-22} 0,{LOGO_H} 22,{LOGO_H}"/>
    <polyline points="{W-22},{LOGO_H} {W},{LOGO_H} {W},{LOGO_H-22}"/>
  </g>

  <!-- ONLINE dot -->
  <circle cx="16" cy="16" r="5" fill="{ACCENT3}" filter="url(#glow-sm)">
    <animate attributeName="opacity" values="0.5;1;0.5" dur="1.8s" repeatCount="indefinite"/>
    <animate attributeName="r" values="4;6;4" dur="1.8s" repeatCount="indefinite"/>
  </circle>
  <text x="26" y="21" font-family="'Courier New',monospace" font-size="11"
        fill="{ACCENT3}" font-weight="700">ONLINE</text>

  <!-- divider -->
  <line x1="0" y1="{LOGO_H}" x2="{W}" y2="{LOGO_H}" stroke="url(#acc)" stroke-width="1.5" opacity="0.4"/>

  <!-- ░░ BOTTOM STRIP ░░ -->
  <rect x="0" y="{LOGO_H}" width="{W}" height="{BOT_H}" fill="{panel2}" opacity="0.92"/>

  <!-- LEFT: name + stats -->
  <g transform="translate(0, {LOGO_H})">
    <rect width="{LP_BOT}" height="{BOT_H}" fill="{bg}" opacity="0.45"/>
    <line x1="{LP_BOT}" y1="0" x2="{LP_BOT}" y2="{BOT_H}" stroke="{bordB}" stroke-width="1"/>

    <text x="{LP_BOT//2}" y="44" text-anchor="middle"
          font-family="system-ui,-apple-system,sans-serif"
          font-size="22" font-weight="900" fill="{tpri}">Hi, I'm Saif &#x1F44B;</text>
    <text x="{LP_BOT//2}" y="67" text-anchor="middle"
          font-family="'Courier New',monospace"
          font-size="13" fill="{ACCENT}" font-weight="600" letter-spacing="1.5">@seko2077</text>
    <text x="{LP_BOT//2}" y="88" text-anchor="middle"
          font-family="system-ui,-apple-system,sans-serif"
          font-size="12" fill="{tmut}">&#127757; Earth C-137</text>

    <line x1="20" y1="104" x2="{LP_BOT-20}" y2="104" stroke="{border}" stroke-width="1"/>

    <!-- LIVE stats (refreshed every 6h by GitHub Actions) -->
    <g font-family="system-ui,-apple-system,sans-serif" text-anchor="middle">
      <g transform="translate({LP_BOT//4 - 10}, 118)">
        <text font-size="24" font-weight="900" fill="{ACCENT}">{fol}</text>
        <text y="22" font-size="11" fill="{tmut}">followers</text>
      </g>
      <g transform="translate({LP_BOT//2}, 118)">
        <text font-size="24" font-weight="900" fill="{ACCENT2}">{fing}</text>
        <text y="22" font-size="11" fill="{tmut}">following</text>
      </g>
      <g transform="translate({LP_BOT*3//4 + 10}, 118)">
        <text font-size="24" font-weight="900" fill="{ACCENT3}">{rep}</text>
        <text y="22" font-size="11" fill="{tmut}">repos</text>
      </g>
    </g>
  </g>

  <!-- RIGHT: info panel -->
  <g transform="translate({LP_BOT + 32}, {LOGO_H + 18})">

    <!-- typing -->
    <g font-family="'Courier New',monospace" font-size="15" font-weight="700">
      <text fill="{ACCENT}" opacity="0.6">&#62;_</text>
      <g transform="translate(26, 0)">
        {type_texts}
        <rect x="0" y="-17" width="9" height="20" fill="{ACCENT}" rx="1">
          <animate attributeName="opacity" values="1;0;1" dur="0.65s" repeatCount="indefinite"/>
        </rect>
      </g>
    </g>

    <!-- bio -->
    <g transform="translate(0, 28)" font-size="13" fill="{tmut}"
       font-family="system-ui,-apple-system,sans-serif">
      <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.5s" begin="0.3s" fill="freeze"/>
        <text y="0"><tspan fill="{ACCENT}" font-family="'Courier New',monospace">&#9733;</tspan>
          <tspan font-weight="700" fill="{tpri}"> Focus: </tspan>Security Engineering &amp; Breaking Things</text></g>
      <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.5s" begin="0.7s" fill="freeze"/>
        <text y="22"><tspan fill="{ACCENT2}" font-family="'Courier New',monospace">&#9733;</tspan>
          <tspan font-weight="700" fill="{tpri}"> Learning: </tspan>Red-teaming, Cloud Security, CTFs</text></g>
      <g opacity="0"><animate attributeName="opacity" values="0;1" dur="0.5s" begin="1.1s" fill="freeze"/>
        <text y="44"><tspan fill="{ACCENT3}" font-family="'Courier New',monospace">&#9733;</tspan>
          <tspan font-weight="700" fill="{tpri}"> Off-duty: </tspan>Gaming &amp; vibing to music</text></g>
    </g>

    <!-- arsenal -->
    <g transform="translate(0, 108)" opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.8s" begin="1.4s" fill="freeze"/>
      <text font-size="11" font-weight="700" fill="{ACCENT}"
            font-family="'Courier New',monospace" letter-spacing="4">ARSENAL</text>
      <line x1="72" y1="-4" x2="810" y2="-4" stroke="{border}" stroke-width="0.7"/>
      <g transform="translate(0, 14)">{pill_svg}</g>
    </g>

  </g>

  <!-- noise overlay -->
  <rect width="{W}" height="{SVG_H}" fill="transparent" filter="url(#noise-f)"/>
</svg>"""

    out = os.path.join(HERE, f"{mode}.svg")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"  wrote {out}  ({W}x{SVG_H})")


generate_svg("dark")
generate_svg("light")
print("Done.")
