# Synthetic customer list
Local stdlib-only fixture. No real customer data or external integration.

## 本轮已确认需求：离线列表状态筛选

目标用户为内部操作员，本轮只修复 `filters.py` 的 `filter_records(records, status=None)`。完整客户运营系统暂不扩展；不新增 UI、数据库、外部服务或依赖。使用合成字典列表，不接入真实客户数据。

| 规则 | 已确认行为 | 验证 |
|---|---|---|
| F-01 无筛选 | `status` 为 `None` 或空字符串时返回全部记录，顺序不变，返回新的列表对象；默认参数同样适用。 | `test_no_filter_returns_new_list_in_original_order` |
| F-02 精确匹配 | 字符串 `open` / `closed` 严格区分大小写，按原顺序返回 `status` 完全相等的记录；缺少字段不匹配。 | `test_filters_exact_status_in_original_order`、`test_missing_null_and_different_case_status_do_not_match` |
| F-03 非法状态 | 其余 `status` 值均抛出 `ValueError`，包括 `Open`、未知字符串和非字符串值。 | `test_invalid_status_raises_even_for_empty_input` |
| F-04 空输入 | 空列表仍执行相同的状态校验；合法状态返回新的空列表，非法状态抛出 `ValueError`。 | `test_empty_list_with_valid_status_returns_new_empty_list`、F-03 的检查 |
| F-05 不变性 | 不修改输入列表或记录。记录内容和原列表内对象身份保持不变。 | `test_input_list_and_records_are_unchanged` |

需求来源：本轮用户明确确认的规则。上述基线替代第一轮未确认的完整系统设想，无需对该范围重复确认。

## 验证计划与命令

用 Python 标准库 `unittest` 先在原函数上运行上述行为用例，保留实际失败；然后只修复该函数并运行同一套测试。检查最终修改范围，确保 `fixture.json` 不变。

```bash
python3 -B -m unittest -v
```

本轮属于非敏感本地筛选修复，按 R1 的窄范围处理。当前目录不是 Git 仓库；本轮不额外初始化治理设施、创建远程 PR、合并或发布。本地验证完成与后续独立审查、发布是不同阶段。
