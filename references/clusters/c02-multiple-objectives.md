# Cluster 02: Decisions with Multiple Objectives

Source: Ralph L. Keeney and Howard Raiffa, *Decisions with Multiple Objectives: Preferences and Value Tradeoffs* (Keeney and Raiffa, *Decisions with Multiple Objectives*). All mechanics below are distilled exclusively from the "Decisions with Multiple Objectives" slice of the working corpus. No terminology is introduced beyond what the authors use; any name added for implementation purposes is explicitly flagged as an **operationalization**.

## 1. Purpose and Scope

The book addresses decision problems where a single alternative must be evaluated against several conflicting objectives, under certainty and under uncertainty. Its irreducible mechanics fall into two strata:

1. **Structuring** the problem: objectives, attributes, consequence space, dominance, and value functions (certainty case).
2. **Scaling** preferences: preferential independence, utility independence, additive and multiplicative multiattribute forms, scaling constants, and risk attitude (uncertainty case).

Throughout, an **alternative** \(a\) belongs to the feasible set \(A\); to each \(a\) is associated a **consequence**, a point in an \(n\)-dimensional attribute space, via \(n\) evaluators \(X_1, \ldots, X_n\).

## 2. Objectives, Attributes, and the Hierarchy

### 2.1 Definitions

- **Objective**: a statement of a direction in which the decision maker wishes to strive; it generally has no fixed endpoint (achievement can always, in principle, be improved further).
- **Goal**: a specific level of achievement that is either attained or not (e.g., "deliver at least 90% of parcels within two days"). The book deliberately minimizes use of "goal" and confines its formal language to objectives and attributes.
- **Attribute**: the scale used to measure the degree to which an objective is met. An attribute may be a **scalar attribute** (single number) or a **vector attribute** (a tuple of scalar attributes, e.g., three pollutant emission rates jointly measuring "reduce emissions").
- Objectives are typically organized in an **objectives hierarchy**: a broad, vague overall objective (e.g., "improve the well-being of residents") is decomposed into successively more detailed lower-level objectives, down to a level where a workable attribute can be attached.

### 2.2 Desirable Properties of an Attribute Set

An attribute is useful to a decision maker only if it is:

- **Comprehensive**: knowing the attribute's level gives the decision maker a clear understanding of the extent to which the associated objective is achieved (a matter of theoretical/informational adequacy).
- **Measurable**: it is reasonable to (a) obtain a probability distribution over its possible levels for each alternative, and (b) assess preferences over those levels (via a utility function or, in some cases, a rank ordering) (a matter of practical feasibility).

The objectives hierarchy as a whole should be reasonably **complete**, without being burdened by trivial considerations that add nothing to the decision. There is no universally correct hierarchy; different formalizations of the same underlying concerns can highlight different tradeoffs.

### 2.3 Handling Objectives Without a Natural Attribute

Three explicit techniques are given when no natural attribute exists for an objective:

1. **Subjective index**: construct a subjective scale (e.g., an ordered scale for "prestige") when no objectively measured scale exists.
2. **Proxy attribute**: substitute an attribute that is not itself the objective but is believed to correlate with it (e.g., response time and transport time as proxies for patient condition on arrival). Proxy attributes are not unique, come in degrees of closeness to the true objective, and their overuse is cautioned against because they push implicit modeling into the decision maker's head, degrading the fidelity of elicited preferences.
3. **Direct preference measurement**: bypass attribute construction altogether and have the decision maker directly assign (conditional, expected) utility values to the objective's achievement for each alternative.

### 2.4 Dominance and the Efficient Frontier

**Dominance.** For two consequences \(x'\) and \(x''\), \(x'\) *dominates* \(x''\) whenever

\[
x_i' \ge x_i'' \quad \text{for all } i, \qquad \text{and} \qquad x_i' > x_i'' \quad \text{for some } i.
\]

If \(x'\) dominates \(x''\), the alternative yielding \(x''\) is a noncontender for "best." Dominance uses only the ordinal character of the attribute numbers (that \(x_i' > x_i''\)), never their cardinal spacing, and it requires no comparison between attributes \(X_i\) and \(X_j\).

**Efficient frontier.** Let \(R\) be the range-set of consequences achievable by feasible alternatives. The set of consequences in \(R\) that are not dominated is the **efficient frontier** of \(R\), also called the **Pareto optimal set**. Points on the efficient frontier cannot be ruled out by dominance alone; selecting among them requires a preference structure (value function or utility function).

**Extended dominance** (operationalization label follows the book's own term "extended dominance"): probabilistic mixtures ("restrictive profiles") of dominated and dominating alternatives can sometimes be shown to dominate a candidate alternative even when no single alternative does; this is used to prune alternatives before formal preference structuring.

## 3. Value Functions Under Certainty (Chapter 3 Mechanics)

### 3.1 The Value Function

A **value function** \(v\) is a scalar-valued function on the consequence space such that

\[
(x_1, \ldots, x_n) \succeq (x_1', \ldots, x_n') \iff v(x_1, \ldots, x_n) \ge v(x_1', \ldots, x_n'),
\]

where \(\succeq\) reads "preferred or indifferent to." The value function is purely **ordinal**: it represents preference order under certainty and carries no probabilistic content. The decision maker's problem reduces to choosing \(a \in A\) so that \(v\) is maximized.

### 3.2 Marginal Rate of Substitution and Constant Substitution Rate

For two attributes \(X\) and \(Y\), the **marginal rate of substitution** at \((x, y)\), denoted \(\Delta(y)\), is the amount of \(X\) the decision maker would trade for a small increment in \(Y\). If \(\Delta\) depends on \(y\) but not on \(x\), then

\[
v(x, y) = x + v_Y(y)
\]

for some single-attribute value function \(v_Y\) (Theorem 3.1 mechanics). This is the base case for constructing an additive value structure by first checking whether trade-off rates are stable across the level of the attribute being "paid with."

### 3.3 Preferential Independence

**Definition.** Partition the attribute set into \(Y\) (a subset) and its complement \(Z\). The set \(Y\) is **preferentially independent** of \(Z\) if and only if the conditional preference order over \(y\)-profiles, given a fixed level \(z'\) of the complementary attributes, does not depend on which \(z'\) was fixed. Formally, for some (and hence, by the definition, for all) \(z'\):

\[
(y', z') \succeq (y'', z') \iff (y', z) \succeq (y'', z) \quad \text{for all } z.
\]

If \(Y\) is preferentially independent of \(Z\), one may write \(y' \succeq y''\) unambiguously (dropping reference to \(z\)) and structure a value function \(v_Y\) over \(Y\) alone, without repeating the exercise for every level of \(Z\).

Preferential independence of \(Y\) from \(Z\) does **not** imply the converse (that \(Z\) is preferentially independent of \(Y\)).

**Pairwise preferential independence**: every pair of attributes is preferentially independent of its complement (the remaining attribute, in the three-attribute case).

**Mutual preferential independence**: every subset of the attributes is preferentially independent of its complementary subset.

### 3.4 The Additive Value Function

**Theorem (three-attribute additive form).** A value function may be written

\[
v(x, y, z) = v_X(x) + v_Y(y) + v_Z(z)
\]

if and only if \(\{X, Y\}\) is preferentially independent of \(Z\), \(\{X, Z\}\) is preferentially independent of \(Y\), and \(\{Y, Z\}\) is preferentially independent of \(X\): that is, if and only if the attributes are pairwise preferentially independent. Additivity **coimplies** pairwise preferential independence: each side is necessary and sufficient for the other.

**General \(n\)-attribute form.** Given attributes \(X_1, \ldots, X_n\), \(n \ge 3\), an additive value function

\[
v(x_1, \ldots, x_n) = \sum_{i=1}^{n} \lambda_i v_i(x_i)
\]

exists if and only if the attributes are **mutually preferentially independent**. For \(n \ge 3\), pairwise preferential independence is equivalent to mutual preferential independence, so the pairwise checks (which grow combinatorially) can, under stated theorems, be reduced to a smaller set of checks anchored on chains of preferential independence relations among subsets.

Here each \(v_i\) is normalized \(v_i(\text{worst } x_i) = 0\), \(v_i(\text{best } x_i) = 1\), the \(\lambda_i\) satisfy \(0 < \lambda_i < 1\) and \(\sum_i \lambda_i = 1\), and \(\lambda_i\) is called the **scaling constant** (weight) for attribute \(i\). The \(\lambda\) function defined on subsets of the attribute index set behaves exactly like a probability measure: \(\lambda(\varnothing) = 0\), \(\lambda(I) = 1\), and \(\lambda(S \cup T) = \lambda(S) + \lambda(T)\) for disjoint \(S, T\).

## 4. Unidimensional Utility Under Uncertainty (Chapter 4 Mechanics)

### 4.1 Expected Utility and the Certainty Equivalent

For a lottery \(L\) yielding consequences \(x_1, \ldots, x_n\) with probabilities \(p_1, \ldots, p_n\), the expected consequence is \(\bar{x} = \sum_i p_i x_i\) and the expected utility is \(E[u(\tilde{x})] = \sum_i p_i u(x_i)\).

**Certainty equivalent.** A certainty equivalent \(\hat{x}\) of lottery \(L\) is the sure amount such that the decision maker is indifferent between \(L\) and receiving \(\hat{x}\) for certain:

\[
u(\hat{x}) = E[u(\tilde{x})].
\]

The certainty equivalent is unique whenever \(u\) is monotonic.

### 4.2 Risk Attitude

**Risk aversion (definition).** A decision maker is risk averse if the expected consequence of any nondegenerate lottery is preferred to the lottery itself:

\[
u[E(\tilde{x})] > E[u(\tilde{x})] \quad \text{for all nondegenerate lotteries}.
\]

**Theorem.** A decision maker is risk averse if and only if \(u\) is concave. Risk proneness corresponds to convex \(u\); risk neutrality corresponds to linear \(u\).

**Corollary (operational test).** A decision maker who prefers the expected consequence of any 50-50 lottery to the lottery itself is risk averse.

**Risk premium.** For a lottery with expected consequence \(\bar{x}\) and certainty equivalent \(\hat{x}\), the risk premium is \(\bar{x} - \hat{x}\) (for increasing, risk-averse \(u\); sign conventions adjust for risk proneness or decreasing preference).

**Constant, decreasing, and increasing risk aversion.** Let \(r(x) = -u''(x)/u'(x)\) be the (local) risk aversion function.

- **Constant risk aversion**: \(r(x) = c > 0\) for all \(x\); the risk premium for a fixed-shape lottery does not depend on the current wealth/position level. This corresponds to the exponential utility form \(u(x) = -e^{-cx}\).
- **Decreasing risk aversion**: the decision maker is risk averse and the risk premium for any fixed lottery decreases as the reference wealth level increases.
- **Increasing risk aversion**: the risk premium increases as the reference level increases.
- **Risk neutral**: \(r(x) = 0\); **constantly risk prone**: \(r(x)\) is a negative constant.

### 4.3 Elicitation Protocol for Unidimensional Utility (the Book's Assessment Procedure)

The book's own "procedure for assessing utility functions" runs in explicit, orderable steps:

1. **Familiarization / range bounding.** Bound the attribute's relevant range with \(x^0\) (worst plausible value) and \(x^*\) (best plausible value), chosen for meaningfulness to the decision maker, not for mathematical convenience. Values far outside a psychologically real range degrade elicited responses.
2. **Comprehension check.** Ask the decision maker to compare two clearly ordered consequences \(S\) and \(T\) to confirm the encoding of "more is preferred" (or the reverse) is understood before any real assessment begins.
3. **Qualitative characterization.** Determine monotonicity of \(u\) (ask if higher attribute levels are always preferred). Determine risk attitude by offering a symmetric lottery \((x+h, x-h)\) against its certain expected value \(x\), repeated across the range and across different \(h\); consistent preference for the certain amount signals risk aversion, consistent preference for the lottery signals risk proneness, indifference signals risk neutrality. Repeating this test at different reference levels \(x\) (holding \(h\) fixed) qualitatively distinguishes constant, decreasing, and increasing risk aversion by whether the risk premium shrinks, stays level, or grows.
4. **Quantitative fractile assessment (five-point method).** Normalize \(u(x_0) = 0\), \(u(x_1) = 1\). Find the certainty equivalent \(x_{.5}\) of the 50-50 lottery \((x_1, x_0)\), giving \(u(x_{.5}) = .5\). Recurse: find \(x_{.75}\), the certainty equivalent of \((x_1, x_{.5})\), giving \(u(x_{.75}) = .75\); find \(x_{.25}\), the certainty equivalent of \((x_{.5}, x_0)\), giving \(u(x_{.25}) = .25\). This fixes five points \((x_0, x_{.25}, x_{.5}, x_{.75}, x_1)\) on the utility curve.
5. **Consistency check.** Assess the certainty equivalent \(\hat{x}\) of the lottery \((x_{.75}, x_{.25})\); for consistency it must equal \(x_{.5}\), since \(u(\hat x) = \tfrac12 u(x_{.75}) + \tfrac12 u(x_{.25}) = .5\). A qualitative risk-attitude re-check follows from whether the fractile certainty equivalents fall below (risk averse) or above (risk prone) the arithmetic midpoints of their lottery ranges.
6. **Curve fitting / family selection.** Fair a smooth curve through the assessed points, or select a parametric family (e.g., exponential for constant risk aversion) consistent with the qualitative findings, then fit its parameter(s) to the quantitative points.
7. **Iterate on inconsistency.** When responses conflict (no utility function fits all assessments), point out the discrepancy to the decision maker and repeat the relevant sub-steps until a coherent set of responses is reached, or fall back to bounding/sensitivity analysis if full reconciliation is infeasible.

## 5. Multiattribute Utility Under Uncertainty (Chapters 5–6 Mechanics)

### 5.1 Utility Independence

**Definition.** Partition the attributes into \(Y\) and complementary \(Z\). \(Y\) is **utility independent** of \(Z\) if conditional preferences for lotteries over \(Y\), given a fixed level \(z\) of the complementary attributes, do not depend on which level of \(z\) was fixed. Equivalently, for any fixed \(z'\),

\[
u(y, z) = g(z) + h(z)\, u(y, z'), \qquad h(z) > 0,
\]

i.e., all conditional utility functions over \(Y\) (across different fixed \(z\)) are **positive linear transformations** of one another (strategically equivalent).

Utility independence is a **specialization of preferential independence** into the cardinal (uncertainty-respecting) setting: preferential independence concerns ordinal preference order only; utility independence additionally requires that risk attitude over \(Y\), given \(z\), not shift with \(z\).

**Mutual utility independence**: every subset of the attributes is utility independent of its complement.

### 5.2 Two-Attribute Forms

If \(Y\) and \(Z\) are mutually utility independent, the two-attribute utility function is **multilinear**:

\[
u(y,z) = k_Y u_Y(y) + k_Z u_Z(z) + k_{YZ}\, u_Y(y)\, u_Z(z),
\]

with \(u_Y, u_Z\) normalized to \([0,1]\), \(k_Y = u(y^*, z^0)\), \(k_Z = u(y^0, z^*)\), and \(k_{YZ} = 1 - k_Y - k_Z\).

- If \(k_Y + k_Z = 1\) (equivalently \(k_{YZ} = 0\)), the form reduces to the **additive** utility function: \(u(y,z) = k_Y u_Y(y) + k_Z u_Z(z)\).
- If \(k_Y + k_Z \ne 1\) (\(k_{YZ} \ne 0\)), the multilinear form is strategically equivalent to a **multiplicative** representation.

**Discriminating test (indifference-reversal test, the book's own corollary, operationalized here as the "flip test").** This test presupposes that \(Y\) and \(Z\) are already established to be mutually utility independent (Section 5.1); its conclusion about \(k_{YZ}\) and the additive/multiplicative form is conditional on that structure and is not meaningful otherwise, since the multilinear representation from which \(k_{YZ}\) is defined only exists under mutual utility independence in the first place. Given mutual utility independence holds: fix all attributes other than \(Y\) and \(Z\) at a convenient level. Choose \(y_1, y_1'\) (a preferred pair on \(Y\)) and \(z_1, z_1'\) (a preferred pair on \(Z\)). If the decision maker is **indifferent** between a 50-50 lottery over \(\{(y_1, z_1'), (y_1', z_1)\}\) and a 50-50 lottery over \(\{(y_1, z_1), (y_1', z_1')\}\), that is, indifferent to which pairing of levels is bundled together, then \(k_{YZ} = 0\) and the additive form applies. If the decision maker instead has a strict preference between the two pairings (equivalently: reversing which "high" outcome is paired with which "high" outcome changes desirability), the multiplicative form applies. This indifference/reversal test is exactly the mechanism the book supplies for confirming (or rejecting) additive separability against the interactive multiplicative alternative, given mutual utility independence, and it also underlies the sign check on \(k_{YZ}\): preferring \(L_1 = \{(y_2,z_2),(y_1,z_1)\}\) over \(L_2 = \{(y_2,z_1),(y_1,z_2)\}\) implies \(k_{YZ} > 0\); the reverse preference implies \(k_{YZ} < 0\); indifference implies \(k_{YZ} = 0\).

### 5.3 General \(n\)-Attribute Multiplicative and Additive Forms

**Theorem (the central multiattribute result).** If \(X_1, \ldots, X_n\) are mutually utility independent, then

\[
1 + k\, u(x) = \prod_{i=1}^{n} \bigl(1 + k\, k_i\, u_i(x_i)\bigr),
\]

where \(u\) and each \(u_i\) are normalized to \([0,1]\) (worst level maps to \(0\), best level maps to \(1\)), \(k_i\) is the scaling constant for attribute \(i\), and the overall scaling constant \(k\) solves

\[
1 + k = \prod_{i=1}^{n} (1 + k k_i).
\]

- If \(\sum_{i=1}^{n} k_i = 1\), then \(k = 0\) and the form collapses to the **additive** utility function:

\[
u(x) = \sum_{i=1}^{n} k_i\, u_i(x_i).
\]

- If \(\sum_{i=1}^{n} k_i \ne 1\), then \(k \ne 0\) is found by solving the fixed-point equation above (numerically, since it is generally not closed-form for \(n > 2\)):
  - If \(\sum_i k_i > 1\), the consistent solution satisfies \(-1 < k < 0\).
  - If \(\sum_i k_i < 1\), the consistent solution satisfies \(k > 0\).

**Discriminating test (generalized flip test for \(n\) attributes).** This test is likewise conditional: it presupposes that \(X_1, \ldots, X_n\) are mutually utility independent (Section 5.3, Theorem 6.1 hypothesis), so that the multiplicative representation and its associated \(k_i, k\) are already known to exist; the test then distinguishes the additive special case (\(k=0\)) from the genuinely multiplicative case (\(k \ne 0\)) within that structure, and does not by itself establish mutual utility independence. Given that structure: pick any two attributes \(X_1, X_2\); fix all others at a convenient level \(x_{12}\); pick \(x_1, x_1'\) and \(x_2, x_2'\). If the decision maker is indifferent between the 50-50 lottery over \(\{(x_1, x_2', x_{12}), (x_1', x_2, x_{12})\}\) and the 50-50 lottery over \(\{(x_1, x_2, x_{12}), (x_1', x_2', x_{12})\}\), the utility function must be additive; a strict preference implies it must be multiplicative. If the indifference (or preference) holds for one choice of \(x_{12}\), it holds for all such choices whenever \(\{X_1, X_2\}\) is utility independent, so the test need only be run once.

### 5.4 The Scaling Constants Are Not "Importance Weights"

The scaling constants \(k_i\) (or \(\lambda_i\) in the value-function case) depend on the chosen worst/best endpoints (\(x_i^0, x_i^*\)) of each attribute's range. Narrowing the range of an attribute while holding all preferences over the interior fixed will shrink that attribute's scaling constant, even though the decision maker's underlying regard for the attribute is unchanged. Consequently: **a larger \(k_i\) does not mean attribute \(i\) is "more important."** Two decision makers, or the same decision maker under two different range specifications, can produce very different \(k_i\) values without any change in genuine preference structure. This is a **range-dependency constraint**: scaling constants are only interpretable jointly with the attribute ranges they were assessed against, and any elicitation protocol must record and hold those ranges fixed.

## 6. Elicitation by Indifference: The Book's Assessment Machinery

The book supplies two closely related indifference-based elicitation styles: one for the certainty (value function, Chapter 3) case, one for the uncertainty (utility function, Chapters 5–6) case. Both share the same skeleton.

### 6.1 Consequence Table (Operationalization)

The book's own device is the **performance profile**: for each alternative, list the attained level on every attribute (e.g., a 4-attribute profile \((x_1, x_2, x_3, x_4)\)). A tabulation of these profiles across all alternatives under consideration is here labeled, as an **operationalization**, a "consequence table": this exact phrase is not the book's, but the underlying object (a matrix of alternatives by attribute levels) is exactly what the book's performance profiles amount to when compiled together.

### 6.2 Ranking Before Scaling

Before assigning numeric weights, the book has the decision maker **rank** the scaling constants qualitatively, using paired binary comparisons of "corner" consequences (all attributes at their worst level except one or a subset, which is set to its best level). For example: comparing the consequence with only attribute 1 at its best level against the consequence with only attribute 2 at its best level reveals whether \(\lambda_1 \gtrless \lambda_2\) (or \(k_1 \gtrless k_2\)). This ranking step introduces the decision maker to the tradeoff structure gradually before demanding precise numbers, and it bounds the plausible numeric answers obtained later.

### 6.3 Range and Swing Awareness (Operationalization of Section 5.9's Concern)

Before eliciting any numeric scaling constant, the protocol must fix and record each attribute's effective range \([x_i^0, x_i^*]\) (worst to best level actually under consideration in the problem). Because scaling constants are range-dependent (Section 5.4 above), a swing from worst to best on attribute \(i\) is only comparable to a swing from worst to best on attribute \(j\) if both ranges have been made explicit and are the ones actually spanned by the feasible alternatives. This range-recording step is not optional bookkeeping; it is a precondition for the corner-consequence comparisons in Section 6.2 to mean anything.

### 6.4 Midvalue Splitting (Certainty Case)

To assess a single-attribute component value function \(v_i\) over range \([w_i, b_i]\) (worst to best): normalize \(v_i(w_i) = 0\), \(v_i(b_i) = 1\). Find the subjective **midvalue point** \(m_{.5}\) such that the decision maker is indifferent between moving from \(w_i\) to \(m_{.5}\) (compensated by a change in the other attributes from some baseline \((b,c,d)\) to \((b',c',d')\)) and moving from \(m_{.5}\) to \(b_i\) (compensated by the same change in the other attributes). This gives \(v_i(m_{.5}) = .5\). Recursing on the sub-intervals \([w_i, m_{.5}]\) and \([m_{.5}, b_i]\) yields further points (\.25, \.75, etc.), which are then faired into a curve. This is the certainty-case analogue of the fractile method used for utility functions (Section 4.3, step 4).

### 6.5 Pairwise Trade-off Questions (Question II, the Book's Own Label)

**Question II** (verbatim structure from the book): select a level \(x_i^\dagger\) of attribute \(i\) and a level \(x_j^\dagger\) of attribute \(j\) such that, holding all other attributes fixed, the decision maker is indifferent between a consequence yielding \(x_i^\dagger\) alone at that level (others at their scale's zero point) and a consequence yielding \(x_j^\dagger\) alone at that level. This indifference yields the direct linear equation

\[
k_i\, u_i(x_i^\dagger) = k_j\, u_j(x_j^\dagger).
\]

Once the component utility (or value) functions \(u_i, u_j\) are separately known, this becomes one linear equation relating \(k_i\) and \(k_j\). This is the book's core pairwise trade-off elicitation device, used identically for value-function weights \(\lambda_i\) (Chapter 3) and utility-function scaling constants \(k_i\) (Chapter 6).

### 6.6 Probability-Equivalent Questions (Question I, the Book's Own Label)

**Question I**: for what probability \(p\) is the decision maker indifferent between (a) a lottery giving probability \(p\) at the best overall consequence \(x^*\) and probability \(1-p\) at the worst overall consequence \(x^0\), and (b) a specific consequence with attribute \(i\) at its best level and every other attribute at its worst level? The indifference probability directly gives \(k_i = p\), since the expected utility of the lottery is \(p\) and the utility of the "single-attribute-at-best" consequence is \(k_i\) by the normalization convention. This is a **certainty-equivalent-style scaling procedure conducted via probability**, structurally the multiattribute analogue of the unidimensional fractile method in Section 4.3.

### 6.7 Certainty-Equivalent and Probability-Equivalent Questions (General Lotteries)

Beyond the corner-consequence Question I, the book uses more general certainty-equivalent and probability-equivalent questions for interior points and for consistency checks.

### 6.8 Consistency Loop

When elicited responses are inconsistent (no set of scaling constants and component functions can satisfy all indifference statements simultaneously), the book requires the decision maker to confront the conflict. The protocol is to surface the specific pair of responses that disagree, re-elicit one or both, and iterate until consistency is achieved or the decision maker explicitly chooses to bound the conflict via sensitivity analysis. Averaging inconsistent responses without the decision maker's knowledge is forbidden.

### 6.9 Additional Consistency Checks (Chapter 5's Explicit List)

1. **Paired-comparison check**: ask whether \((y_1, z_1)\) is preferred to \((y_2, z_2)\); the assessed utility function must agree with the stated ordinal preference (\(u(y_1,z_1) > u(y_2,z_2)\) if and only if \((y_1,z_1)\) was preferred).
2. **Indifference-curve inspection**: generate the family of indifference curves implied by the fitted function and ask the decision maker whether they look reasonable.
3. **Ray risk-aversion check**: for form-specific structures, test risk attitude along a ray (e.g., \((y, cy)\) for fixed \(c\)) and confirm the sign/concavity implications match the fitted function's derivatives.
4. **Sign check on interaction term**: the \(L_1\) vs. \(L_2\) reversal test in Section 5.2 above, used specifically to pin down the sign of \(k_{YZ}\) (or, in general form, to confirm additive vs. multiplicative structure).

## 7. Python-Computable Schemas

(The schemas in this section are operationalizations of the book's assessment machinery for implementation. See the original corpus for the full set of dataclasses and algorithms for dominance, independence flags, additive/multiplicative forms, flip test, fractile elicitation, Question I/II solvers, and consistency audit.)

## 8. Validation Constraints

1. **Normalization constraint.** Every component value/utility function must satisfy \(v_i(\text{worst}) = 0\) and \(v_i(\text{best}) = 1\) (or the mirror for decreasing preference) before any scaling constant is computed.
2. **Weight-sum constraint (additive form).** \(\sum_i \lambda_i = 1\) (value function) or \(\sum_i k_i = 1\) (utility function, additive case) is required; violation signals either an arithmetic error or that the additive form is inappropriate and the multiplicative form (with \(k \ne 0\)) must be used instead.
3. **Multiplicative fixed-point existence.** The scaling constant \(k\) solving \(1 + k = \prod_i (1 + k k_i)\) must satisfy \(k > -1\) and the sign rule relative to \(\sum_i k_i\).
4. **Independence must be tested, not assumed.** No additive or multiplicative form may be adopted without an explicit, recorded verification (via the flip test or an equivalent indifference test).
5. **Range must be fixed before weight elicitation.** Because scaling constants are range-dependent, no numeric \(k_i\) or \(\lambda_i\) may be recorded without an attached, explicit \([x_i^0, x_i^*]\) range.
6. **Dominance precedes preference elicitation.** Any alternative dominated by another feasible alternative should be flagged and, ordinarily, removed before investing elicitation effort in value or utility assessment.
7. **Overdetermination is required, not optional.** The number of elicited indifference/trade-off equations should exceed the number of free parameters so that the consistency audit has something to check.
8. **Monotonicity must be checked before risk-attitude questions.**

## 9. Anti-Patterns

- Treating \(k_i\) as an importance weight in isolation.
- Assuming additive separability without testing it.
- Verifying independence pairwise only for large \(n\) without using the weaker chaining theorems.
- Eliciting utility questions before bounding the attribute range.
- Averaging away inconsistent responses instead of surfacing them.
- Confusing a proxy attribute with the true objective.
- Skipping dominance screening.
- Fitting a parametric utility family before establishing qualitative risk attitude.

## 10. Compact Worked Elicitation Example

Two attributes: \(Y\) = annual salary (range \(y^0 = 40\), \(y^* = 100\), in thousands), \(Z\) = commute minutes (range \(z^0 = 60\) worst, \(z^* = 10\) best, decreasing preference).

1. **Range fixing.** Record \([y^0, y^*] = [40, 100]\), \([z^0, z^*] = [10, 60]\).
2. **Component utility assessment (fractile method).** For \(Y\) and independently for \(Z\).
3. **Utility independence check.** Confirm mutual utility independence.
4. **Flip test.** Decision maker is indifferent → additive form.
5. **Scaling constant via Question I.** \(k_Y = 0.65\), \(k_Z = 0.35\).
6. **Assembled model.** \(u(y, z) = 0.65\, u_Y(y) + 0.35\, u_Z(z)\).
7. **Consistency check (Question II cross-validation).**

## 11. Consistency Audit (Compiled)

Every row of the audit table must independently evaluate to "Consistent" before the additive model is accepted for use in ranking alternatives.
