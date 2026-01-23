# Web Crawling Services

## Overview

The CAI-Service web crawling infrastructure provides a robust, scalable solution for crawling websites, extracting content, and ingesting data into the knowledge pipeline. This system enables automated content discovery through sitemap parsing, intelligent page crawling with browser automation, and seamless integration with the document processing pipeline for vector embeddings and knowledge indexing.

The crawling services are designed to handle enterprise-scale web scraping operations while respecting rate limits, managing browser resources efficiently, and ensuring reliable content extraction across diverse website architectures.

## Architecture

The web crawling system consists of four primary components:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Web Crawling Pipeline                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │   Sitemap    │───▶│    Crawl     │───▶│    Ingestion     │  │
│  │   Scraper    │    │    Worker    │    │     Worker       │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│         │                   │                     │             │
│         ▼                   ▼                     ▼             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │   URL Queue  │    │   Browser    │    │  Vector Store    │  │
│  │              │    │   Manager    │    │  (Embeddings)    │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## SitemapScraper

### Purpose

The `SitemapScraper` is responsible for discovering URLs from website sitemaps, parsing sitemap indices, and building comprehensive URL lists for crawling operations. It supports standard XML sitemaps, sitemap indices, and handles common sitemap variations.

### Configuration

```typescript
// sitemap-scraper.config.ts
interface SitemapScraperConfig {
  // Maximum number of URLs to extract from a sitemap
  maxUrls: number;
  
  // Timeout for sitemap HTTP requests (ms)
  requestTimeout: number;
  
  // User agent string for requests
  userAgent: string;
  
  // Whether to follow sitemap index files
  followSitemapIndex: boolean;
  
  // URL patterns to include (regex)
  includePatterns: RegExp[];
  
  // URL patterns to exclude (regex)
  excludePatterns: RegExp[];
  
  // Rate limiting between requests (ms)
  requestDelay: number;
}

const defaultConfig: SitemapScraperConfig = {
  maxUrls: 10000,
  requestTimeout: 30000,
  userAgent: 'CAI-Service-Crawler/1.0',
  followSitemapIndex: true,
  includePatterns: [],
  excludePatterns: [/\.(jpg|jpeg|png|gif|pdf|zip)$/i],
  requestDelay: 100
};
```

### Usage

```typescript
import { SitemapScraper } from '@cai-service/crawl-worker';

// Initialize the scraper
const scraper = new SitemapScraper({
  maxUrls: 5000,
  includePatterns: [/\/blog\//, /\/docs\//],
  excludePatterns: [/\/admin\//, /\/api\//]
});

// Scrape a sitemap
async function discoverUrls(baseUrl: string): Promise<string[]> {
  try {
    const sitemapUrl = `${baseUrl}/sitemap.xml`;
    const urls = await scraper.scrape(sitemapUrl);
    
    console.log(`Discovered ${urls.length} URLs from sitemap`);
    return urls;
  } catch (error) {
    // Fallback: try common sitemap locations
    const fallbackLocations = [
      '/sitemap_index.xml',
      '/sitemap-index.xml',
      '/sitemaps/sitemap.xml'
    ];
    
    for (const location of fallbackLocations) {
      try {
        const urls = await scraper.scrape(`${baseUrl}${location}`);
        if (urls.length > 0) return urls;
      } catch (e) {
        continue;
      }
    }
    
    throw new Error('No valid sitemap found');
  }
}
```

### Handling Sitemap Indices

```typescript
// The scraper automatically handles sitemap indices
interface SitemapEntry {
  loc: string;
  lastmod?: string;
  changefreq?: 'always' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'never';
  priority?: number;
}

async function scrapeWithMetadata(sitemapUrl: string): Promise<SitemapEntry[]> {
  const scraper = new SitemapScraper({ followSitemapIndex: true });
  
  const entries = await scraper.scrapeWithMetadata(sitemapUrl);
  
  // Filter by priority or last modified date
  const highPriorityUrls = entries
    .filter(entry => (entry.priority ?? 0.5) >= 0.7)
    .sort((a, b) => (b.priority ?? 0.5) - (a.priority ?? 0.5));
  
  return highPriorityUrls;
}
```

## CrawlWorker

### Purpose

The `CrawlWorker` handles the actual page fetching, content extraction, and initial processing of web pages. It manages concurrent crawling operations, handles retries, and coordinates with the browser management system.

### Configuration

```typescript
// crawl-worker.config.ts
interface CrawlWorkerConfig {
  // Maximum concurrent pages to crawl
  concurrency: number;
  
  // Maximum retries per URL
  maxRetries: number;
  
  // Delay between retries (ms)
  retryDelay: number;
  
  // Page load timeout (ms)
  pageTimeout: number;
  
  // Whether to wait for JavaScript rendering
  waitForJs: boolean;
  
  // CSS selector to wait for before extraction
  waitForSelector?: string;
  
  // Content extraction selectors
  contentSelectors: ContentSelectors;
  
  // Rate limiting configuration
  rateLimit: RateLimitConfig;
}

interface ContentSelectors {
  // Main content area selector
  content: string;
  
  // Title selector
  title: string;
  
  // Elements to remove before extraction
  removeSelectors: string[];
  
  // Metadata selectors
  metadata: {
    description?: string;
    author?: string;
    publishDate?: string;
  };
}

interface RateLimitConfig {
  // Requests per second per domain
  requestsPerSecond: number;
  
  // Minimum delay between requests to same domain (ms)
  minDelay: number;
  
  // Maximum delay between requests (ms)
  maxDelay: number;
}
```

### Basic Crawling

```typescript
import { CrawlWorker, CrawlResult } from '@cai-service/crawl-worker';

const worker = new CrawlWorker({
  concurrency: 5,
  maxRetries: 3,
  pageTimeout: 30000,
  waitForJs: true,
  contentSelectors: {
    content: 'article, main, .content, #content',
    title: 'h1, title',
    removeSelectors: ['nav', 'footer', 'aside', '.advertisement', '.cookie-banner'],
    metadata: {
      description: 'meta[name="description"]',
      author: 'meta[name="author"]',
      publishDate: 'meta[name="publish-date"], time[datetime]'
    }
  },
  rateLimit: {
    requestsPerSecond: 2,
    minDelay: 500,
    maxDelay: 2000
  }
});

async function crawlUrls(urls: string[]): Promise<CrawlResult[]> {
  const results: CrawlResult[] = [];
  
  // Start the worker
  await worker.start();
  
  // Process URLs in batches
  for await (const result of worker.crawl(urls)) {
    if (result.success) {
      results.push(result);
      console.log(`Crawled: ${result.url} (${result.content.length} chars)`);
    } else {
      console.error(`Failed: ${result.url} - ${result.error}`);
    }
  }
  
  // Gracefully shutdown
  await worker.stop();
  
  return results;
}
```

### Advanced Crawling Options

```typescript
// Custom content extraction with preprocessing
const advancedWorker = new CrawlWorker({
  concurrency: 3,
  waitForJs: true,
  waitForSelector: '.main-content-loaded',
  
  // Custom extraction function
  extractContent: async (page) => {
    // Wait for dynamic content
    await page.waitForSelector('.dynamic-content', { timeout: 5000 });
    
    // Execute custom extraction logic
    const content = await page.evaluate(() => {
      const article = document.querySelector('article');
      if (!article) return null;
      
      // Remove unwanted elements
      article.querySelectorAll('script, style, .ads').forEach(el => el.remove());
      
      return {
        title: document.querySelector('h1')?.textContent?.trim(),
        content: article.innerText,
        html: article.innerHTML,
        links: Array.from(article.querySelectorAll('a[href]'))
          .map(a => a.getAttribute('href'))
          .filter(Boolean)
      };
    });
    
    return content;
  },
  
  // Pre-crawl page setup
  beforeCrawl: async (page, url) => {
    // Set cookies for authentication
    await page.setCookie({
      name: 'session',
      value: process.env.CRAWL_SESSION_TOKEN,
      domain: new URL(url).hostname
    });
    
    // Block unnecessary resources
    await page.setRequestInterception(true);
    page.on('request', (req) => {
      if (['image', 'stylesheet', 'font'].includes(req.resourceType())) {
        req.abort();
      } else {
        req.continue();
      }
    });
  }
});
```

### Crawl Result Structure

```typescript
interface CrawlResult {
  // Original URL
  url: string;
  
  // Final URL after redirects
  finalUrl: string;
  
  // Whether crawl was successful
  success: boolean;
  
  // Error message if failed
  error?: string;
  
  // HTTP status code
  statusCode: number;
  
  // Extracted content
  content: string;
  
  // Raw HTML (optional)
  html?: string;
  
  // Page title
  title: string;
  
  // Extracted metadata
  metadata: {
    description?: string;
    author?: string;
    publishDate?: Date;
    keywords?: string[];
  };
  
  // Discovered links
  links: string[];
  
  // Crawl timestamp
  crawledAt: Date;
  
  // Processing duration (ms)
  duration: number;
}
```

## Browser Management

### BrowserPool

The `BrowserPool` manages Puppeteer/Playwright browser instances efficiently, handling resource allocation, cleanup, and crash recovery.

```typescript
import { BrowserPool, BrowserInstance } from '@cai-service/browser-manager';

const pool = new BrowserPool({
  // Maximum browser instances
  maxBrowsers: 5,
  
  // Maximum pages per browser
  maxPagesPerBrowser: 10,
  
  // Browser launch options
  launchOptions: {
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--disable-gpu',
      '--window-size=1920x1080'
    ]
  },
  
  // Idle timeout before closing browser (ms)
  idleTimeout: 300000,
  
  // Max age before recycling browser (ms)
  maxAge: 3600000,
  
  // Health check interval (ms)
  healthCheckInterval: 60000
});

// Acquire a page from the pool
async function withPage<T>(callback: (page: Page) => Promise<T>): Promise<T> {
  const page = await pool.acquirePage();
  
  try {
    return await callback(page);
  } finally {
    await pool.releasePage(page);
  }
}

// Example usage
const content = await withPage(async (page) => {
  await page.goto('https://example.com', { waitUntil: 'networkidle2' });
  return page.content();
});
```

### Browser Health Monitoring

```typescript
interface BrowserHealth {
  browserId: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  activePages: number;
  memoryUsage: number;
  uptime: number;
  lastActivity: Date;
}

// Monitor browser pool health
pool.on('health', (health: BrowserHealth[]) => {
  const unhealthy = health.filter(h => h.status === 'unhealthy');
  if (unhealthy.length > 0) {
    console.warn(`${unhealthy.length} unhealthy browsers detected`);
  }
});

pool.on('browserCrashed', async (browserId: string) => {
  console.error(`Browser ${browserId} crashed, spawning replacement`);
  // Automatic recovery is handled by the pool
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('Shutting down browser pool...');
  await pool.shutdown();
  process.exit(0);
});
```

## IngestionWorker

### Purpose

The `IngestionWorker` processes crawled content, transforms it into documents, generates vector embeddings, and stores the results in the knowledge base.

### Configuration

```typescript
interface IngestionWorkerConfig {
  // Batch size for processing
  batchSize: number;
  
  // Chunk size for text splitting (tokens)
  chunkSize: number;
  
  // Chunk overlap (tokens)
  chunkOverlap: number;
  
  // Embedding model configuration
  embeddingModel: {
    provider: 'openai' | 'cohere' | 'local';
    model: string;
    dimensions: number;
  };
  
  // Vector store configuration
  vectorStore: {
    type: 'pinecone' | 'weaviate' | 'postgres';
    collection: string;
  };
  
  // Content preprocessing options
  preprocessing: {
    removeHtml: boolean;
    normalizeWhitespace: boolean;
    removeUrls: boolean;
    minContentLength: number;
  };
}
```

### Document Processing Pipeline

```typescript
import { IngestionWorker, Document } from '@cai-service/ingestion-worker';

const ingestionWorker = new IngestionWorker({
  batchSize: 50,
  chunkSize: 512,
  chunkOverlap: 50,
  embeddingModel: {
    provider: 'openai',
    model: 'text-embedding-3-small',
    dimensions: 1536
  },
  vectorStore: {
    type: 'postgres',
    collection: 'knowledge_base'
  },
  preprocessing: {
    removeHtml: true,
    normalizeWhitespace: true,
    removeUrls: false,
    minContentLength: 100
  }
});

async function ingestCrawlResults(results: CrawlResult[]): Promise<void> {
  // Convert crawl results to documents
  const documents: Document[] = results
    .filter(r => r.success && r.content.length >= 100)
    .map(result => ({
      id: generateDocumentId(result.url),
      content: result.content,
      metadata: {
        source: 'web_crawl',
        url: result.url,
        title: result.title,
        crawledAt: result.crawledAt,
        ...result.metadata
      }
    }));
  
  // Process and ingest documents
  const stats = await ingestionWorker.ingest(documents);
  
  console.log(`Ingestion complete:
    - Documents processed: ${stats.documentsProcessed}
    - Chunks created: ${stats.chunksCreated}
    - Embeddings generated: ${stats.embeddingsGenerated}
    - Errors: ${stats.errors.length}
  `);
}
```

### Custom Text Splitting

```typescript
import { TextSplitter, RecursiveCharacterTextSplitter } from '@cai-service/text-processing';

// Configure custom text splitter
const splitter = new RecursiveCharacterTextSplitter({
  chunkSize: 1000,
  chunkOverlap: 200,
  separators: ['\n\n', '\n', '. ', ' ', ''],
  lengthFunction: (text) => {
    // Use token count instead of character count
    return countTokens(text);
  }
});

// Split document into chunks
const chunks = await splitter.splitDocuments(documents);

// Add chunk metadata
const enrichedChunks = chunks.map((chunk, index) => ({
  ...chunk,
  metadata: {
    ...chunk.metadata,
    chunkIndex: index,
    totalChunks: chunks.length
  }
}));
```

## Crawl Configuration

### Environment Variables

```bash
# Browser Configuration
CRAWLER_MAX_BROWSERS=5
CRAWLER_MAX_PAGES_PER_BROWSER=10
CRAWLER_BROWSER_TIMEOUT=60000

# Rate Limiting
CRAWLER_REQUESTS_PER_SECOND=2
CRAWLER_MIN_DELAY_MS=500
CRAWLER_MAX_DELAY_MS=2000

# Content Extraction
CRAWLER_PAGE_TIMEOUT=30000
CRAWLER_WAIT_FOR_JS=true
CRAWLER_MAX_CONTENT_LENGTH=1000000

# Ingestion
INGESTION_BATCH_SIZE=50
INGESTION_CHUNK_SIZE=512
INGESTION_CHUNK_OVERLAP=50

# Embedding Model
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536

# Vector Store
VECTOR_STORE_TYPE=postgres
VECTOR_STORE_COLLECTION=knowledge_base

# Queue Configuration
CRAWL_QUEUE_NAME=crawl-jobs
CRAWL_QUEUE_CONCURRENCY=10
```

### Job Configuration

```typescript
interface CrawlJobConfig {
  // Job identification
  jobId: string;
  name: string;
  
  // Target configuration
  target: {
    // Base URL or sitemap URL
    url: string;
    
    // Discovery method
    discoveryMethod: 'sitemap' | 'crawl' | 'urls';
    
    // For 'urls' method, list of specific URLs
    urls?: string[];
    
    // Maximum URLs to crawl
    maxUrls: number;
    
    // Maximum crawl depth (for 'crawl' method)
    maxDepth?: number;
  };
  
  // URL filtering
  filters: {
    includePatterns: string[];
    excludePatterns: string[];
    includeDomains?: string[];
  };
  
  // Scheduling
  schedule?: {
    cron: string;
    timezone: string;
  };
  
  // Callbacks
  callbacks?: {
    onComplete?: string;
    onError?: string;
    webhook?: string;
  };
}

// Example job configuration
const crawlJob: CrawlJobConfig = {
  jobId: 'docs-crawl-001',
  name: 'Documentation Crawler',
  target: {
    url: 'https://docs.example.com/sitemap.xml',
    discoveryMethod: 'sitemap',
    maxUrls: 1000
  },
  filters: {
    includePatterns: ['^https://docs\\.example\\.com/'],
    excludePatterns: ['/api/', '/internal/', '\\.pdf$']
  },
  schedule: {
    cron: '0 2 * * *',  // Daily at 2 AM
    timezone: 'UTC'
  },
  callbacks: {
    webhook: 'https://api.internal.com/crawl-complete'
  }
};
```

## Best Practices

### 1. Rate Limiting and Politeness

```typescript
// Always implement respectful crawling
const politeConfig = {
  // Check robots.txt
  respectRobotsTxt: true,
  
  // Reasonable rate limiting
  rateLimit: {
    requestsPerSecond: 1,
    minDelay: 1000
  },
  
  // Identify your crawler
  userAgent: 'CAI-Service-Bot/1.0 (+https://yoursite.com/bot-info)',
  
  // Honor Crawl-delay directive
  honorCrawlDelay: true
};
```

### 2. Error Handling and Retries

```typescript
async function robustCrawl(url: string): Promise<CrawlResult> {
  const maxRetries = 3;
  const backoffMs = 1000;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await crawlWorker.crawlUrl(url);
    } catch (error) {
      if (attempt === maxRetries) throw error;
      
      const delay = backoffMs * Math.pow(2, attempt - 1);
      console.log(`Retry ${attempt}/${maxRetries} for ${url} in ${delay}ms`);
      await sleep(delay);
    }
  }
  
  throw new Error('Unreachable');
}
```

### 3. Resource Management

```typescript
// Implement proper cleanup
class CrawlService {
  private pool: BrowserPool;
  private worker: CrawlWorker;
  
  async shutdown(): Promise<void> {
    // Stop accepting new jobs
    await this.worker.stop();
    
    // Wait for in-flight requests
    await this.worker.drain();
    
    // Close browser pool
    await this.pool.shutdown();
    
    // Close database connections
    await this.db.close();
  }
}

// Handle process signals
process.on('SIGINT', () => service.shutdown());
process.on('SIGTERM', () => service.shutdown());
```

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Browser crashes frequently | Memory exhaustion | Reduce `maxPagesPerBrowser`, enable resource blocking |
| Slow crawling | Rate limiting too aggressive | Increase `requestsPerSecond` (if allowed) |
| Missing content | JavaScript rendering needed | Enable `waitForJs`, increase `pageTimeout` |
| Duplicate content | Same URL with different parameters | Normalize URLs, use canonical URL detection |
| Blocked by site | Bot detection | Rotate user agents, use proxy rotation |

### Debug Mode

```typescript
// Enable verbose logging for troubleshooting
const debugWorker = new CrawlWorker({
  debug: true,
  logLevel: 'debug',
  
  // Capture screenshots on error
  captureScreenshotOnError: true,
  screenshotPath: './debug/screenshots',
  
  // Save HTML on extraction failure
  saveHtmlOnError: true,
  htmlPath: './debug/html'
});

debugWorker.on('debug', (event) => {
  console.log(`[${event.type}] ${event.url}: ${event.message}`);
});
```

## Related Documentation

- [Document Processing Pipeline](./document-processing.md)
- [Vector Embeddings Configuration](./vector-embeddings.md)
- [Knowledge Base API](./knowledge-api.md)
- [Queue Management](./queue-management.md)