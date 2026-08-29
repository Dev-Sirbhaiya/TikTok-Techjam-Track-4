13. **Change-point / override detection** — recognise genuine pivots and invalidate outdated information instead of merely decaying it slowly.

14. **Structured shopping world model** — model how the internal shopping state is expected to change after different actions.

15. **Counterfactual action simulation** — before asking something, simulate “what happens if I ask use-case/material/style/etc.?”

16. **Shallow future planning** — initially look only 1–2 conversational steps into the future; no giant Dreamer-like neural model.

17. **Value-of-information questioning** — ask whatever question is expected to improve actual retrieval/ranking, not merely reduce entropy.

18. **Metric-aware planning** — value actions according to expected **HitRate@10 + MRR + speed/turn efficiency**, matching the competition.

19. **Retriever-disagreement questioning** — use disagreement between BM25/dense/structured retrieval as evidence about what clarification would be useful.

20. **Recommend while asking** — return the best current Top-10 every turn while simultaneously asking a useful clarification when appropriate.

21. **Portfolio/slate Top-10** — protect the highest ranks for high-confidence products while using some lower slots to hedge unresolved intent.

22. **Uncertainty-controlled diversity** — diversify more while uncertain; concentrate recommendations as confidence rises.

23. **Comparative preference learning** — understand signals like “more like #2,” “less flashy,” or choosing between representative products.

24. **Tinder-style preference probe for demo/product version** — show contrasting directions to cheaply discover latent preference; not load-bearing for the headless evaluator.

25. **Lightweight OLIVIA-style policy adaptation** — track which types of actions/questions are actually helping during the current conversation and slightly reweight them.

26. **Global prior + session adaptation** — start from a well-tested global strategy rather than trying to learn everything from ten turns.

27. **SkillOpt-style offline self-evolution** — run development conversations, inspect failures, modify strategy/configuration, and keep changes only when held-out score improves.

28. **Counterfactual/synthetic rollouts** — exploit the deterministic development environment/catalogue to create many possible state/action transitions from only 200 sessions.

29. **Uncertainty calibration** — make sure confidence values actually correspond reasonably to retrieval success before trusting the planner.

30. **Planning fallback** — when imagined futures are unreliable, automatically fall back to simpler one-step VOI rather than trusting bad simulations.

31. **Fully local scoring path** — embeddings, retrieval, state update and planning should work without relying on an external LLM/API.

32. **Strict ablations** — every fancy component must prove that it improves held-out TechnicalScore; otherwise we remove it.

The **central architecture** is therefore essentially:

$$
\boxed{
\text{Conversation}
\rightarrow
\text{Distilled Latent Belief State}
\rightarrow
\text{Multi-Hypothesis Retrieval}
\rightarrow
\text{Product Belief}
\rightarrow
\text{Imagine Actions}
\rightarrow
\text{Choose Best Action}
\rightarrow
\text{Top-10 + Clarification}
\rightarrow
\text{Update State}
}
$$

And importantly, **we are NOT currently planning to implement** a giant trained Dreamer-style world model, heavy RL, full MCTS, MIND/ComiRec retraining, or complicated LoRA/hypernetwork adaptation. Those only enter if simpler versions experimentally justify them.