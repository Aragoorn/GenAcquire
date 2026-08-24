# GensAcquire – Universal AI-Powered Intelligent Escrow Protocol

**Contract Address (Studio):** `0xd96dD4E6491d022334D3B7D301029d40b4795157`
## live demo : https://dapper-cascaron-8b0c9b.netlify.app/

https://explorer-studio.genlayer.com/address/0xd96dD4E6491d022334D3B7D301029d40b4795157

## Overview

NexusAcquire is an intelligent escrow protocol built on GenLayer that enables trustless buying and selling of digital and real-world assets (GitHub repositories, documents, RWA, freelance deliverables, etc.).

The key innovation is that **validators judge the actual deliverable**, not just the seller’s written description.

### How it works

1. Buyer locks funds and defines clear conditions.
2. Seller submits evidence URLs (GitHub links, documents, etc.).
3. The contract itself fetches the real content from those URLs using `gl.nondet.web.get`.
4. An LLM under the Equivalence Principle evaluates whether the fetched content satisfies the buyer’s conditions.
5. Funds are automatically released or refunded **on-chain** via `emit_transfer`.

## Key Features Addressing Steward Feedback

- **Real web fetching**: The contract reads the actual content of evidence URLs (README, LICENSE, documents, etc.).
- **Strict seller check**: Only the registered seller can call `submit()`.
- **On-chain settlement**: Successful evaluation immediately transfers funds using `emit_transfer`.
- Anti-fraud ownership registry to prevent double-selling.

## Main Functions

| Function       | Description                                      | Who can call      |
|----------------|--------------------------------------------------|-------------------|
| `register`     | Register ownership of an asset                   | Anyone            |
| `create`       | Create a new escrow (payable)                    | Buyer             |
| `submit`       | Submit evidence URLs                             | Only registered Seller |
| `evaluate`     | Fetch real content + AI judgment + settle funds  | Anyone            |
| `timeout`      | Refund buyer if time expires                     | Anyone            |
| `get` / `info` | View escrow and protocol status                  | Anyone            |

## Tested Flow

- Seller: `0xA1C6808b8f08D091e2826C9640Be302a310655E1`
- Buyer: `0xaa5Eaa814bD58e5079Db20FB0826D2727c926b9E`

Full happy-path and negative tests (seller-only submit, real content evaluation) have been executed successfully on Studio.

## Why this matters

Traditional escrows only check text descriptions.  
NexusAcquire forces the validators to look at the **real deliverable**, making the system significantly harder to game and truly leveraging GenLayer’s unique capabilities.
