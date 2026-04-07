# GEMINI.md

AetherReader is a mobile-first web application for reading ebooks stored in Nextcloud.

## Core Rules
- **Type-Safety**: Use TypeScript for all components (frontend and backend).
- **Mobile-First**: Prioritize responsive CSS and touch-friendly UI.
- **Sync**: Automatically save and restore reading progress (CFI for EPUB, Page for PDF).
- **Authentication**: Use Nextcloud WebDAV credentials for library access.

## Architecture
- **Monorepo**: Managed via npm workspaces.
- **apps/web**: React/Vite/TS/Vanilla CSS.
- **apps/api**: Express/TS/SQLite/Drizzle.
- **packages/shared**: Shared types and interfaces.

## Verification
- Unit tests for WebDAV and Progress logic.
- Manual verification of mobile responsiveness.
