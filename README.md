# NexusAcquire

**Universal AI-Powered Intelligent Escrow Protocol on GenLayer**
 
Built natively for the GenLayer ecosystem.

---

### For live testing of all contract functions, please use the official GenLayer Studio with the deployed contract address: 0x7caEB9A2313e9e178c48F8731371a03E9c64abA1




## Overview

NexusAcquire is an intelligent escrow and asset acquisition protocol that enables trust-minimized buying and selling of real-world and digital assets.  

It leverages GenLayer’s unique capabilities — large language models and consensus on subjective outcomes — to automatically evaluate whether evidence provided by a seller satisfies the conditions defined by a buyer.

The protocol removes the need for traditional intermediaries, centralized escrow services, and human arbitrators in many types of transactions.

---

## Problem It Solves

Current asset transactions (especially those involving digital goods, code, documents, and real-world assets) suffer from:

- Lack of trust between buyers and sellers
- High fees and delays caused by intermediaries
- Risk of fraud and double-selling the same asset
- Difficulty verifying evidence in an unbiased and automated way
- Prolonged capital lock-up

NexusAcquire addresses these issues by combining on-chain escrow logic with GenLayer’s AI consensus mechanism.

---

## How It Works

1. **Asset Registration** (optional but recommended)  
   The seller registers a unique asset ID in the on-chain registry.

2. **Create Escrow**  
   The buyer locks funds and defines:
   - Asset type
   - Unique asset ID
   - Conditions that must be met
   - Timeout period

3. **Submit Evidence**  
   The seller submits evidence links and an agreement statement.

4. **Intelligent Evaluation**  
   The contract uses GenLayer’s `prompt_non_comparative` equivalence principle to reach consensus on whether the evidence satisfies the stated conditions.

5. **Settlement**  
   - If approved → status becomes `RELEASED` and ownership is transferred to the buyer in the registry.  
   - If rejected → status becomes `REFUNDED`.

6. **Timeout**  
   After the deadline, anyone can mark the escrow as `EXPIRED`.

---

## Key Features

- AI-powered evaluation using GenLayer consensus
- On-chain ownership registry (anti-fraud / anti double-selling)
- Configurable timeout and fee structure
- Timelock-protected ownership transfer of the protocol
- Pause functionality
- Clear status lifecycle: `FUNDED` → `SUBMITTED` → `RELEASED` / `REFUNDED` / `EXPIRED`
- Fully transparent and auditable on-chain history

---

## Supported Asset Types

- GitHub repositories & source code
- Real estate documents
- Vehicle titles
- Tokenized Real-World Assets (RWA)
- AI models and digital assets
- Freelance deliverables
- Any asset whose evidence can be provided via web links

---

## Target Users

- DAO treasuries
- RWA platforms
- Real estate and vehicle marketplaces
- Freelancers and clients
- Developers selling code or models
- Any party needing reliable automated escrow

---

## Current Status

This version is fully deployable and tested on **GenLayer Studio**.

Native token (ERC-20) support and automatic value transfers have been simplified for Studio compatibility. Full production-ready value transfer logic will be enabled on the live network.

---

## Future Roadmap

- Full ERC-20 and multi-token support
- Automatic value transfers on finality
- Multi-modal evidence evaluation (images, PDFs, etc.)
- Simple frontend for non-technical users
- Reputation and identity integrations
- Dedicated marketplace built on top of the protocol
- Cross-chain expansion

---

## Security Highlights

- Owner cannot access or seize user funds
- On-chain registry prevents double-selling
- Timelock for critical admin actions
- Strict input validation
- Pause mechanism for emergencies

---

## License

MIT

---

**Built for the GenLayer ecosystem**  
NexusAcquire aims to become a standard intelligent escrow layer for trust-minimized asset acquisition.