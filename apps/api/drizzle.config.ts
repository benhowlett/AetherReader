import type { Config } from 'drizzle-kit';

export default {
  schema: './src/db/schema.ts',
  out: './drizzle',
  dialect: 'libsql',
  dbCredentials: {
    url: 'file:sqlite.db',
  },
} satisfies Config;
