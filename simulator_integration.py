"""
Integration module between Orion Finance simulator and Dash visualization.
"""

import asyncio
import logging
import threading
from queue import Queue
from typing import Any, Dict

from main import Simulation

logger = logging.getLogger("Orion App")

class SimulatorState:
    def __init__(self):
        self.vault_states = {}
        self.worker_state = {}
        self.metavault_state = {}
        self.curator_states = {}
        self.last_nonzero_tvl = {}  # Track last non-zero TVL for each vault
        self.latest_returns = []  # Track latest R_t values for histogram
        self._state_queue = Queue()
        self._running = False
        self._simulation_thread = None

    def update_state(self, node_type: str, node_name: str, state: Dict[str, Any]):
        """Update the state of a specific node."""
        if node_type == "vault":
            self.vault_states[node_name] = state
            # Track non-zero TVL values
            tvl = state.get("tvl", 0)
            if tvl > 0:
                self.last_nonzero_tvl[node_name] = tvl
        elif node_type == "worker":
            self.worker_state = state
            # Track R_t values if available
            if "latest_returns" in state:
                self.latest_returns = state["latest_returns"]
        elif node_type == "metavault":
            self.metavault_state = state
        elif node_type == "curator":
            # Store encrypted portfolio as a string
            encrypted_portfolio = state.get("portfolio", b"").hex()
            self.curator_states[node_name] = {"encrypted_portfolio": encrypted_portfolio}

        # Put the updated state in the queue for the Dash app
        self._state_queue.put(self.get_state())

    def get_state(self) -> Dict[str, Any]:
        """Get the current state of the simulation."""
        # Create a clean copy of vault states without the encrypted data
        clean_vault_states = {}
        for vault_name, state in self.vault_states.items():
            current_tvl = float(state.get("tvl", 0))
            # Use last non-zero TVL if current is zero
            display_tvl = current_tvl if current_tvl > 0 else self.last_nonzero_tvl.get(vault_name, current_tvl)
            
            clean_state = {
                "tvl": display_tvl  # Ensure it's a float
            }
            clean_vault_states[vault_name] = clean_state

        # Clean worker state
        clean_worker_state = {}
        if self.worker_state:
            portfolios_matrix = self.worker_state.get("portfolios_matrix")
            if portfolios_matrix is not None:
                # Convert pandas DataFrame to dict of lists
                clean_worker_state["portfolios_matrix"] = {
                    "columns": portfolios_matrix.columns.tolist(),
                    "data": portfolios_matrix.values.tolist(),
                }
            # Include latest returns for histogram
            clean_worker_state["latest_returns"] = self.latest_returns

        # Clean metavault state
        clean_metavault_state = {}
        if self.metavault_state:
            final_portfolio = self.metavault_state.get("final_portfolio")
            if final_portfolio is not None:
                clean_metavault_state["final_portfolio"] = {
                    "labels": final_portfolio.index.tolist(),
                    "values": final_portfolio.values.tolist(),
                }

        # Clean curator states
        clean_curator_states = {}
        for curator_name, state in self.curator_states.items():
            clean_curator_states[curator_name] = {
                "encrypted_portfolio": state.get("encrypted_portfolio", "N/A")
            }

        return {
            "vault_states": clean_vault_states,
            "worker_state": clean_worker_state,
            "metavault_state": clean_metavault_state,
            "curator_states": clean_curator_states,
        }

    def get_next_state(self) -> Dict[str, Any]:
        """Get the next state from the queue."""
        try:
            return self._state_queue.get_nowait()
        except:
            return self.get_state()

    def start_simulation(self, graph):
        """Start the simulation in a separate thread."""
        if self._running:
            return

        self._running = True
        self._simulation_thread = threading.Thread(
            target=self._run_simulation, args=(graph,), daemon=True
        )
        self._simulation_thread.start()

    def _run_simulation(self, graph):
        """Run the simulation in a separate thread."""

        async def run():
            sim = Simulation(graph)
            
            # Set up callback for worker state updates
            worker_state = sim.graph.nodes["OrionWorker"]["state"]
            worker_state['update_callback'] = self.update_state
            
            # Override the send_to and recv_from methods to capture state updates
            original_send_to = sim.send_to
            original_recv_from = sim.recv_from

            async def new_send_to(target, msg):
                # Update state based on message type
                if msg["type"] == "vault_state":
                    self.update_state("vault", msg["from"], msg["state"])
                elif msg["type"] == "final_portfolio":
                    self.update_state(
                        "metavault", "MetaVault", {"final_portfolio": msg["portfolio"]}
                    )

                await original_send_to(target, msg)

            async def new_recv_from(target):
                msg = await original_recv_from(target)

                # Update state based on received message
                if msg["type"] == "curator_action":
                    self.update_state(
                        "curator",
                        msg["from"],
                        {"portfolio": msg["encrypted_portfolio"]},
                    )

                return msg

            sim.send_to = new_send_to
            sim.recv_from = new_recv_from

            try:
                await sim.start()
            except Exception as e:
                logger.error(f"Simulation error: {str(e)}", exc_info=True)
                self._running = False

        # Run the async simulation
        asyncio.run(run())


# Create a global simulator state instance
simulator_state = SimulatorState()
