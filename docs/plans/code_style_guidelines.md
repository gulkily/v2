# Code Style Guidelines

## 1. Separate Content From Code
- Human-authored content must not be embedded directly inside source code when it can live in a separate file.
- Text content, HTML templates, LLM prompts, email bodies, fixture payloads, and other large string resources should live in a dedicated template or content directory.
- Code should load these files by path and supply only the minimal runtime variables needed for rendering.
- Inline strings in code are acceptable only for very short constants, identifiers, error codes, or tightly local messages.

## 2. Prefer Simple, Portable Dependencies
- Reference implementations should minimize third-party module use.
- Favor standard-library solutions when they remain readable.
- Do not introduce framework-heavy abstractions into the core parsing, canonicalization, or CGI contract layers.

## 3. Keep Parsing And Rendering Deterministic
- Any code that affects canonical payloads, hashing, signing, ordering, or API responses must be explicit and deterministic.
- Avoid locale-sensitive formatting, implicit timezone behavior, or unordered map output in canonical paths.
- Make normalization rules visible in code rather than relying on library defaults.

## 4. Keep Canonical Logic Separate From Convenience Logic
- Canonical parsing, validation, hashing, and signing rules should live in narrowly scoped modules.
- UI helpers, derived indexes, cache builders, and debug conveniences should not alter canonical behavior.
- If a convenience layer disagrees with canonical logic, canonical logic wins.

## 5. Prefer Small Files With Clear Boundaries
- Each module should have a single clear purpose.
- Parsing, storage, signing, CGI dispatch, and rendering should remain separable.
- Avoid large mixed-purpose files that combine protocol handling, HTML generation, and git operations.

## 6. Use Explicit Names
- Prefer names that describe the domain role of a function or file.
- Use terms like `canonicalize_post`, `load_thread`, `write_record`, or `render_index` instead of vague helpers such as `process_data`.
- Keep repository paths and generated file names predictable.

## 7. Design For Cross-Implementation Parity
- When behavior must match across Perl and Python, choose the simplest rule that can be implemented the same way in both.
- Document edge cases near the code that implements them.
- Add fixtures for any behavior where byte-identical success output matters.

## 8. Keep Templates Mostly Logic-Light
- Templates should focus on presentation and interpolation, not business rules.
- Canonical record interpretation, policy decisions, and permission logic belong in code, not in templates.
- If template branching becomes substantial, move the decision into code and pass a simpler render context.

## 9. Prefer ASCII In Canonical Paths
- Canonical repository content, API fixtures, and protocol examples should remain ASCII-only unless a later spec revision explicitly changes that rule.
- If non-ASCII is ever introduced in non-canonical surfaces, isolate the conversion boundary clearly.

## 10. Write Comments Sparingly But Precisely
- Add comments where canonical behavior, normalization, or portability constraints are easy to misread.
- Do not add comments that only restate the code literally.

## 11. Keep Emitted HTML Source Readable
- HTML responses should preserve meaningful line breaks around major document and component boundaries so browser page-source views stay readable.
- Prefer shared render helpers and multiline templates over long concatenated one-line HTML strings when the response is meant for humans to inspect.
- If a route must build HTML in code, keep the structure explicit enough that future tests can assert durable formatting boundaries without snapshotting entire pages.
