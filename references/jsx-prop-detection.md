# JSX Prop 泄漏检测规则

> 规则ID: JSTS-PROP-001
> 触发条件：当变更文件包含 React/JSX 组件时自动激活
> 优先级：高（此为code-review skill强制检测项）

---

## 规则描述

当 JSX 组件新增 prop 时，必须检查是否遗漏了原有 prop 的绑定。这是最常见的 React 组件重构错误之一。

## 检测逻辑

1. 识别 JSX 组件的新增/修改 prop 传递（如 `<Component newProp={value} />`）
2. 检查该组件是否通过 `{...props}` 或 `props.xxx` 方式传递给子组件
3. 如果父组件新增了 prop 但子组件未同步接收，标记为问题
4. 特别关注从 `props` 解构时遗漏的属性

## 常见误判场景

- 组件内部使用的 prop（不需要传递给子组件）→ 不报告
- 类型定义中已有但实现中遗漏 → 报告
- HOC/wrapper 组件有意过滤 prop → 不报告

## 示例

### 问题代码

```jsx
// 父组件新增了 onClick prop
<Button onClick={handleClick} label="Submit" />

// 但子组件解构时遗漏了 onClick
function Button({ label, className }) {
  // onClick 被遗漏了！
  return <button className={className}>{label}</button>;
}
```

### 正确代码

```jsx
function Button({ label, className, onClick }) {
  return <button className={className} onClick={onClick}>{label}</button>;
}
```

## 严重级别

- 遗漏事件处理prop（onClick, onChange, onSubmit等）→ `major`
- 遗漏样式/数据prop → `minor`
- 遗漏可选prop且无业务影响 → `suggestion`
