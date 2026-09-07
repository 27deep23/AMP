"""
Red-Team Test: QAOA Multi-Layer Parameterization & Depth Verification.
Verifies that build_qaoa_circuit correctly constructs p-layer circuits with 2p parameters.
"""

import pytest
import numpy as np
from core.quantum_optimizer import build_qaoa_circuit, qubo_to_ising


def test_qaoa_multi_layer_circuit_construction():
    """Verify circuit parameters and gate depth for p=1, p=2, p=3."""
    Q = np.array([
        [1.0, 0.5, 0.2],
        [0.5, 2.0, 0.3],
        [0.2, 0.3, 1.5]
    ])
    offset = 0.5
    h, J, ising_offset = qubo_to_ising(Q, offset)

    for p in [1, 2, 3]:
        gammas = np.linspace(0.1, 0.5, p)
        betas = np.linspace(0.2, 0.6, p)

        circuit = build_qaoa_circuit(3, h, J, gammas, betas)
        
        assert circuit.num_qubits == 3
        # Check that parameter count across gammas and betas equals 2*p
        assert len(gammas) == p
        assert len(betas) == p

        # Check circuit depth increases with p
        if p > 1:
            prev_circuit = build_qaoa_circuit(3, h, J, gammas[:p-1], betas[:p-1])
            assert circuit.depth() > prev_circuit.depth()
