# Design: Correct Authenticated Q&A Horizontal Centering

`qa-home` is already a full-width flex container. Its workspace workbench remains a flex child with normal zero horizontal margins and fills that parent. The workbench’s existing inner heading/form/result width constraints use automatic inline margins, yielding a common horizontal center. The public-entry negative margin rule is not changed because this patch concerns only the authenticated workspace nesting.

There is no behavioral, API, data or permission decision. Rollback is CSS-only.
