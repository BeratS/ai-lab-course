# What the Numbers Say

| Label | Pass rate | Faithful | Avg. seconds |
| --- | --- | --- | --- |
| baseline | 92% | 92% | 5.1 |
| topk3 | 100% | 100% | 4.9 |
| strict-grader | 92% | 92% | 4.9 |
| no-retry | 83% | 83% | 4.5 |

## 1. Every failure is a “faithful” failure

`correct` is 100% in all four runs, so the answers always contained the right facts.

What failed is that the answer added something the sources don't support.

Remember the Tirana answer:

> “I'd suggest contacting Studio Lumi directly.”

That's helpful, but it's not in the documents.

It may also be the multi-hop answer:

> “11–13 days in total”

This is a calculation, and a strict judge might say the sum isn't explicitly written in the sources.

## 2. The differences are mostly noise

On 12 questions, one case represents approximately 8 percentage points.

Going from 92% to 100% with `topk3` is a single question.

Run baseline again, and you might get 100% too. You can't conclude that `topk3` is better from one run.

## 3. Retrieval isn't your bottleneck

`sources` is 100% everywhere, even with `TOP_K = 3`, because you only have 6 chunks.

The dataset is too easy to demonstrate retrieval problems.

## 4. No-retry is the only hint of a real effect

There are 2 more failures, but it saves approximately 0.6 seconds per question (around 12%).

That's worth checking with repeated runs.

## Honest conclusion

Your eval set is saturated.

Everything scores around 90–100%, so it can't reliably distinguish between the different versions.

This is a very common real-world finding, and recognizing it is a senior-level skill.