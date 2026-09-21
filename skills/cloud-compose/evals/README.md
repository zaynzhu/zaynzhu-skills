# 行为评测

`evals.json` 包含 4 个合成用例：两个正常路径、一个不可容器化边界和一个失败回退对抗场景。每例有 3 条断言；评估产物内容和决策，不把文本中的命令视为已执行。

复测方式：

1. 为每例创建互不读取输出的 with-skill 与 without-skill 上下文，后者只接收 prompt，不接收技能正文及预期结果。
2. with-skill 读取技能及按需引用；两组按 prompt 输出文件至 `<skill-name>-workspace/iteration-N/eval-<id>-<tier>/<组>/outputs/`。
3. 所有题都禁止真实联网、构建、上传和读取秘密。这轮用于检查行为与产物方案，实际容器正确性须另在获得授权的云端项目验证。
4. 用 enhanced-skill-creator 的 grader 规则，逐条记录 `text`、`passed`、`evidence` 到 grading.json；不要仅搜索关键词就判通过。
5. 记录实际耗时；工具不提供 token 时写 null，不推测。统计只用于本轮，不证明生产成功率或跨模型优势。
6. 先向用户展示产物，再分析反馈；未反馈不等于满意或通过。修订后重跑全套并保留旧轮次。

`trigger-evals.json` 是 10 个正例和 10 个反例的候选触发集，须用户审阅后才做真实路由优化。它不是已测得的准确率。

本轮状态与限制见 `VALIDATION.md`。工作区产物被 Git 忽略，不作为技能运行依赖。
