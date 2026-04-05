# UI Experience Contract

## Purpose

Define the non-code interface rules that the reconstructed frontend must uphold across routes.

## 1. Tone Contract

- The experience must feel professional, growth-oriented, and credible.
- Quiz-like interactions may be energetic, but they must not feel childish or detached from career outcomes.
- Visual richness must support comprehension, not decoration alone.

## 1A. Art Direction Contract

- The product should read as a career atlas, not a generic SaaS dashboard.
- The interface should favor strong typography, whitespace, rhythm, and composition before adding chrome.
- The system should use no more than two type families and one primary accent color unless a stronger system is intentionally introduced.
- Decorative gradients, floating stat cards, and ornamental icon clutter must not become the default visual language.

## 2. Navigation Contract

- Authenticated users always have access to a stable primary navigation shell.
- The current section must be obvious at a glance.
- No primary navigation item may point to a missing, placeholder-only, or broken route.

## 2A. Product Surface Contract

- Logged-in screens must prioritize utility copy, status, hierarchy, and action over marketing language.
- Dense information is acceptable if spacing, typography, and grouping preserve fast scanning.
- Cards should only be used when the card itself is the interaction, such as a choice state or a journey node.

## 3. Roadmap Contract

- On larger screens, the roadmap is presented as a journey or atlas with visible hierarchy.
- On smaller screens, the same content collapses into a readable sequential structure.
- Users can always identify current progress, next actionable step, and completed work.
- The roadmap must be the signature visual object of the authenticated product experience.

## 4. Assessment Contract

- The assessment experience must show clear progression from introduction to questions to submission to results.
- Each question state must be obvious before the user advances.
- Processing and completed states must be visually distinct.
- Result screens must direct the user toward roadmap or jobs next actions.
- Assessment interactions may borrow from premium quiz patterns, but the tone must remain professional and outcome-focused.

## 5. Shared State Contract

- Loading, empty, processing, success, and error states must be intentionally designed rather than left as raw placeholders.
- Notification counts and saved-job state must remain understandable from any relevant surface.
- When backend data is missing or delayed, the UI must still communicate the user’s next safe action.

## 5A. Public Surface Contract

- The landing page and public auth surfaces must carry strong brand presence in the first viewport.
- The landing hero should be full-bleed or near full-bleed, with one dominant visual idea and no hero-card clutter.
- Public copy should stay short, brand-led, and easy to scan in seconds.

## 5B. Motion Contract

- The redesign must ship with at least one entrance sequence, one scroll-linked or sticky reveal pattern, and one consistent hover/layout transition family.
- Motion must improve hierarchy, atmosphere, or affordance rather than exist as decoration.
- Mobile performance and readability take precedence over animation ambition.

## 6. Template Inspiration Contract

- roadmap.sh informs learning-path density, hierarchy, and progression cues.
- Genially’s Work Style Quiz informs professional visual-choice interactions and profile-style result framing.
- The final UI must be original to Sha8alny and not a brand clone of either source.
