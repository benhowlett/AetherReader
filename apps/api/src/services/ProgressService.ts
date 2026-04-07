import { drizzle } from 'drizzle-orm/libsql';
import { createClient } from '@libsql/client';
import { progress } from '../db/schema.js';
import { eq } from 'drizzle-orm';
import { ReadingProgress } from '@aetherreader/shared';

export class ProgressService {
  private db: any; // Use more specific type if possible

  constructor(dbPath: string) {
    const client = createClient({
      url: `file:${dbPath}`,
    });
    this.db = drizzle(client);
  }

  async saveProgress(item: ReadingProgress) {
    return this.db.insert(progress).values({
      bookPath: item.bookPath,
      position: item.position,
      lastReadAt: item.lastReadAt,
    })
    .onConflictDoUpdate({
      target: progress.bookPath,
      set: {
        position: item.position,
        lastReadAt: item.lastReadAt,
      },
    })
    .run();
  }

  async getProgress(bookPath: string): Promise<ReadingProgress | undefined> {
    const results = await this.db.select().from(progress).where(eq(progress.bookPath, bookPath)).all();
    if (results.length === 0) return undefined;
    const result = results[0];
    return {
      bookPath: result.bookPath,
      position: result.position,
      lastReadAt: result.lastReadAt,
    };
  }
}
