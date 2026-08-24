# frontend-visual-baseline Specification

## Purpose

Define a stable “政通惠” visual identity for the rebuilt frontend across public, authenticated, protected, and failure states without changing accepted route, session, API, permission, or data behavior.

## ADDED Requirements

### Requirement: Reference-derived product identity

The frontend SHALL present “政通惠” and “一站式政策服务平台” as its primary product identity and SHALL use a coherent white/pale blue-gray canvas, neutral text, restrained blue-purple emphasis, Chinese system typography, and compact top navigation derived from the authorized public visual reference. The implementation MUST be independently authored in this repository and MUST NOT copy legacy JavaScript, CSS, component source, routes, payloads, state, or business behavior.

#### Scenario: Visitor recognizes the rebuilt product

- **WHEN** a visitor opens any current public or protected route
- **THEN** the visible shell uses the “政通惠” identity and shared reference-derived visual system rather than the previous generic dark sidebar workbench

#### Scenario: Visual reference is implemented within the new architecture

- **WHEN** UI1.0 assets and styles are inspected
- **THEN** they contain only repository-authored React/CSS plus documented authorized static photographs and do not contain copied legacy application source or unavailable legacy behavior

### Requirement: Public entrance and real authentication continuity

The signed-out home SHALL provide locally served photographic personal and enterprise entrances that target the existing `/personal` and `/enterprise` routes. The login page SHALL retain the configured Supabase form, busy/disabled/error behavior, and successful redirect. Visual entrances MUST NOT create a local identity, bypass a route guard, mount protected content, or display fabricated policy, question-answer, or workspace results.

#### Scenario: Signed-out visitor chooses a service entrance

- **WHEN** a signed-out visitor activates the personal or enterprise entrance
- **THEN** the existing protected route and authentication guard handle the request and no protected workspace content is mounted before authorization

#### Scenario: Login service is unavailable

- **WHEN** required public authentication configuration is missing or sign-in fails
- **THEN** the restyled login view preserves the explicit unavailable/error state and does not create a fake session or Mock success

#### Scenario: Local entrance assets are rendered

- **WHEN** the signed-out home is loaded without access to the legacy site
- **THEN** both repository-local entrance images decode successfully with positive dimensions and the page does not depend on a runtime hotlink

### Requirement: Protected workspace visual continuity without permission change

The authenticated header, home, and role workspace views SHALL use the same visual baseline while continuing to derive role navigation from the database identity and continuing to mount role content only after backend workspace authorization. Government and administrator entries MUST remain reachable when returned by `/me`, even though the signed-out visual entrance emphasizes personal and enterprise services.

#### Scenario: Provisioned user enters an assigned role

- **WHEN** `/me` returns an active identity and the matching workspace endpoint authorizes the requested role
- **THEN** the header and page show only the existing real identity/scope and authorized role entries using the shared visual baseline

#### Scenario: Backend denies the requested role

- **WHEN** the workspace endpoint returns HTTP 403
- **THEN** the frontend shows the existing explicit access-denied state in the shared visual system and does not mount protected role content

### Requirement: Consistent explicit system states

Loading, signed-out, missing-configuration, authentication failure, identity failure, authorization checking, authorization failure, access denied, disabled-feature, health, and not-found views SHALL use the same typography, spacing, surface, action, and focus rules. Restyling MUST NOT merge distinct states, hide retry actions, or silently substitute a Mock result.

#### Scenario: A guarded dependency fails

- **WHEN** an existing auth, identity, permission, feature, or health dependency reports an error
- **THEN** its stable explicit message and retry action where currently provided remain visible and operable within the new presentation

### Requirement: Responsive and accessible essential controls

The frontend SHALL support desktop and mobile layouts down to `320px`, including the acceptance viewport `390x844`, without horizontal page overflow, incoherent overlap, clipped essential text, or layout shifts caused by dynamic identity/role content. Navigation, login, retry, role entrances, identity, and sign-out MUST remain visible and keyboard operable. Focus MUST be visibly indicated, media dimensions MUST be stable, and non-essential motion MUST respect `prefers-reduced-motion`.

#### Scenario: Authenticated user uses a mobile viewport

- **WHEN** an authenticated page is rendered at `390x844`
- **THEN** the product header, authorized navigation, current identity, and sign-out control remain reachable and no essential element is hidden behind another element or outside the horizontal viewport

#### Scenario: Dynamic content is longer than expected

- **WHEN** an identity, organization, route label, error, or control contains its longest supported text
- **THEN** it wraps or truncates deliberately within stable layout constraints and does not overlap adjacent content or resize fixed-format controls incoherently
