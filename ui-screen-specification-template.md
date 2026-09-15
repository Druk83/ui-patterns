# {{screen.title}}

Status: {{screen.status}}  
Screen ID: `{{screen.screen_id}}`  
Route: `{{screen.route}}`  
Template set: `ui-patterns`

Template set version: `{{package.template_set_version}}`
Screen pool: `{{screen.screen_pool_ref.pool_id}}` version `{{screen.screen_pool_ref.version}}`

Pattern: `{{pattern.pattern_id}}` version `{{pattern.version}}`
Interface type: `{{screen.interface_type}}`
Applied templates: `{{screen.applied_templates}}`
Screen UI template: `{{screen.template_id}}` revision `{{screen.template_revision}}`
Principle profiles: `{{screen.principle_profiles}}`
Information architecture profile: `{{screen.information_architecture_profiles}}`

## Назначение и контекст

{{screen.purpose}}

## Контекст использования

| Parameter | Value | Status |
|---|---|---|
| Environment | {{screen.usage_context.environment}} | {{screen.usage_context.environment_status}} |
| Device and viewport | {{screen.usage_context.device_and_viewport}} | {{screen.usage_context.device_status}} |
| Usage frequency | {{screen.usage_context.usage_frequency}} | {{screen.usage_context.frequency_status}} |
| Task criticality | {{screen.usage_context.task_criticality}} | {{screen.usage_context.criticality_status}} |
| User preparation | {{screen.usage_context.user_preparation}} | {{screen.usage_context.user_preparation_status}} |

## Модальность интерфейса и технические ограничения

- Input channels: {{screen.interface_modality.input_channels}}
- Output channels: {{screen.interface_modality.output_channels}}
- Primary modality: {{screen.interface_modality.primary_modality}}
- Fallback modality: {{screen.interface_modality.fallback_modality}}
- Data volume class: {{screen.data_scale_and_performance.data_volume_class}}
- Loading strategy: {{screen.data_scale_and_performance.loading_strategy}}
- Update frequency: {{screen.data_scale_and_performance.update_frequency}}
- Response expectation: {{screen.data_scale_and_performance.response_expectation}}
- Long operation behavior: {{screen.data_scale_and_performance.long_operation_behavior}}
- Data integrations: {{screen.integration_and_component_constraints.data_integrations}}
- External services: {{screen.integration_and_component_constraints.external_services}}
- Component system: {{screen.integration_and_component_constraints.component_system}}
- Design tokens: {{screen.integration_and_component_constraints.design_tokens}}
- Compatibility constraints: {{screen.integration_and_component_constraints.compatibility_constraints}}

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

## Information architecture decisions

| Decision | Scope | Decision and rationale | Affected UI refs | Verification method | Status |
|---|---|---|---|---|---|
| `{{ia_decision.ia_decision_id}}` / `{{ia_decision.ia_principle_id}}` | {{ia_decision.scope}} | {{ia_decision.decision}} {{ia_decision.rationale}} | {{ia_decision.affected_ui_refs}} | {{ia_decision.verification_method}} | {{ia_decision.status}} |

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

## UX principle decisions

Для каждого применимого профиля фиксируется не название закона, а его результат для реализации:

- Principle: `{{principle.principle_id}}`
- Applicability: `{{principle.applicability}}`
- Decision: {{principle.decision}}
- Implementation rule: {{principle.implementation_rule}}
- Affected UI refs: {{principle.affected_ui_refs}}
- Verification method: {{principle.verification_method}}
- Status: {{principle.status}}

## Risk and non-happy paths

- Behavioral influence: {{risk_and_ethics.behavioral_influence}}
- User benefit: {{risk_and_ethics.user_benefit}}
- Foreseeable harm: {{risk_and_ethics.foreseeable_harm}}
- Safeguards and opt-out: {{risk_and_ethics.safeguards}}
- Non-happy-path coverage: {{risk_and_ethics.non_happy_path_coverage}}

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
- [ ] Тип интерфейса, среда использования, частота и критичность задачи описаны или отмечены как `GAP`.
- [ ] Каналы ввода/вывода, fallback и технические ограничения описаны или отмечены как `GAP`.
- [ ] Объём данных, стратегия загрузки, интеграции и компонентная основа описаны, если они влияют на решение.
- [ ] Все действия имеют условия доступности, успех, ошибку и переход.
- [ ] Все применимые состояния описаны.
- [ ] Проверены роли, viewport, orientation и responsive-поведение.
- [ ] Проверены accessibility, validation, recovery и overflow.
- [ ] Применимые UX-принципы переведены в правила реализации и проверки.
- [ ] Информационная архитектура, точки входа, маркировка и способы поиска описаны или явно отмечены как `GAP`.
- [ ] Сквозные шаблоны применены или явно отклонены с причиной.
- [ ] Проверены неидеальные сценарии и риск воздействия на пользователя.
- [ ] Reference artifact согласован и связан с экраном.
- [ ] Все GAP имеют владельца и условие закрытия.
