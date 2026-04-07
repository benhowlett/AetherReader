import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const progress = sqliteTable('progress', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  bookPath: text('book_path').notNull().unique(),
  position: text('position').notNull(),
  lastReadAt: integer('last_read_at').notNull(),
});
