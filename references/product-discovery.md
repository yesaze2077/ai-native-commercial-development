# Product Discovery and Commercial Intent

## Mode and applicable inputs

Use for a new product, an unclear problem, a material change in customer or commercial model, or evidence contradicting the accepted direction. Start from the authoritative request, existing [PRODUCT](../assets/project-template/docs/product/PRODUCT.md), accepted specification, customer evidence and resource constraints. For an increment, examine only assumptions affected by that increment; do not reopen settled decisions without material evidence.

Planning, diagnosis and review produce findings or proposed decisions; they do not authorize implementation, customer contact, external experiments or purchases. Reuse accepted requirements and their evidence instead of repeating discovery. This guide adds no approval ceremony or mandatory research team; existing authorization and risk rules govern dependent work.

## Working method

1. **Describe one consequential problem.** Name the user, triggering situation, job to finish, current behavior or workaround, and observable cost of failure. Separate the beneficiary from the buyer or budget owner. Replace “users need AI” with a concrete task and consequence. State what a successful outcome lets that person do.
2. **Separate evidence from assumptions.** For each material claim, record the source/date, relevant population, observation, interpretation and remaining uncertainty. Distinguish observed behavior, reported preference, internal opinion and a proposed hypothesis. A competitor feature or enthusiastic interview is a signal, not proof of demand. Treat unavailable joins and unmeasured behavior as unknown.
3. **Compare the real alternatives.** Include the current workaround and doing nothing, alongside a small number of plausible solutions. Compare time to value, switching effort, trust, cost and the outcome the user values. Explain why the proposed slice is preferable under current constraints; preserve the rejected alternatives and the condition that would make one preferable.
4. **Make value and viability explicit.** Describe how the product creates or protects value, who pays or allocates resources, likely pricing or internal value logic, delivery/support costs and major acquisition or adoption dependencies. Label modeled economics as assumptions. For an internal tool, use time, error, service or capacity value without inventing revenue.
5. **Test the most dangerous assumption first.** Choose the assumption whose failure would invalidate the direction: problem frequency, willingness to switch/pay, ability to deliver the outcome, lawful/authorized data access, or sustainable delivery cost. Use the cheapest discriminating test within scope: existing records, a task walkthrough, a concept/prototype comparison, manual fulfillment or a bounded technical probe. Specify what observation would contradict the hypothesis. A proxy measures only its stated proxy; clicks do not establish retention or willingness to pay.
6. **Set the decision before seeing results.** Record the test owner, population, time/cost cap, observation window, measure, minimum evidence and continue/change/stop thresholds. Choose thresholds from business constraints rather than a universal sample size. If research cannot resolve a critical uncertainty safely or affordably, return the unresolved dependency and a smaller alternative. Do not fill gaps with fabricated research.

A compact decision row is enough: `assumption → evidence/gap → cheapest test → threshold/window → owner → result → decision`. Reuse existing evidence when its population and conditions still fit. Run new research only where it can change a decision.

## Outputs and exit basis

Update the existing product brief, issue or specification with the problem, users/buyer, evidence and assumptions, alternatives, value/commercial logic, chosen slice, non-goals, success measures and unresolved risks. Preserve authoritative IDs and lineage under [operating-model.md](operating-model.md); a separate research report is optional.

Continue when the slice has a defensible user outcome, explicit assumptions, testable acceptance and a verification plan proportionate to risk. Change direction when evidence invalidates the proposed mechanism but supports the underlying problem. Stop or defer when the problem lacks sufficient consequence, feasibility/value fails its threshold, or a necessary dependency remains unavailable. Record who owns the next decision and its evidence requirement. “Discovery complete” means the next authorized decision is supported, not that product-market fit is proven.
