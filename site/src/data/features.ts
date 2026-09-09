import fs from 'node:fs';
import path from 'node:path';

export type Category =
  | 'agents'
  | 'endpoints'
  | 'routing'
  | 'tools'
  | 'quality'
  | 'ui'
  | 'infrastructure';

export interface Feature {
  slug: string;
  /** Visual grouping on the matrix page. */
  category: Category;
  name: string;
  summary: string;
  description: string;
  pm: string;
  /** supported | not_supported | partial | not_confirmed */
  support_status: 'supported' | 'not_supported' | 'partial' | 'not_confirmed';
  /** ga | preview | in_progress | not_confirmed | tbd */
  implementation_status: 'ga' | 'preview' | 'in_progress' | 'not_confirmed' | 'tbd';
  /** Optional. Status-only features (e.g. infra prerequisites) omit this. */
  test_file?: string;
  azure_docs?: string;
  /** Optional direct link to a specific sample (notebook / SDK example), NOT a repo home page. */
  sample_url?: string;
  notes?: string;
  /** null when the feature has no test_file (status-only card). */
  test_source: string | null;
  /** Public-URL paths (relative to base) to screenshots/<slug>/*.png, sorted by filename. Empty if none. */
  screenshots: string[];
}

export const CATEGORY_ORDER: Category[] = ['agents', 'endpoints', 'routing', 'tools', 'quality', 'ui', 'infrastructure'];

export const CATEGORY_LABEL: Record<Category, string> = {
  agents: 'Agents',
  endpoints: 'Direct API endpoints',
  routing: 'Routing & providers',
  tools: 'Agent tools',
  quality: 'Quality & safety',
  ui: 'Foundry UI',
  infrastructure: 'Infrastructure & publishing',
};

export const CATEGORY_DESCRIPTION: Record<Category, string> = {
  agents: 'Features where the BYOM `{connection}/{deployment}` prefix is passed directly as the model parameter.',
  endpoints: 'Raw OpenAI-compatible (and adjacent) endpoints exposed by the Foundry account. Some accept the BYOM prefix; many are platform-native and do not.',
  routing: 'Different connection shapes and upstream providers the gateway can front: APIM vs ModelGateway, OpenAI vs Anthropic vs catalog, static vs dynamic model discovery.',
  tools: 'Tools that run inside a Prompt Agent. The tool itself has no model parameter — BYOM applies to the host agent\'s orchestrator model.',
  quality: 'Evaluations and red-teaming pipelines. Some of these take their own judge/target model parameters.',
  ui: 'Foundry portal experience for BYOM \u2014 connection creation surfaces, playground/model-picker visibility, dynamic deployment listing.',
  infrastructure: 'Infrastructure prerequisites, publishing surfaces, and rollup status cards.',
};

const featuresDir = path.resolve(process.cwd(), '../features');
// Astro only serves static files from site/public at build/dev time, but the source-of-truth
// screenshots live next to each feature (features/<slug>/screenshots/*.png). Mirror them into
// public/screenshots/<slug>/ so <img> tags can reference a stable, base-aware URL.
const screenshotsPublicDir = path.resolve(process.cwd(), 'public/screenshots');

function copyFeatureScreenshots(slug: string, dir: string): string[] {
  const srcDir = path.join(dir, 'screenshots');
  if (!fs.existsSync(srcDir)) return [];
  const files = fs
    .readdirSync(srcDir, { withFileTypes: true })
    .filter((f) => f.isFile() && /\.(png|jpe?g|webp|gif)$/i.test(f.name))
    .map((f) => f.name)
    .sort();
  if (files.length === 0) return [];
  const destDir = path.join(screenshotsPublicDir, slug);
  fs.mkdirSync(destDir, { recursive: true });
  for (const file of files) {
    fs.copyFileSync(path.join(srcDir, file), path.join(destDir, file));
  }
  return files.map((file) => `screenshots/${slug}/${file}`);
}

export function loadFeatures(): Feature[] {
  const slugs = fs
    .readdirSync(featuresDir, { withFileTypes: true })
    .filter((d) => d.isDirectory() && !d.name.startsWith('_'))
    .map((d) => d.name)
    .sort();

  return slugs.map((slug) => {
    const dir = path.join(featuresDir, slug);
    const meta = JSON.parse(fs.readFileSync(path.join(dir, 'feature.json'), 'utf8')) as Omit<Feature, 'test_source' | 'screenshots'>;
    let test_source: string | null = null;
    if (meta.test_file) {
      test_source = fs.readFileSync(path.join(dir, meta.test_file), 'utf8');
    }
    const screenshots = copyFeatureScreenshots(slug, dir);
    return { ...meta, test_source, screenshots };
  });
}
