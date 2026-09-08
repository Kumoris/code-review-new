# XML 配置文件检视规则

> 触发条件：当变更文件包含 `.xml` 文件时加载

---

## 目录

- [XML 语法规则](#xml-语法规则)
- [错误码配置规则](#错误码配置规则)

---

## XML 语法规则

### XML-SYNTAX-001: XML 闭合标签必须匹配

- **检查锚点**: `.xml` 文件 diff 中新增或修改的闭合标签 `</Xxx>` 或自闭合标签 `/>`
- **触发条件**: diff 中出现以下任一情况：
  - 同一层级出现重复闭合标签（如两个 `</PARAS>`）
  - 闭合标签与开始标签不匹配（如 `<PARA>...</PARAM>`）
  - 删除了开始标签但保留了闭合标签（或反之）
- **严重程度**: fatal（XML 解析失败导致运行时错误）
- **反例**:
  - 新增行含 `</PARAS>` 但该层级已有 `</PARAS>` 闭合 → 重复闭合标签，XML 解析报错
  - 删除 `<PARA>` 开始标签但保留 `</PARA>` 闭合标签 → 标签不匹配
  - `<PARA>...</PARAM>` — 开始标签 `<PARA>` 与闭合标签 `</PARAM>` 不匹配
- **正例**:
  - 新增 `<PARA name="xxx" value="yyy"/>` 自闭合标签，不破坏结构
  - 新增成对的 `<PARA>...</PARA>`，闭合标签与开始标签一一对应

### XML-SYNTAX-002: XML 属性值必须使用引号包裹

- **检查锚点**: `.xml` 文件 diff 中的属性赋值
- **触发条件**: 属性值未用双引号或单引号包裹（如 `name=2689030159` 而非 `name="2689030159"`）
- **严重程度**: fatal（XML 解析必然失败）
- **反例**: `<PARA name=2689030159 value=Error/>` — 属性值无引号
- **正例**: `<PARA name="2689030159" value="Error"/>` — 属性值有引号

### XML-SYNTAX-003: XML 标签嵌套正确

- **检查锚点**: `.xml` 文件 diff 中新增或修改的嵌套标签结构
- **触发条件**: 子标签在父标签外部闭合，即标签交叉嵌套
- **严重程度**: fatal（XML 解析失败，well-formedness 检查不通过）
- **反例**:
  - `<A><B></A></B>` — B 在 A 外部闭合，交叉嵌套
  - `<PARAS><PARA>...</PARAS></PARA>` — PARA 未在 PARAS 内闭合
- **正例**:
  - `<A><B></B></A>` — B 在 A 内正确闭合
  - `<PARAS><PARA>...</PARA></PARAS>` — 嵌套顺序正确

---

## 错误码配置规则

### XML-ERRCODE-001: 中英文错误码必须同步新增

- **检查锚点**: `locale/en_US/` 和 `locale/zh_CN/` 下的错误码 XML 文件
- **触发条件**: diff 中 `en_US` 目录新增了错误码 `PARA` 但 `zh_CN` 目录的对应文件未同步新增相同 `name` 的条目（或反之）
- **严重程度**: major（用户看到空错误码或 fallback 到英文）
- **反例**:
  - `en_US/bms_resman_errorcode.xml` 新增 `<PARA name="2689030159" value="Failure: ..."/>`，但 `zh_CN/bms_resman_errorcode.xml` 未新增同名条目
  - 中英文 `name` 属性值不一致（如 en_US 用 `2689030159`，zh_CN 用 `2689030160`）
- **正例**:
  - en_US 和 zh_CN 都新增 `<PARA name="2689030159" .../>`，name 值一致

### XML-ERRCODE-002: 错误码格式一致性

- **检查锚点**: 同一 `name` 的中英文 `PARA` 条目
- **触发条件**: 英文 value 以 "Error:" 开头但中文 value 以 "失败:" 开头（或反之），前缀风格不一致
- **严重程度**: minor（用户体验不一致）
- **反例**:
  - en_US: `value="Failure: The profile has been bound."` → 前缀 "Failure:"
  - zh_CN: `value="错误: 当前模板已被绑定"` → 前缀 "错误:"
  - 上下文已有条目统一用 "Error:"/"错误："，但新增条目用了 "Failure:"/"失败:"
- **正例**:
  - en_US/zh_CN 的前缀风格与同文件已有条目保持一致
