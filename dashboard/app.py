"""Dashboard IRIS: status node, compliance rate, pelanggaran per waktu, dan event terbaru (Plotly Dash).

Jalankan dari root repo:  .venv\\Scripts\\python dashboard/app.py   lalu buka http://127.0.0.1:8050
Data dari MQTT (lihat store.py). Untuk demo tanpa kamera: vision/sim_publisher.py.
"""

import time
from datetime import datetime

import plotly.graph_objects as go
from dash import ALL, Dash, Input, Output, ctx, dcc, html, no_update

from store import Store

NODES = ["gate1", "zoneA"]  # node ESP32 yang ditampilkan (sama dengan firmware/src/config.h)
BIN_S = 30           # lebar bin grafik (detik)
WINDOW_S = 10 * 60   # rentang waktu grafik
STALE_S = 15         # status node lebih tua dari ini dianggap offline
HEARTBEAT_STALE_S = 5

# Warna (palet referensi dataviz): status untuk state, kategorikal untuk seri grafik
STATUS = {"good": "#0ca30c", "warning": "#fab219", "serious": "#ec835a", "critical": "#d03b3b", "neutral": "#898781"}
SERIES = {"compliance": "#2a78d6", "helmet": "#2a78d6", "vest": "#eb6834"}
INK, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"

STATE_VIEW = {  # state -> (kategori status, ikon, label Indonesia)
    "GRANTED": ("good", "✔", "Akses diberikan"),
    "NORMAL": ("good", "✔", "Zona aman"),
    "IDLE": ("neutral", "○", "Siap"),
    "WARNING": ("warning", "⚠", "Peringatan"),
    "DENIED": ("critical", "✖", "Akses ditolak"),
    "ALARM": ("critical", "✖", "Alarm"),
    "FAULT": ("serious", "⏻", "Gangguan vision"),
    "OFFLINE": ("neutral", "–", "Node offline"),
}
EVENT_LABEL = {"granted": "Izin masuk", "denied": "Ditolak", "warning": "Peringatan", "alarm": "Alarm",
               "cleared": "Patuh kembali", "fault": "Gangguan", "recovered": "Pulih"}
ITEM_LABEL = {"helmet": "Helm", "vest": "Rompi"}

store = Store()
app = Dash(__name__, title="IRIS Dashboard")


# ---------- Komponen ----------
def pill(text, kind):
    return html.Span(text, className=f"pill pill-{kind}")


def stat_tile(label, value, sub=""):
    return html.Div([html.Div(label, className="tile-label"), html.Div(value, className="tile-value"),
                     html.Div(sub, className="tile-sub")], className="tile")


def node_card(node):
    """Kerangka kartu: judul + tombol tetap (tidak digambar ulang), isi diperbarui tiap detik."""
    return html.Div([
        html.Div([html.Span(node, className="node-name"),
                  html.Button("Reset alarm", id={"type": "reset", "node": node}, className="btn")],
                 className="card-head"),
        html.Div(id={"type": "node-body", "node": node}),
    ], className="card")


def node_body(s, now):
    if s is None:
        s = {"state": "OFFLINE", "_rx": 0}
    age = now - s["_rx"]
    state = s.get("state", "OFFLINE") if age <= STALE_S else "OFFLINE"
    kind, icon, label = STATE_VIEW.get(state, ("neutral", "?", state))
    head = html.Div([html.Span(icon, className="state-icon"), html.Span(state, className="state-code"),
                     html.Span(label, className="state-label")], className=f"state state-{kind}")
    if "mode" not in s:  # belum ada status, atau pesan Last Will "OFFLINE" (hanya node & state)
        return [head, html.P("Belum ada status dari node ini sejak dashboard dibuka.", className="caption")]
    missing = ", ".join(ITEM_LABEL.get(m, m) for m in s.get("missing", [])) or "–"
    rows = [("Mode", f"{s.get('mode', '-')} · sumber {s.get('source', '-')}"),
            ("Palang", "terbuka" if s.get("gate") == "open" else "tertutup") if s.get("mode") == "gate" else
            ("Durasi pelanggaran", f"{s.get('violation_s', 0)} s"),
            ("Orang terdeteksi", str(s.get("person_count", "-"))),
            ("APD kurang", missing),
            ("Update terakhir", f"{age:.0f} s lalu" if age < 3600 else "data lama (retained)")]
    return [head, html.Table([html.Tr([html.Td(k, className="k"), html.Td(v)]) for k, v in rows], className="kv")]


def base_layout(fig, ytitle, now):
    fig.update_layout(
        template="plotly_white", height=300, margin=dict(l=48, r=16, t=8, b=40),
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif', size=12, color=INK),
        legend=dict(orientation="h", y=1.12, x=0, font=dict(color=MUTED), traceorder="normal"),
        hoverlabel=dict(bgcolor="white", bordercolor=AXIS, font=dict(color=INK)),
    )
    fig.update_xaxes(gridcolor=GRID, linecolor=AXIS, tickfont=dict(color=MUTED), showline=True, tickformat="%H:%M",
                     type="date", range=[datetime.fromtimestamp(now - WINDOW_S), datetime.fromtimestamp(now)])
    fig.update_yaxes(gridcolor=GRID, linecolor=AXIS, tickfont=dict(color=MUTED), title=dict(text=ytitle,
                     font=dict(color=MUTED)), zeroline=False)
    return fig


def empty_note(fig, text):
    fig.add_annotation(text=text, showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper",
                       font=dict(color=MUTED, size=13))
    return fig


def bins(now):
    start = int((now - WINDOW_S) // BIN_S * BIN_S)
    return list(range(start, int(now) + 1, BIN_S))


def compliance_figure(detections, now):
    edges = bins(now)
    totals = {b: [0, 0] for b in edges}
    for t, _node, persons, compliant in detections:
        b = int(t // BIN_S * BIN_S)
        if b in totals:
            totals[b][0] += persons
            totals[b][1] += compliant
    xs = [datetime.fromtimestamp(b) for b in edges if totals[b][0]]
    ys = [round(100 * totals[b][1] / totals[b][0], 1) for b in edges if totals[b][0]]
    fig = go.Figure(go.Scatter(x=xs, y=ys, mode="lines+markers", name="Compliance",
                               line=dict(color=SERIES["compliance"], width=2),
                               marker=dict(size=8, line=dict(color=SURFACE, width=2)),
                               hovertemplate="%{x|%H:%M:%S}<br>Compliance %{y:.1f}%<extra></extra>"))
    base_layout(fig, "% orang patuh", now)
    fig.update_yaxes(range=[0, 105])
    fig.update_layout(hovermode="x", showlegend=False)
    return fig if xs else empty_note(fig, "Menunggu data deteksi dari server vision…")


def violations_figure(events, now):
    edges = bins(now)
    counts = {item: {b: 0 for b in edges} for item in ITEM_LABEL}
    for e in events:
        if e.get("type") not in ("denied", "alarm"):
            continue
        b = int(e["_rx"] // BIN_S * BIN_S)
        for item in e.get("missing", []):
            if item in counts and b in counts[item]:
                counts[item][b] += 1
    xs = [datetime.fromtimestamp(b + BIN_S / 2) for b in edges]
    fig = go.Figure([go.Bar(x=xs, y=[counts[item][b] for b in edges], name=label,
                            marker=dict(color=SERIES[item], line=dict(color=SURFACE, width=2),
                                        cornerradius=4),
                            hovertemplate=f"%{{x|%H:%M:%S}}<br>{label} kurang: %{{y}}<extra></extra>")
                     for item, label in ITEM_LABEL.items()])
    base_layout(fig, "jumlah kejadian", now)
    fig.update_layout(barmode="stack", bargap=0.25)
    fig.update_yaxes(rangemode="tozero", dtick=1)
    total = sum(sum(c.values()) for c in counts.values())
    return fig if total else empty_note(fig, "Belum ada pelanggaran (event denied/alarm)")


# ---------- Layout ----------
app.layout = html.Div([
    html.Header([
        html.Div([html.H1("IRIS"), html.Span("Dashboard Kepatuhan APD · Tim Montblanc", className="subtitle")]),
        html.Div(id="conn", className="conn"),
    ], className="header"),
    html.Div(id="tiles", className="tiles"),
    html.Div([node_card(n) for n in NODES], className="nodes"),
    html.Div(id="toast", className="toast"),
    html.Div([
        html.Div([html.H2("Compliance rate"), html.P(f"Persentase orang terdeteksi yang memakai helm dan rompi, per {BIN_S} detik",
                                                     className="caption"),
                  dcc.Graph(id="g-compliance", config={"displayModeBar": False})], className="panel"),
        html.Div([html.H2("Pelanggaran per waktu"), html.P(f"Event ditolak/alarm menurut APD yang kurang, per {BIN_S} detik",
                                                           className="caption"),
                  dcc.Graph(id="g-violations", config={"displayModeBar": False})], className="panel"),
    ], className="charts"),
    html.Div([html.H2("Event terbaru"), html.Div(id="events")], className="panel"),
    dcc.Interval(id="tick", interval=1000),
], className="page")


@app.callback(Output("conn", "children"), Output("tiles", "children"),
              Output({"type": "node-body", "node": ALL}, "children"),
              Output("g-compliance", "figure"), Output("g-violations", "figure"), Output("events", "children"),
              Input("tick", "n_intervals"))
def refresh(_):
    snap, now = store.snapshot(), time.time()

    hb = snap["heartbeat"]
    vision_on = hb is not None and now - hb["_rx"] <= HEARTBEAT_STALE_S
    conn = [pill("✔ Broker terhubung" if snap["connected"] else "✖ Broker terputus",
                 "good" if snap["connected"] else "critical"),
            pill("✔ Server vision online" if vision_on else "⏻ Server vision offline", "good" if vision_on else "serious")]

    persons = sum(d[2] for d in snap["detections"] if d[0] >= snap["started"])
    compliant = sum(d[3] for d in snap["detections"] if d[0] >= snap["started"])
    events = snap["events"]
    count = lambda *types: sum(1 for e in events if e.get("type") in types)  # noqa: E731
    tiles = [
        stat_tile("Compliance rate sesi", f"{100 * compliant / persons:.0f}%" if persons else "–",
                  f"dari {persons} deteksi orang" if persons else "belum ada deteksi"),
        stat_tile("Pelanggaran", str(count("denied", "alarm")), "event ditolak + alarm"),
        stat_tile("Izin masuk", str(count("granted")), "palang dibuka"),
        stat_tile("Server vision", f"{hb.get('fps', 0):.1f} FPS" if vision_on else "offline",
                  f"heartbeat {now - hb['_rx']:.0f} s lalu" if hb else "belum ada heartbeat"),
    ]

    nodes = [node_body(snap["nodes"].get(n), now) for n in NODES]

    rows = [html.Tr([html.Th(h) for h in ("Waktu", "Node", "Kejadian", "APD kurang", "Orang", "Durasi (s)")])]
    for e in reversed(events[-12:]):
        rows.append(html.Tr([html.Td(datetime.fromtimestamp(e["_rx"]).strftime("%H:%M:%S")), html.Td(e["node"]),
                             html.Td(EVENT_LABEL.get(e.get("type"), e.get("type"))),
                             html.Td(", ".join(ITEM_LABEL.get(m, m) for m in e.get("missing", [])) or "–"),
                             html.Td(e.get("person_count", "–")), html.Td(e.get("duration_s", "–"))]))
    table = html.Table(rows, className="events") if events else html.P("Belum ada event.", className="caption")

    return conn, tiles, nodes, compliance_figure(snap["detections"], now), violations_figure(events, now), table


@app.callback(Output("toast", "children"), Input({"type": "reset", "node": ALL}, "n_clicks"),
              prevent_initial_call=True)
def reset_clicked(clicks):
    if not ctx.triggered_id or not any(clicks):
        return no_update
    node = ctx.triggered_id["node"]
    store.send_reset(node)
    return f"Perintah reset dikirim ke {node} ({datetime.now():%H:%M:%S})"


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8050)
