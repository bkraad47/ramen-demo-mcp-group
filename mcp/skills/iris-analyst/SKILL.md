---
name: iris-analyst
description: Explore the Iris data set with the demo group's iris_describe, iris_outliers and iris_group_means tools and report what they return, nothing more.
---
# Iris analyst

Use this when someone asks about the Iris flower measurements served by this group (resource `ramen://demo/iris.csv`).

1. Start with `iris_describe` for the row count and per-column mean, std, min and max.
2. For "unusual" or "extreme" values call `iris_outliers` with the column and `z` 2.5; lower `z` only if it returns no
   rows, and never below 1.5. The result is capped; if `truncated` is true, say so instead of asking for every row.
3. For differences between species call `iris_group_means` with `by` `species`. Hosts that render MCP Apps show its
   bar chart; otherwise describe the three groups from the JSON.
4. Quote numbers exactly as the tools return them. Do not compute, round further or fill in a value a tool did not give.

Answer in a few sentences, naming the tool each number came from.
