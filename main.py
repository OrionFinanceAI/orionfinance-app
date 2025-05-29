import asyncio
import json
import logging
import os
import random
from datetime import datetime

import networkx as nx
import numpy as np
import pandas as pd
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from utils import N_VAULTS, UNIVERSE

# Configure logging
log_filename = f"orion_simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(),  # Also show logs in console
    ],
)

logger = logging.getLogger("OrionSimulation")


def encrypt_json_dict(aes_key: bytes, data: dict) -> bytes:
    json_str = json.dumps(data)
    data_bytes = json_str.encode("utf-8")

    nonce = os.urandom(12)  # 12 bytes nonce for AES-GCM
    aesgcm = AESGCM(aes_key)
    ciphertext = aesgcm.encrypt(nonce, data_bytes, None)

    # Return nonce + ciphertext
    return nonce + ciphertext


def decrypt_json_dict(aes_key: bytes, encrypted_data: bytes) -> dict:
    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]

    aesgcm = AESGCM(aes_key)
    decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)

    json_str = decrypted_bytes.decode("utf-8")
    return json.loads(json_str)


keys_array = [os.urandom(32) for _ in range(N_VAULTS)]


def build_graph():
    G = nx.DiGraph()

    # Add Curators
    for i in range(N_VAULTS):
        G.add_node(f"Curator{i + 1}", type="curator", state={"key": keys_array[i]})

    # Add Vaults
    tvls_array=np.random.uniform(10000, 1000000, N_VAULTS)
    tvls_array=tvls_array/np.sum(tvls_array)*100
    for i in range(N_VAULTS):
        G.add_node(
            f"Vault{i + 1}",
            type="vault",
            state={
                "tvl": tvls_array[i],
                "internal_ledger_last_state": None,
            },
        )

    G.add_node(
        "OrionWorker",
        type="worker",
        state={
            "key_array": keys_array,
            "portfolios_matrix": None,
        },
    )
    G.add_node(
        "MetaVault",
        type="metavault",
        state={"final_portfolio": None},
    )

    for i in range(N_VAULTS):
        G.add_edge(f"Curator{i + 1}", f"Vault{i + 1}")
        G.add_edge("OrionWorker", f"Vault{i + 1}")
    G.add_edge("OrionWorker", "MetaVault")

    return G


async def curator_node(name, state, send_to, recv_from):
    while True:
        # Wait for clock tick
        await asyncio.sleep(random.uniform(5, 6))

        n_assets = random.randint(1, len(UNIVERSE))
        assets = random.sample(UNIVERSE, n_assets)

        weights = [random.uniform(0, 1) for _ in range(n_assets)]
        weights = [w / sum(weights) for w in weights]

        portfolio = {asset: weights[i] for i, asset in enumerate(assets)}
        encrypted_portfolio = encrypt_json_dict(state["key"], portfolio)

        await send_to(
            name.replace("Curator", "Vault"),
            {
                "from": name,
                "type": "curator_action",
                "encrypted_portfolio": encrypted_portfolio,
            },
        )
        logger.info(f"[{name}] Sent encrypted portfolio to vault")


async def vault_node(name, state, send_to, recv_from):
    while True:
        msg = await recv_from(name)
        logger.info(f"[{name}] Received message of type: {msg['type']}")

        if msg["type"] == "curator_action":
            logger.info(f"[{name}] Received encrypted portfolio from {msg['from']}")
            state["internal_ledger_last_state"] = msg["encrypted_portfolio"]
            logger.info(f"[{name}] Stored encrypted portfolio")

        elif msg["type"] == "worker_request":
            logger.info(f"[{name}] Sending state to worker")
            await send_to(
                "OrionWorker", {"from": name, "type": "vault_state", "state": state}
            )

        elif msg["type"] == "tvl_transfer":
            logger.info(f"[{name}] Current TVL: {state['tvl']:.2f}")
            transfer_amount = msg["amount"]
            # Check if transfer would make`` TVL negative
            if transfer_amount > state["tvl"]:
                logger.warning(
                    f"[{name}] Rejected transfer: would make TVL negative"
                )
                transfer_amount = state["tvl"]  # Only transfer what's available
            state["tvl"] -= transfer_amount
            logger.info(
                f"[{name}] Transferred {transfer_amount:.2f} from idle to active TVL"
            )
            logger.info(f"[{name}] New TVL: {state['tvl']:.2f}")

        elif msg["type"] == "update_tvl":
            logger.info(f"[{name}] Current TVL: {state['tvl']:.2f}")
            state["tvl"] = msg["amount"]
            logger.info(f"[{name}] Updated TVL to: {state['tvl']:.2f}")


async def worker_node(name, state, send_to, recv_from, worker_clock):
    while True:
        logger.info("[OrionWorker] Starting new cycle")
        # Wait for clock tick
        await asyncio.sleep(5)

        if state["portfolios_matrix"] is not None:
            # "Measure" ERC4626 performance
            R_t = np.random.normal(
                loc=0.01, scale=0.03, size=state["portfolios_matrix"].shape[0]
            )
            logger.info(f"[OrionWorker] ERC4626 performance: {R_t}")
            
            # Store latest returns for visualization
            state["latest_returns"] = R_t.tolist()
            
            # Notify external state tracking if callback exists
            if 'update_callback' in state and callable(state['update_callback']):
                state['update_callback']("worker", name, state)

            # Compute ERC4626 performance
            PandL_t = state["portfolios_matrix"].T.dot(R_t).to_numpy()
            logger.info(f"[OrionWorker] ERC4626 performance: {PandL_t}")

            active_tvl = state["portfolios_matrix"].sum(axis=0).to_numpy()
            logger.info(f"[OrionWorker] Active TVL: {active_tvl}")

            updated_tvl = active_tvl + PandL_t
            logger.info(f"[OrionWorker] Updated TVL: {updated_tvl}")

            # Update each vault's TVL with the corresponding updated TVL
            for i, tvl in enumerate(updated_tvl):
                vault_name = f"Vault{i + 1}"
                logger.info(
                    f"[OrionWorker] Updating {vault_name} TVL to {tvl:.2f}"
                )
                await send_to(vault_name, {"type": "update_tvl", "amount": tvl})

        # Request states from all vaults
        logger.info("[OrionWorker] Requesting states from all vaults")
        vault_states = {}
        for i in range(N_VAULTS):
            vault_name = f"Vault{i + 1}"
            await send_to(vault_name, {"type": "worker_request"})

        # Collect responses from all vaults
        logger.info("[OrionWorker] Collecting vault states")
        for _ in range(N_VAULTS):
            msg = await recv_from(name)
            if msg["type"] == "vault_state":
                vault_states[msg["from"]] = msg["state"]
                logger.info(f"[OrionWorker] Received state from {msg['from']}")

        logger.info(f"[OrionWorker] Processing {len(vault_states)} vault states")

        # First, process all portfolios and create the matrix
        portfolio_dfs = []
        for vault_name, vault_state in vault_states.items():
            logger.info(f"[OrionWorker] Processing {vault_name}")
            logger.info(
                f"[OrionWorker] Current TVL: {vault_state['tvl']:.2f}"
            )

            if vault_state["internal_ledger_last_state"]:
                curator_idx = int(vault_name.replace("Vault", "")) - 1
                curator_key = state["key_array"][curator_idx]
                portfolio = decrypt_json_dict(
                    curator_key, vault_state["internal_ledger_last_state"]
                )

                # Create portfolio dataframe
                df = pd.DataFrame.from_dict(
                    portfolio, orient="index", columns=["weight"]
                )

                # Transfer TVL from idle to active
                transfer_amount = vault_state["tvl"]
                if transfer_amount > 0:
                    logger.info(
                        f"[OrionWorker] Initiating transfer of {transfer_amount:.2f}"
                    )
                    await send_to(
                        vault_name, {"type": "tvl_transfer", "amount": transfer_amount}
                    )
                    logger.info(f"[OrionWorker] Sent transfer request to {vault_name}")

                    # Weight portfolio by TVL
                    df = df * transfer_amount
                    portfolio_dfs.append(df)
                    logger.info(
                        f"[OrionWorker] Added portfolio from {vault_name} with TVL {transfer_amount:.2f}"
                    )
            else:
                logger.info(f"[OrionWorker] No portfolio found for {vault_name}")

        # Update worker state with portfolios matrix and total TVL
        if portfolio_dfs:
            logger.info("[OrionWorker] Creating portfolios matrix")
            state["portfolios_matrix"] = pd.concat(portfolio_dfs, axis=1).fillna(0)
            logger.info(
                f"[OrionWorker] Portfolios matrix created with shape: {state['portfolios_matrix'].shape}"
            )

            # Compute final portfolio
            final_portfolio = state["portfolios_matrix"].sum(axis=1)
            logger.info(f"[OrionWorker] Final portfolio computed:\n{final_portfolio}")

            # Send final portfolio to metavault
            await send_to(
                "MetaVault",
                {
                    "type": "final_portfolio",
                    "portfolio": final_portfolio,
                },
            )
            logger.info("[OrionWorker] Sent final portfolio to MetaVault")
        else:
            logger.info("[OrionWorker] No portfolios to create matrix")
            state["portfolios_matrix"] = None


async def metavault_node(name, state, send_to, recv_from):
    while True:
        msg = await recv_from(name)
        logger.info(f"[{name}] Received message of type: {msg['type']}")

        if msg["type"] == "final_portfolio":
            logger.info(f"[{name}] Received final portfolio")
            state["final_portfolio"] = msg["portfolio"]
            logger.info(
                f"[{name}] Updated state - Final portfolio:\n{state['final_portfolio']}"
            )


class Simulation:
    def __init__(self, graph):
        self.graph = graph
        self.queues = {node: asyncio.Queue() for node in graph.nodes}
        self.worker_clock = asyncio.Event()  # Add worker clock event

    async def send_to(self, target, msg):
        await self.queues[target].put(msg)

    async def recv_from(self, target):
        return await self.queues[target].get()

    async def run_node(self, name, logic):
        state = self.graph.nodes[name]["state"]
        if name == "OrionWorker":
            # For worker, pass the clock event
            await logic(name, state, self.send_to, self.recv_from, self.worker_clock)
        else:
            await logic(name, state, self.send_to, self.recv_from)

    async def start(self):
        node_logic_map = {
            # "lp": lp_node,
            "curator": curator_node,
            "vault": vault_node,
            "worker": worker_node,
            "metavault": metavault_node,
        }
        tasks = []
        for node in self.graph.nodes:
            logic_fn = node_logic_map[self.graph.nodes[node]["type"]]
            tasks.append(asyncio.create_task(self.run_node(node, logic_fn)))
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    logger.info("Starting Orion Finance simulation")
    graph = build_graph()
    sim = Simulation(graph)
    try:
        asyncio.run(sim.start())
    except KeyboardInterrupt:
        logger.info("Simulation stopped by user.")
    except Exception as e:
        logger.error(f"Simulation stopped due to error: {str(e)}", exc_info=True)
    finally:
        logger.info("Simulation ended.")
