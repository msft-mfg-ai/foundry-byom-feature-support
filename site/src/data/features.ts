import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export interface Feature {
  slug: string;
  name: string;
  summary: string;
  description: string;
  pm: string;
  /** supported | not_supported | partial | not_confirmed */
  support_status: 'supported' | 'not_supported' | 'partial' | 'not_confirmed';
  /** ga | preview | in_progress | not_confirmed */
  implementation_status: 'ga' | 'preview' | 'in_progress' | 'not_confirmed';
  test_file: string;
  azure_docs?: string;
  notes?: string;
  test_source: string;
}

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const featuresDir = path.resolve(__dirname, '../../../features');

export function loadFeatures(): Feature[] {
  const slugs = fs
    .readdirSync(featuresDir, { withFileTypes: true })
    .filter((d) => d.isDirectory() && !d.name.startsWith('_'))
    .map((d) => d.name)
    .sort();

  return slugs.map((slug) => {
    const dir = path.join(featuresDir, slug);
    const meta = JSON.parse(fs.readFileSync(path.join(dir, 'feature.json'), 'utf8')) as Omit<Feature, 'test_source'>;
    const testPath = path.join(dir, meta.test_file);
    const test_source = fs.readFileSync(testPath, 'utf8');
    return { ...meta, test_source };
  });
}
