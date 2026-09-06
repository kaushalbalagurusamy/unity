# Unity: Universal Semantic Intermediate Representation for Codebase Intelligence

[![Target Venue: NeurIPS / ICLR](https://img.shields.io/badge/Target-NeurIPS%20%2F%20ICLR%202025%2F2026-blue.svg)](./RESEARCH_PROPOSAL.md)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-green.svg)](./LICENSE)
[![Status: Research Inquiry](https://img.shields.io/badge/Status-Formal%20Proposal%20Stage-orange.svg)](./RESEARCH_PROPOSAL.md)

> **Project Unity** investigates a universal, invariant-preserving intermediate representation designed specifically for transformer attention mechanisms. By deterministically lowering heterogeneous source code into a canonical 3-Layer Semantic Intermediate Representation (Unity-IR), Unity eliminates syntactic noise, mitigates cross-lingual performance disparities (e.g., Python vs. Rust/C++/Go), and replaces slow, brittle Graph RAG pipelines with self-contained, high-density semantic contexts.

---

## 📄 Full Research Proposal

The formal research proposal for scientific inquiry targeting the **AI/ML Track of NeurIPS / ICLR** is available in:
👉 **[RESEARCH_PROPOSAL.md](./RESEARCH_PROPOSAL.md)**

---

## 🎯 The Core Thesis

Current LLMs used in software engineering face a critical trilemma:
1. **Reasoning Horizon Attenuation:** Long-context attention mechanisms experience severe recall degradation ("lost-in-the-middle") over multi-file causal chains.
2. **Graph RAG Maintenance & Latency Tax:** Graph RAG and Code Property Graphs (CPGs) introduce multi-second retrieval latency, high maintenance costs, and brittle multi-hop queries.
3. **Cross-Lingual Disparity:** Massive pre-training data imbalances result in steep drops in accuracy when evaluating models on systems languages (Rust, C++, Go) or legacy stacks (COBOL) compared to Python.

**Unity's Solution:** A deterministic lowering compiler that translates source code across diverse languages into **Unity-IR**, composed of:
* **Layer 1 (Contract & Systems Semantics):** Concurrency isolation, memory ownership/lifetimes, and side-effect purity derived via static analysis.
* **Layer 2 (Algorithmic Core):** First-order mathematical logic, set transformations, and state-transition invariants.
* **Layer 3 (Causal Intent):** Disambiguated Controlled Natural Language (CNL) and explicit cross-file symbol hyperlinks.

---

## 🔬 Scientific Inquiry & Benchmarking

Project Unity evaluates its hypotheses across three rigorous benchmark tiers:
* **Tier 1 (Real-World Issues):** SWE-bench Multilingual (300 tasks across 9 languages) & SWE-bench Java.
* **Tier 2 (Multi-File Dependencies):** CrossCodeEval & RepoEval.
* **Tier 3 (Execution Simulation & Invariants):** CRUXEval-X & Custom Concurrency Invariant Suite.

Read the complete problem formulation, architectural specifications, empirical baselines, and scholarly citations in **[RESEARCH_PROPOSAL.md](./RESEARCH_PROPOSAL.md)**.
