# {{screen.title}}

Status: {{screen.status}}  
Screen ID: `{{screen.screen_id}}`  
Route: `{{screen.route}}`  
Pattern: `{{pattern.pattern_id}}` version `{{pattern.version}}`

## Назначение и контекст

{{screen.purpose}}

## Роли и доступ

| Role | Visibility | Allowed actions | Denied actions |
|---|---|---|---|
| {{role.name}} | {{role.visibility}} | {{role.allowed_actions}} | {{role.denied_actions}} |

## Viewport и orientation

- Viewport: {{screen.viewport}}
- Orientation: {{screen.orientation}}
- Responsive profile: {{screen.responsive_profile}}
- Overflow rule: {{screen.overflow_rule}}

## Reference artifacts

| Artifact | Type | Status | Viewport | Role | State | Version |
|---|---|---|---|---|---|---|
| {{reference.artifact_id}} | {{reference.type}} | {{reference.status}} | {{reference.viewport}} | {{reference.role}} | {{reference.state}} | {{reference.version}} |

## UI-блоки

### {{block.title}}

- UI ID: `{{block.ui_id}}`
- Purpose: {{block.purpose}}
- Data source: {{block.data_source}}
- Displayed fields: {{block.displayed_fields}}
- Controls: {{block.controls}}
- Required pattern roles: {{block.pattern_roles}}

#### Actions

| Action | Trigger | Availability | Input | Success | Error | Next transition |
|---|---|---|---|---|---|---|
| {{action.action_id}} | {{action.trigger}} | {{action.availability}} | {{action.input}} | {{action.success}} | {{action.error}} | {{action.transition}} |

#### States

| State | Entry conditions | Visible changes | Available actions | Exit transitions |
|---|---|---|---|---|
| {{state.state_id}} | {{state.entry_conditions}} | {{state.visible_changes}} | {{state.available_actions}} | {{state.exit_transitions}} |

#### Validation and errors

- Validation rules: {{block.validation.rules}}
- Error placement: {{block.validation.error_placement}}
- Focus after error: {{block.validation.focus_after_error}}
- Cancel and recovery: {{block.validation.recovery}}

#### Accessibility

- Keyboard order: {{block.accessibility.keyboard_order}}
- Focus management: {{block.accessibility.focus_management}}
- Screen reader output: {{block.accessibility.screen_reader}}
- Contrast and scaling: {{block.accessibility.contrast_and_scaling}}

#### Responsive behavior

- Narrow viewport: {{block.responsive.narrow_viewport}}
- Orientation change: {{block.responsive.orientation_change}}
- Overflow and scrolling: {{block.responsive.overflow}}
- Touch target rules: {{block.responsive.touch_targets}}

## Transitions

| Source | Event | Condition | Target | Data preservation |
|---|---|---|---|---|
| {{transition.source}} | {{transition.event}} | {{transition.condition}} | {{transition.target}} | {{transition.data_preservation}} |

## Traceability

- Requirements: {{traceability.requirement_refs}}
- Scenarios: {{traceability.scenario_refs}}
- Pattern adaptations: {{traceability.pattern_refs}}
- Acceptance criteria: {{traceability.acceptance_refs}}
- Open GAP: {{traceability.gap_refs}}

## Критерии приёмки

- [ ] Все существенные блоки и данные описаны.
- [ ] Все действия имеют условия доступности, успех, ошибку и переход.
- [ ] Все применимые состояния описаны.
- [ ] Проверены роли, viewport, orientation и responsive-поведение.
- [ ] Проверены accessibility, validation, recovery и overflow.
- [ ] Reference artifact согласован и связан с экраном.
- [ ] Все GAP имеют владельца и условие закрытия.
