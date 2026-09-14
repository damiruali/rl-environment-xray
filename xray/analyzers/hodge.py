"""Experimental incidence projection. See docs/HODGE_NOTES.md for qualifications."""

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import lsqr


def analyze(graph):
    nodes = {node: i for i, node in enumerate(graph)}
    edges = list(graph.edges(keys=True, data=True))
    rr, cc, vv = [], [], []
    for i, (u, v, _, _) in enumerate(edges):
        rr.extend([i, i])
        cc.extend([nodes[u], nodes[v]])
        vv.extend([-1.0, 1.0])
    incidence = coo_matrix((vv, (rr, cc)), shape=(len(edges), len(nodes))).tocsr()
    rewards = np.array([edge[3]["reward"] for edge in edges])
    solution = lsqr(incidence, rewards, atol=1e-11, btol=1e-11, iter_lim=max(100, len(nodes) * 5))
    gradient = incidence @ solution[0]
    residual = rewards - gradient
    energy = float(rewards @ rewards)
    strongest = np.argsort(abs(residual))[::-1][:5]
    return {
        "experimental": True,
        "affects_gate": False,
        "residual_energy_ratio": float(residual @ residual) / energy if energy else 0.0,
        "orthogonality_error": float(np.linalg.norm(incidence.T @ residual)),
        "solver_stop_code": solution[1],
        "iterations": solution[2],
        "strongest_edges": [
            {
                "source": edges[i][0],
                "target": edges[i][1],
                "action": edges[i][3]["action"],
                "residual": float(residual[i]),
            }
            for i in strongest
        ],
        "limitation": "Algebraic cycle-space residual is not a directed exploitable-cycle proof; gradient is not necessarily business progress.",
    }
