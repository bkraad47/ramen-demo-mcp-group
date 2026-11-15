---
name: iris_analysis
description: Answer a question about the Iris data set by calling iris_describe, iris_outliers and iris_group_means, in that order, and quoting only their numbers.
---
# Iris analysis

Question: {{question}}

1. Call `iris_describe` once. Note the row count and each column's mean and std.
2. Call `iris_outliers` for the column the question is about (or `sepal_width` if it names none) with `z` 2.5.
   Report `total` and the rows returned; if `truncated` is true, say so and raise `z` rather than asking for more.
3. Call `iris_group_means` with `by` `species` and compare the three species on the columns that matter.
4. Answer the question in a short paragraph. Every number you write must appear in a tool result; if a tool errors
   or a value is missing, say what is missing instead of estimating it.
