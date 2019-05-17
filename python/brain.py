import argparse
import graph as graph_mod
import math
import sys
import utility

TEMPLATES = {}
SIZE_RATE = 0.025
WEIGHT_THRESHOLD = 0.01

TEMPLATES["txt"] = {}
TEMPLATES["txt"]["graph"] = """
{nodes}
{edges}
""".lstrip()
TEMPLATES["txt"]["node"] = """node {i} {type}"""
TEMPLATES["txt"]["edge"] = """edge {i} {j} {w}"""

TEMPLATES["gv"] = {}
TEMPLATES["gv"]["graph"] = """
digraph {{
    outputorder=edgesfirst;
    node [fixedsize=true, label="", shape=circle, style=filled, width=0.075];
    edge [arrowhead=none];
{nodes}
{edges}
}}
""".lstrip()
TEMPLATES["gv"]["node"] = """    {i} [fillcolor="#{r:02x}{g:02x}{b:02x}", pos="{x:.3f},{y:.3f}!"];"""
TEMPLATES["gv"]["edge"] = """    {i} -> {j} [color="#000000{a:02x}"];"""

TEMPLATES["tex"] = {}
TEMPLATES["tex"]["graph"] = """
\\documentclass{{standalone}}
\\usepackage{{tikz}}
\\usetikzlibrary{{backgrounds}}
\\begin{{document}}
\\begin{{tikzpicture}}
    [
        every node/.style={{draw, circle, minimum size=0.075in, inner sep=0pt}}
    ]
{nodes}
    \\begin{{scope}}[on background layer]
{edges}
    \\end{{scope}}
\\end{{tikzpicture}}
\\end{{document}}
""".lstrip()
TEMPLATES["tex"]["node"] = """    \\node[fill={{rgb,255:red,{r};green,{g};blue,{b}}}] ({i}) at ({x:.3f}in,{y:.3f}in) {{}};"""
TEMPLATES["tex"]["edge"] = """        \\draw[-, color={{rgb,255:red,{r};green,{g};blue,{b}}}] ({i}) to ({j});"""

def setColor(kwargs, byte):
    kwargs.update({
        "r": byte,
        "g": byte,
        "b": byte
    })

def setPosition(kwargs, count, offset):
    size = count * SIZE_RATE
    angle = offset - 2 * math.pi * kwargs["i"] / count
    kwargs.update({
        "x": size * math.cos(angle),
        "y": size * math.sin(angle)
    })

parser = argparse.ArgumentParser()
parser.add_argument("run", metavar = "RUN")
parser.add_argument("agent", metavar = "AGENT", type = int)
parser.add_argument("stage", metavar = "STAGE", choices = ("incept", "birth", "death"))
parser.add_argument("format", metavar = "FORMAT", choices = ("txt", "gv", "tex"))
args = parser.parse_args()
graph = graph_mod.Graph.read(args.run, args.agent, args.stage, graph_mod.GraphType.ALL)
counts = utility.getNeuronCounts(args.run)[args.agent]
sector = 2 * math.pi / counts["Total"]
offset = math.pi / 2 + (counts["Input"] - 1) * sector / 2
nodes = []
edges = []
kwargs = {
    "i": 0
}
for nerve in utility.getNerves(args.run):
    if nerve in ("Red", "Green", "Blue"):
        kwargs["type"] = "Input-" + nerve
        setColor(kwargs, 128)
        kwargs[nerve[0].lower()] = 255
    elif kwargs["i"] < counts["Input"]:
        kwargs["type"] = "Input-Other"
        setColor(kwargs, 0)
    else:
        kwargs["type"] = "Output"
        setColor(kwargs, 255)
    for _ in xrange(counts[nerve]):
        setPosition(kwargs, counts["Total"], offset)
        nodes.append(TEMPLATES[args.format]["node"].format(**kwargs))
        kwargs["i"] += 1
setColor(kwargs, 192)
for _ in xrange(counts["Internal"]):
    kwargs["type"] = "Internal"
    setPosition(kwargs, counts["Total"], offset)
    nodes.append(TEMPLATES[args.format]["node"].format(**kwargs))
    kwargs["i"] += 1
weights = {}
for i in xrange(graph.size):
    for j in xrange(graph.size):
        weight = graph.weights[i][j]
        if weight is None or abs(weight) < WEIGHT_THRESHOLD:
            continue
        weights[(i, j)] = weight
kwargs = {}
for indices, weight in sorted(weights.iteritems(), key = lambda item: abs(item[1])):
    kwargs.update({
        "i": indices[0],
        "j": indices[1]
    })
    kwargs["w"] = weight
    alpha = int(256 * abs(weight))
    if alpha > 255:
        alpha = 255
    setColor(kwargs, 255 - alpha)
    kwargs["a"] = alpha
    edges.append(TEMPLATES[args.format]["edge"].format(**kwargs))
sys.stdout.write(TEMPLATES[args.format]["graph"].format(nodes = "\n".join(nodes), edges = "\n".join(edges)))
