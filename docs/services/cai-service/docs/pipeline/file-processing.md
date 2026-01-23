# File Processing

## Overview

The cai-service implements a robust file processing system using the Factory design pattern to handle various document types during knowledge ingestion. This system enables the Conversational AI service to extract, parse, and process content from multiple file formats including PDF, CSV, JSON, and TXT files, preparing them for vector embedding and knowledge indexing.

The file processing architecture is designed with extensibility in mind, allowing developers to easily add support for new file types while maintaining a consistent interface across all processors. This documentation covers the complete file processing system, from the core FileFactory pattern to individual processor implementations and guidelines for extending the system.

## FileFactory Pattern

### Architecture Overview

The FileFactory serves as the central orchestrator for file processing operations. It implements the Factory Method design pattern, which provides a clean abstraction for creating file processor instances based on file type detection.

```typescript
// packages/ingestion/src/factories/FileFactory.ts

import { FileProcessor } from '../interfaces/FileProcessor';
import { PDFProcessor } from '../processors/PDFProcessor';
import { CSVProcessor } from '../processors/CSVProcessor';
import { JSONProcessor } from '../processors/JSONProcessor';
import { TXTProcessor } from '../processors/TXTProcessor';
import { UnsupportedFileTypeError } from '../errors/UnsupportedFileTypeError';

export type SupportedFileType = 'pdf' | 'csv' | 'json' | 'txt';

export interface FileFactoryOptions {
  maxFileSize?: number;
  encoding?: BufferEncoding;
  chunkSize?: number;
}

export class FileFactory {
  private static processors: Map<SupportedFileType, new () => FileProcessor> = new Map([
    ['pdf', PDFProcessor],
    ['csv', CSVProcessor],
    ['json', JSONProcessor],
    ['txt', TXTProcessor],
  ]);

  private options: FileFactoryOptions;

  constructor(options: FileFactoryOptions = {}) {
    this.options = {
      maxFileSize: options.maxFileSize || 50 * 1024 * 1024, // 50MB default
      encoding: options.encoding || 'utf-8',
      chunkSize: options.chunkSize || 1000,
    };
  }

  public createProcessor(fileType: SupportedFileType): FileProcessor {
    const ProcessorClass = FileFactory.processors.get(fileType);
    
    if (!ProcessorClass) {
      throw new UnsupportedFileTypeError(
        `File type '${fileType}' is not supported. Supported types: ${this.getSupportedTypes().join(', ')}`
      );
    }

    return new ProcessorClass();
  }

  public static registerProcessor(
    fileType: SupportedFileType,
    processor: new () => FileProcessor
  ): void {
    FileFactory.processors.set(fileType, processor);
  }

  public getSupportedTypes(): SupportedFileType[] {
    return Array.from(FileFactory.processors.keys());
  }

  public detectFileType(filename: string): SupportedFileType | null {
    const extension = filename.split('.').pop()?.toLowerCase();
    return FileFactory.processors.has(extension as SupportedFileType)
      ? (extension as SupportedFileType)
      : null;
  }
}
```

### FileProcessor Interface

All file processors must implement the `FileProcessor` interface, ensuring consistency across different file type handlers:

```typescript
// packages/ingestion/src/interfaces/FileProcessor.ts

export interface ProcessingResult {
  content: string;
  metadata: FileMetadata;
  chunks: ContentChunk[];
}

export interface FileMetadata {
  filename: string;
  fileSize: number;
  mimeType: string;
  processedAt: Date;
  pageCount?: number;
  rowCount?: number;
  characterCount: number;
  customMetadata?: Record<string, unknown>;
}

export interface ContentChunk {
  id: string;
  content: string;
  startPosition: number;
  endPosition: number;
  pageNumber?: number;
  rowIndex?: number;
}

export interface ProcessingOptions {
  extractMetadata?: boolean;
  chunkSize?: number;
  overlapSize?: number;
  preserveFormatting?: boolean;
}

export interface FileProcessor {
  readonly supportedMimeTypes: string[];
  readonly fileExtension: string;
  
  process(buffer: Buffer, options?: ProcessingOptions): Promise<ProcessingResult>;
  validate(buffer: Buffer): Promise<boolean>;
  extractMetadata(buffer: Buffer): Promise<FileMetadata>;
}
```

### Basic Usage

```typescript
// Example: Processing a file through the FileFactory

import { FileFactory } from '@cai-service/ingestion';

async function processUploadedFile(
  fileBuffer: Buffer,
  filename: string
): Promise<ProcessingResult> {
  const factory = new FileFactory({
    maxFileSize: 100 * 1024 * 1024, // 100MB
    chunkSize: 500,
  });

  // Detect file type from filename
  const fileType = factory.detectFileType(filename);
  
  if (!fileType) {
    throw new Error(`Unsupported file type for: ${filename}`);
  }

  // Create appropriate processor
  const processor = factory.createProcessor(fileType);

  // Validate the file
  const isValid = await processor.validate(fileBuffer);
  if (!isValid) {
    throw new Error(`Invalid ${fileType} file: ${filename}`);
  }

  // Process the file
  const result = await processor.process(fileBuffer, {
    extractMetadata: true,
    chunkSize: 500,
    overlapSize: 50,
  });

  return result;
}
```

## PDF Processing

### Overview

The PDF processor handles Portable Document Format files, extracting text content while preserving structural information such as page boundaries and reading order. It utilizes the `pdf-parse` library for reliable text extraction.

### Implementation

```typescript
// packages/ingestion/src/processors/PDFProcessor.ts

import pdf from 'pdf-parse';
import { v4 as uuidv4 } from 'uuid';
import {
  FileProcessor,
  ProcessingResult,
  ProcessingOptions,
  FileMetadata,
  ContentChunk,
} from '../interfaces/FileProcessor';

export class PDFProcessor implements FileProcessor {
  readonly supportedMimeTypes = ['application/pdf'];
  readonly fileExtension = 'pdf';

  async process(
    buffer: Buffer,
    options: ProcessingOptions = {}
  ): Promise<ProcessingResult> {
    const {
      extractMetadata = true,
      chunkSize = 1000,
      overlapSize = 100,
      preserveFormatting = false,
    } = options;

    const pdfData = await pdf(buffer, {
      // Custom render function for better text extraction
      pagerender: preserveFormatting ? this.renderPageWithFormatting : undefined,
    });

    const content = this.normalizeText(pdfData.text);
    const chunks = this.createChunks(content, chunkSize, overlapSize, pdfData.numpages);
    
    const metadata: FileMetadata = extractMetadata
      ? await this.extractMetadata(buffer)
      : this.createBasicMetadata(buffer, content);

    return {
      content,
      metadata,
      chunks,
    };
  }

  async validate(buffer: Buffer): Promise<boolean> {
    try {
      // Check PDF magic bytes
      const header = buffer.slice(0, 5).toString();
      if (header !== '%PDF-') {
        return false;
      }

      // Attempt to parse to ensure validity
      await pdf(buffer, { max: 1 }); // Only parse first page for validation
      return true;
    } catch {
      return false;
    }
  }

  async extractMetadata(buffer: Buffer): Promise<FileMetadata> {
    const pdfData = await pdf(buffer);
    
    return {
      filename: '',
      fileSize: buffer.length,
      mimeType: 'application/pdf',
      processedAt: new Date(),
      pageCount: pdfData.numpages,
      characterCount: pdfData.text.length,
      customMetadata: {
        pdfVersion: pdfData.info?.PDFFormatVersion,
        title: pdfData.info?.Title,
        author: pdfData.info?.Author,
        subject: pdfData.info?.Subject,
        keywords: pdfData.info?.Keywords,
        creator: pdfData.info?.Creator,
        producer: pdfData.info?.Producer,
        creationDate: pdfData.info?.CreationDate,
        modificationDate: pdfData.info?.ModDate,
      },
    };
  }

  private normalizeText(text: string): string {
    return text
      .replace(/\r\n/g, '\n')
      .replace(/\r/g, '\n')
      .replace(/\n{3,}/g, '\n\n')
      .replace(/[ \t]+/g, ' ')
      .trim();
  }

  private createChunks(
    content: string,
    chunkSize: number,
    overlapSize: number,
    pageCount: number
  ): ContentChunk[] {
    const chunks: ContentChunk[] = [];
    let position = 0;

    while (position < content.length) {
      const endPosition = Math.min(position + chunkSize, content.length);
      const chunkContent = content.slice(position, endPosition);

      chunks.push({
        id: uuidv4(),
        content: chunkContent,
        startPosition: position,
        endPosition,
        pageNumber: this.estimatePageNumber(position, content.length, pageCount),
      });

      position = endPosition - overlapSize;
      if (position < 0) position = 0;
      if (endPosition === content.length) break;
    }

    return chunks;
  }

  private estimatePageNumber(
    position: number,
    totalLength: number,
    pageCount: number
  ): number {
    return Math.ceil((position / totalLength) * pageCount) || 1;
  }

  private renderPageWithFormatting(pageData: any): Promise<string> {
    // Custom rendering logic to preserve formatting
    return pageData.getTextContent().then((textContent: any) => {
      let lastY = -1;
      let text = '';
      
      for (const item of textContent.items) {
        if (lastY !== item.transform[5] && lastY !== -1) {
          text += '\n';
        }
        text += item.str;
        lastY = item.transform[5];
      }
      
      return text;
    });
  }

  private createBasicMetadata(buffer: Buffer, content: string): FileMetadata {
    return {
      filename: '',
      fileSize: buffer.length,
      mimeType: 'application/pdf',
      processedAt: new Date(),
      characterCount: content.length,
    };
  }
}
```

### Usage Examples

```typescript
// Processing a PDF file
import { PDFProcessor } from '@cai-service/ingestion';
import * as fs from 'fs';

async function processPDFDocument(filePath: string) {
  const processor = new PDFProcessor();
  const buffer = fs.readFileSync(filePath);

  // Validate the PDF
  if (!(await processor.validate(buffer))) {
    throw new Error('Invalid PDF file');
  }

  // Process with custom options
  const result = await processor.process(buffer, {
    extractMetadata: true,
    chunkSize: 800,
    overlapSize: 100,
    preserveFormatting: true,
  });

  console.log(`Extracted ${result.chunks.length} chunks from ${result.metadata.pageCount} pages`);
  console.log(`Document title: ${result.metadata.customMetadata?.title}`);
  
  return result;
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `extractMetadata` | boolean | true | Extract PDF metadata (author, title, etc.) |
| `chunkSize` | number | 1000 | Characters per chunk |
| `overlapSize` | number | 100 | Overlap between consecutive chunks |
| `preserveFormatting` | boolean | false | Attempt to preserve text formatting |

### Edge Cases and Considerations

- **Scanned PDFs**: Documents that are scanned images without OCR will return empty or minimal text. Consider integrating an OCR service for such documents.
- **Encrypted PDFs**: Password-protected PDFs will fail validation. Implement password handling if needed.
- **Large PDFs**: Files with hundreds of pages should be processed with streaming to avoid memory issues.

## CSV Processing

### Overview

The CSV processor handles comma-separated value files, supporting various delimiters, quote characters, and encoding schemes. It converts tabular data into structured content suitable for knowledge ingestion.

### Implementation

```typescript
// packages/ingestion/src/processors/CSVProcessor.ts

import { parse, Options as CSVParseOptions } from 'csv-parse/sync';
import { v4 as uuidv4 } from 'uuid';
import {
  FileProcessor,
  ProcessingResult,
  ProcessingOptions,
  FileMetadata,
  ContentChunk,
} from '../interfaces/FileProcessor';

export interface CSVProcessingOptions extends ProcessingOptions {
  delimiter?: string;
  quote?: string;
  escape?: string;
  hasHeader?: boolean;
  columns?: string[] | boolean;
  skipEmptyLines?: boolean;
  rowsPerChunk?: number;
}

export class CSVProcessor implements FileProcessor {
  readonly supportedMimeTypes = ['text/csv', 'application/csv'];
  readonly fileExtension = 'csv';

  async process(
    buffer: Buffer,
    options: CSVProcessingOptions = {}
  ): Promise<ProcessingResult> {
    const {
      extractMetadata = true,
      delimiter = ',',
      quote = '"',
      escape = '"',
      hasHeader = true,
      columns = hasHeader,
      skipEmptyLines = true,
      rowsPerChunk = 50,
    } = options;

    const csvContent = buffer.toString('utf-8');
    
    const parseOptions: CSVParseOptions = {
      delimiter,
      quote,
      escape,
      columns,
      skip_empty_lines: skipEmptyLines,
      trim: true,
      relax_column_count: true,
    };

    const records = parse(csvContent, parseOptions) as Record<string, string>[];
    const content = this.recordsToText(records, hasHeader);
    const chunks = this.createRowChunks(records, rowsPerChunk);

    const metadata: FileMetadata = {
      filename: '',
      fileSize: buffer.length,
      mimeType: 'text/csv',
      processedAt: new Date(),
      rowCount: records.length,
      characterCount: content.length,
      customMetadata: {
        columnCount: records.length > 0 ? Object.keys(records[0]).length : 0,
        columns: records.length > 0 ? Object.keys(records[0]) : [],
        delimiter,
        hasHeader,
      },
    };

    return {
      content,
      metadata,
      chunks,
    };
  }

  async validate(buffer: Buffer): Promise<boolean> {
    try {
      const content = buffer.toString('utf-8');
      
      // Check for basic CSV structure
      if (!content.trim()) {
        return false;
      }

      // Attempt to parse first few lines
      const lines = content.split('\n').slice(0, 10).join('\n');
      parse(lines, { relax_column_count: true });
      
      return true;
    } catch {
      return false;
    }
  }

  async extractMetadata(buffer: Buffer): Promise<FileMetadata> {
    const result = await this.process(buffer, { extractMetadata: true });
    return result.metadata;
  }

  private recordsToText(
    records: Record<string, string>[],
    includeHeaders: boolean
  ): string {
    if (records.length === 0) return '';

    const lines: string[] = [];
    
    if (includeHeaders && records.length > 0) {
      const headers = Object.keys(records[0]);
      lines.push(`Columns: ${headers.join(', ')}`);
      lines.push('');
    }

    records.forEach((record, index) => {
      const rowText = Object.entries(record)
        .map(([key, value]) => `${key}: ${value}`)
        .join('; ');
      lines.push(`Row ${index + 1}: ${rowText}`);
    });

    return lines.join('\n');
  }

  private createRowChunks(
    records: Record<string, string>[],
    rowsPerChunk: number
  ): ContentChunk[] {
    const chunks: ContentChunk[] = [];
    
    for (let i = 0; i < records.length; i += rowsPerChunk) {
      const chunkRecords = records.slice(i, i + rowsPerChunk);
      const chunkContent = chunkRecords
        .map((record, idx) => {
          return Object.entries(record)
            .map(([key, value]) => `${key}: ${value}`)
            .join('; ');
        })
        .join('\n');

      chunks.push({
        id: uuidv4(),
        content: chunkContent,
        startPosition: i,
        endPosition: Math.min(i + rowsPerChunk, records.length),
        rowIndex: i,
      });
    }

    return chunks;
  }
}
```

### Usage Examples

```typescript
// Processing CSV with custom options
import { CSVProcessor } from '@cai-service/ingestion';

async function processCSVData(buffer: Buffer) {
  const processor = new CSVProcessor();

  const result = await processor.process(buffer, {
    delimiter: ';',  // European-style CSV
    hasHeader: true,
    rowsPerChunk: 25,
    skipEmptyLines: true,
  });

  console.log(`Processed ${result.metadata.rowCount} rows`);
  console.log(`Columns: ${result.metadata.customMetadata?.columns}`);

  return result;
}

// Processing TSV (Tab-separated values)
async function processTSVData(buffer: Buffer) {
  const processor = new CSVProcessor();

  return processor.process(buffer, {
    delimiter: '\t',
    hasHeader: true,
  });
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `delimiter` | string | ',' | Field delimiter character |
| `quote` | string | '"' | Quote character for fields |
| `escape` | string | '"' | Escape character within quoted fields |
| `hasHeader` | boolean | true | First row contains column headers |
| `columns` | string[] \| boolean | true | Column names or auto-detect |
| `skipEmptyLines` | boolean | true | Skip empty rows |
| `rowsPerChunk` | number | 50 | Rows per content chunk |

## JSON Processing

### Overview

The JSON processor handles JavaScript Object Notation files, supporting both single objects and arrays of objects. It flattens nested structures and converts them into readable text format for knowledge ingestion.

### Implementation

```typescript
// packages/ingestion/src/processors/JSONProcessor.ts

import { v4 as uuidv4 } from 'uuid';
import {
  FileProcessor,
  ProcessingResult,
  ProcessingOptions,
  FileMetadata,
  ContentChunk,
} from '../interfaces/FileProcessor';

export interface JSONProcessingOptions extends ProcessingOptions {
  flattenDepth?: number;
  arrayItemsPerChunk?: number;
  keyValueSeparator?: string;
  itemSeparator?: string;
}

export class JSONProcessor implements FileProcessor {
  readonly supportedMimeTypes = ['application/json', 'text/json'];
  readonly fileExtension = 'json';

  async process(
    buffer: Buffer,
    options: JSONProcessingOptions = {}
  ): Promise<ProcessingResult> {
    const {
      extractMetadata = true,
      flattenDepth = 10,
      arrayItemsPerChunk = 20,
      keyValueSeparator = ': ',
      itemSeparator = '\n',
      chunkSize = 1000,
    } = options;

    const jsonContent = buffer.toString('utf-8');
    const data = JSON.parse(jsonContent);

    const flattenedData = this.flattenObject(data, flattenDepth);
    const content = this.dataToText(flattenedData, keyValueSeparator, itemSeparator);
    const chunks = Array.isArray(data)
      ? this.createArrayChunks(data, arrayItemsPerChunk)
      : this.createObjectChunks(content, chunkSize);

    const metadata: FileMetadata = {
      filename: '',
      fileSize: buffer.length,
      mimeType: 'application/json',
      processedAt: new Date(),
      characterCount: content.length,
      customMetadata: {
        isArray: Array.isArray(data),
        itemCount: Array.isArray(data) ? data.length : 1,
        topLevelKeys: Array.isArray(data)
          ? (data.length > 0 ? Object.keys(data[0]) : [])
          : Object.keys(data),
        maxDepth: this.calculateDepth(data),
      },
    };

    return {
      content,
      metadata,
      chunks,
    };
  }

  async validate(buffer: Buffer): Promise<boolean> {
    try {
      const content = buffer.toString('utf-8');
      JSON.parse(content);
      return true;
    } catch {
      return false;
    }
  }

  async extractMetadata(buffer: Buffer): Promise<FileMetadata> {
    const result = await this.process(buffer, { extractMetadata: true });
    return result.metadata;
  }

  private flattenObject(
    obj: any,
    maxDepth: number,
    prefix: string = '',
    currentDepth: number = 0
  ): Record<string, any> {
    if (currentDepth >= maxDepth) {
      return { [prefix || 'value']: JSON.stringify(obj) };
    }

    const result: Record<string, any> = {};

    if (Array.isArray(obj)) {
      obj.forEach((item, index) => {
        const key = prefix ? `${prefix}[${index}]` : `[${index}]`;
        if (typeof item === 'object' && item !== null) {
          Object.assign(result, this.flattenObject(item, maxDepth, key, currentDepth + 1));
        } else {
          result[key] = item;
        }
      });
    } else if (typeof obj === 'object' && obj !== null) {
      for (const [key, value] of Object.entries(obj)) {
        const newKey = prefix ? `${prefix}.${key}` : key;
        if (typeof value === 'object' && value !== null) {
          Object.assign(result, this.flattenObject(value, maxDepth, newKey, currentDepth + 1));
        } else {
          result[newKey] = value;
        }
      }
    } else {
      result[prefix || 'value'] = obj;
    }

    return result;
  }

  private dataToText(
    data: Record<string, any>,
    keyValueSeparator: string,
    itemSeparator: string
  ): string {
    return Object.entries(data)
      .map(([key, value]) => `${key}${keyValueSeparator}${value}`)
      .join(itemSeparator);
  }

  private createArrayChunks(data: any[], itemsPerChunk: number): ContentChunk[] {
    const chunks: ContentChunk[] = [];

    for (let i = 0; i < data.length; i += itemsPerChunk) {
      const chunkItems = data.slice(i, i + itemsPerChunk);
      const chunkContent = chunkItems
        .map((item, idx) => `Item ${i + idx + 1}: ${JSON.stringify(item, null, 2)}`)
        .join('\n\n');

      chunks.push({
        id: uuidv4(),
        content: chunkContent,
        startPosition: i,
        endPosition: Math.min(i + itemsPerChunk, data.length),
        rowIndex: i,
      });
    }

    return chunks;
  }

  private createObjectChunks(content: string, chunkSize: number): ContentChunk[] {
    const chunks: ContentChunk[] = [];
    const lines = content.split('\n');
    let currentChunk = '';
    let startPosition = 0;

    lines.forEach((line, index) => {
      if (currentChunk.length + line.length > chunkSize && currentChunk) {
        chunks.push({
          id: uuidv4(),
          content: currentChunk.trim(),
          startPosition,
          endPosition: index,
        });
        currentChunk = '';
        startPosition = index;
      }
      currentChunk += line + '\n';
    });

    if (currentChunk.trim()) {
      chunks.push({
        id: uuidv4(),
        content: currentChunk.trim(),
        startPosition,
        endPosition: lines.length,
      });
    }

    return chunks;
  }

  private calculateDepth(obj: any, currentDepth: number = 0): number {
    if (typeof obj !== 'object' || obj === null) {
      return currentDepth;
    }

    const values = Array.isArray(obj) ? obj : Object.values(obj);
    if (values.length === 0) {
      return currentDepth + 1;
    }

    return Math.max(...values.map(v => this.calculateDepth(v, currentDepth + 1)));
  }
}
```

### Usage Examples

```typescript
// Processing JSON data
import { JSONProcessor } from '@cai-service/ingestion';

async function processJSONDocument(buffer: Buffer) {
  const processor = new JSONProcessor();

  const result = await processor.process(buffer, {
    flattenDepth: 5,
    arrayItemsPerChunk: 10,
    keyValueSeparator: ' = ',
  });

  console.log(`JSON type: ${result.metadata.customMetadata?.isArray ? 'Array' : 'Object'}`);
  console.log(`Items/Keys: ${result.metadata.customMetadata?.itemCount}`);
  console.log(`Max depth: ${result.metadata.customMetadata?.maxDepth}`);

  return result;
}
```

## TXT Processing

### Overview

The TXT processor handles plain text files with various encodings. It provides intelligent chunking based on paragraph and sentence boundaries for optimal knowledge retrieval.

### Implementation

```typescript
// packages/ingestion/src/processors/TXTProcessor.ts

import { v4 as uuidv4 } from 'uuid';
import {
  FileProcessor,
  ProcessingResult,
  ProcessingOptions,
  FileMetadata,
  ContentChunk,
} from '../interfaces/FileProcessor';

export interface TXTProcessingOptions extends ProcessingOptions {
  encoding?: BufferEncoding;
  chunkByParagraph?: boolean;
  minChunkSize?: number;
  sentenceBoundary?: boolean;
}

export class TXTProcessor implements FileProcessor {
  readonly supportedMimeTypes = ['text/plain'];
  readonly fileExtension = 'txt';

  async process(
    buffer: Buffer,
    options: TXTProcessingOptions = {}
  ): Promise<ProcessingResult> {
    const {
      encoding = 'utf-8',
      chunkSize = 1000,
      overlapSize = 100,
      chunkByParagraph = false,
      minChunkSize = 100,
      sentenceBoundary = true,
    } = options;

    const content = this.normalizeText(buffer.toString(encoding));
    
    const chunks = chunkByParagraph
      ? this.createParagraphChunks(content, minChunkSize)
      : this.createSentenceAwareChunks(content, chunkSize, overlapSize, sentenceBoundary);

    const metadata: FileMetadata = {
      filename: '',
      fileSize: buffer.length,
      mimeType: 'text/plain',
      processedAt: new Date(),
      characterCount: content.length,
      customMetadata: {
        wordCount: this.countWords(content),
        lineCount: content.split('\n').length,
        paragraphCount: content.split(/\n\n+/).filter(p => p.trim()).length,
        encoding,
      },
    };

    return {
      content,
      metadata,
      chunks,
    };
  }

  async validate(buffer: Buffer): Promise<boolean> {
    try {
      // Check if buffer can be decoded as text
      const content = buffer.toString('utf-8');
      
      // Check for binary content (null bytes)
      if (content.includes('\0')) {
        return false;
      }

      // Check for reasonable text content
      const printableRatio = this.calculatePrintableRatio(content);
      return printableRatio > 0.9; // 90% printable characters
    } catch {
      return false;
    }
  }

  async extractMetadata(buffer: Buffer): Promise<FileMetadata> {
    const result = await this.process(buffer, { extractMetadata: true });
    return result.metadata;
  }

  private normalizeText(text: string): string {
    return text
      .replace(/\r\n/g, '\n')
      .replace(/\r/g, '\n')
      .replace(/\t/g, '    ')
      .trim();
  }

  private createParagraphChunks(content: string, minChunkSize: number): ContentChunk[] {
    const paragraphs = content.split(/\n\n+/).filter(p => p.trim());
    const chunks: ContentChunk[] = [];
    let currentChunk = '';
    let startPosition = 0;
    let position = 0;

    paragraphs.forEach((paragraph, index) => {
      const trimmedParagraph = paragraph.trim();
      
      if (currentChunk.length + trimmedParagraph.length < minChunkSize) {
        currentChunk += (currentChunk ? '\n\n' : '') + trimmedParagraph;
      } else {
        if (currentChunk) {
          chunks.push({
            id: uuidv4(),
            content: currentChunk,
            startPosition,
            endPosition: position,
          });
        }
        currentChunk = trimmedParagraph;
        startPosition = position;
      }
      
      position += trimmedParagraph.length + 2; // Account for \n\n
    });

    if (currentChunk) {
      chunks.push({
        id: uuidv4(),
        content: currentChunk,
        startPosition,
        endPosition: content.length,
      });
    }

    return chunks;
  }

  private createSentenceAwareChunks(
    content: string,
    chunkSize: number,
    overlapSize: number,
    sentenceBoundary: boolean
  ): ContentChunk[] {
    if (!sentenceBoundary) {
      return this.createSimpleChunks(content, chunkSize, overlapSize);
    }

    const sentences = this.splitIntoSentences(content);
    const chunks: ContentChunk[] = [];
    let currentChunk = '';
    let startPosition = 0;
    let position = 0;

    sentences.forEach((sentence) => {
      if (currentChunk.length + sentence.length > chunkSize && currentChunk) {
        chunks.push({
          id: uuidv4(),
          content: currentChunk.trim(),
          startPosition,
          endPosition: position,
        });
        
        // Calculate overlap
        const overlapStart = Math.max(0, currentChunk.length - overlapSize);
        currentChunk = currentChunk.slice(overlapStart);
        startPosition = position - currentChunk.length;
      }
      
      currentChunk += sentence;
      position += sentence.length;
    });

    if (currentChunk.trim()) {
      chunks.push({
        id: uuidv4(),
        content: currentChunk.trim(),
        startPosition,
        endPosition: content.length,
      });
    }

    return chunks;
  }

  private createSimpleChunks(
    content: string,
    chunkSize: number,
    overlapSize: number
  ): ContentChunk[] {
    const chunks: ContentChunk[] = [];
    let position = 0;

    while (position < content.length) {
      const endPosition = Math.min(position + chunkSize, content.length);
      
      chunks.push({
        id: uuidv4(),
        content: content.slice(position, endPosition),
        startPosition: position,
        endPosition,
      });

      position = endPosition - overlapSize;
      if (position < 0) position = 0;
      if (endPosition === content.length) break;
    }

    return chunks;
  }

  private splitIntoSentences(text: string): string[] {
    // Split on sentence boundaries while keeping the delimiter
    return text.split(/(?<=[.!?])\s+/).filter(s => s.trim());
  }

  private countWords(text: string): number {
    return text.split(/\s+/).filter(word => word.length > 0).length;
  }

  private calculatePrintableRatio(text: string): number {
    const printableCount = text.split('').filter(char => {
      const code = char.charCodeAt(0);
      return (code >= 32 && code <= 126) || // ASCII printable
             (code >= 160) || // Extended characters
             char === '\n' || char === '\t' || char === '\r';
    }).length;

    return printableCount / text.length;
  }
}
```

### Usage Examples

```typescript
// Processing text with intelligent chunking
import { TXTProcessor } from '@cai-service/ingestion';

async function processTextDocument(buffer: Buffer) {
  const processor = new TXTProcessor();

  // Chunk by paragraphs for structured documents
  const result = await processor.process(buffer, {
    chunkByParagraph: true,
    minChunkSize: 200,
  });

  console.log(`Word count: ${result.metadata.customMetadata?.wordCount}`);
  console.log(`Paragraphs: ${result.metadata.customMetadata?.paragraphCount}`);

  return result;
}

// Processing with sentence boundary awareness
async function processNarrativeText(buffer: Buffer) {
  const processor = new TXTProcessor();

  return processor.process(buffer, {
    chunkSize: 500,
    overlapSize: 50,
    sentenceBoundary: true,
  });
}
```

## Adding New File Types

### Step-by-Step Guide

Adding support for a new file type involves implementing the `FileProcessor` interface and registering the processor with the FileFactory.

#### Step 1: Create the Processor Class

```typescript
// packages/ingestion/src/processors/XMLProcessor.ts

import { XMLParser } from 'fast-xml-parser';
import { v4 as uuidv4 } from 'uuid';
import {
  FileProcessor,
  ProcessingResult,
  ProcessingOptions,
  FileMetadata,
  ContentChunk,
} from '../interfaces/FileProcessor';

export interface XMLProcessingOptions extends ProcessingOptions {
  ignoreAttributes?: boolean;
  preserveNamespaces?: boolean;
  textNodeName?: string;
}

export class XMLProcessor implements FileProcessor {
  readonly supportedMimeTypes = ['application/xml', 'text/xml'];
  readonly fileExtension = 'xml';

  private parser: XMLParser;

  constructor() {
    this.parser = new XMLParser({
      ignoreAttributes: false,
      attributeNamePrefix: '@_',
      textNodeName: '#text',
    });
  }

  async process(
    buffer: Buffer,
    options: XMLProcessingOptions = {}
  ): Promise<ProcessingResult> {
    const {
      chunkSize = 1000,
      ignoreAttributes = false,
      textNodeName = '#text',
    } = options;

    const xmlContent = buffer.toString('utf-8');
    const parsed = this.parser.parse(xmlContent);
    
    const content = this.xmlToText(parsed);
    const chunks = this.createChunks(content, chunkSize);

    const metadata: FileMetadata = {
      filename: '',
      fileSize: buffer.length,
      mimeType: 'application/xml',
      processedAt: new Date(),
      characterCount: content.length,
      customMetadata: {
        rootElement: Object.keys(parsed)[0],
        hasAttributes: !ignoreAttributes,
      },
    };

    return { content, metadata, chunks };
  }

  async validate(buffer: Buffer): Promise<boolean> {
    try {
      const content = buffer.toString('utf-8');
      
      // Check for XML declaration or root element
      if (!content.trim().startsWith('<?xml') && !content.trim().startsWith('<')) {
        return false;
      }

      this.parser.parse(content);
      return true;
    } catch {
      return false;
    }
  }

  async extractMetadata(buffer: Buffer): Promise<FileMetadata> {
    const result = await this.process(buffer);
    return result.metadata;
  }

  private xmlToText(obj: any, indent: string = ''): string {
    if (typeof obj !== 'object' || obj === null) {
      return String(obj);
    }

    const lines: string[] = [];

    for (const [key, value] of Object.entries(obj)) {
      if (key.startsWith('@_')) {
        lines.push(`${indent}Attribute ${key.slice(2)}: ${value}`);
      } else if (key === '#text') {
        lines.push(`${indent}${value}`);
      } else if (Array.isArray(value)) {
        value.forEach((item, idx) => {
          lines.push(`${indent}${key} [${idx + 1}]:`);
          lines.push(this.xmlToText(item, indent + '  '));
        });
      } else if (typeof value === 'object') {
        lines.push(`${indent}${key}:`);
        lines.push(this.xmlToText(value, indent + '  '));
      } else {
        lines.push(`${indent}${key}: ${value}`);
      }
    }

    return lines.join('\n');
  }

  private createChunks(content: string, chunkSize: number): ContentChunk[] {
    const chunks: ContentChunk[] = [];
    let position = 0;

    while (position < content.length) {
      const endPosition = Math.min(position + chunkSize, content.length);
      
      chunks.push({
        id: uuidv4(),
        content: content.slice(position, endPosition),
        startPosition: position,
        endPosition,
      });

      position = endPosition;
    }

    return chunks;
  }
}
```

#### Step 2: Register the Processor

```typescript
// packages/ingestion/src/index.ts

import { FileFactory } from './factories/FileFactory';
import { XMLProcessor } from './processors/XMLProcessor';

// Register the new processor
FileFactory.registerProcessor('xml', XMLProcessor);

// Export for external use
export { XMLProcessor } from './processors/XMLProcessor';
```

#### Step 3: Update Type Definitions

```typescript
// packages/ingestion/src/factories/FileFactory.ts

// Update the SupportedFileType union
export type SupportedFileType = 'pdf' | 'csv' | 'json' | 'txt' | 'xml';
```

#### Step 4: Add Tests

```typescript
// packages/ingestion/tests/processors/XMLProcessor.test.ts

import { XMLProcessor } from '../../src/processors/XMLProcessor';

describe('XMLProcessor', () => {
  let processor: XMLProcessor;

  beforeEach(() => {
    processor = new XMLProcessor();
  });

  describe('validate', () => {
    it('should return true for valid XML', async () => {
      const buffer = Buffer.from('<?xml version="1.0"?><root><item>test</item></root>');
      expect(await processor.validate(buffer)).toBe(true);
    });

    it('should return false for invalid XML', async () => {
      const buffer = Buffer.from('not xml content');
      expect(await processor.validate(buffer)).toBe(false);
    });
  });

  describe('process', () => {
    it('should extract text content from XML', async () => {
      const xml = '<?xml version="1.0"?><root><title>Test</title><content>Hello World</content></root>';
      const buffer = Buffer.from(xml);
      
      const result = await processor.process(buffer);
      
      expect(result.content).toContain('Test');
      expect(result.content).toContain('Hello World');
      expect(result.metadata.mimeType).toBe('application/xml');
    });
  });
});
```

### Best Practices for Custom Processors

1. **Implement All Interface Methods**: Ensure `process`, `validate`, and `extractMetadata` are fully implemented.

2. **Handle Errors Gracefully**: Wrap parsing operations in try-catch blocks and throw meaningful errors.

3. **Support Configuration Options**: Allow customization through options parameters.

4. **Generate Unique Chunk IDs**: Use UUID or similar for chunk identification.

5. **Include Comprehensive Metadata**: Extract as much useful metadata as possible.

6. **Write Thorough Tests**: Cover edge cases, invalid inputs, and various file formats.

7. **Document MIME Types**: Clearly specify all supported MIME types.

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Empty content from PDF | Scanned document without OCR | Integrate OCR service or reject such files |
| CSV parsing fails | Incorrect delimiter detection | Explicitly specify delimiter in options |
| JSON depth exceeded | Deeply nested structure | Increase `flattenDepth` option |
| Large file memory issues | File exceeds memory limits | Implement streaming processing |
| Encoding errors | Wrong encoding specified | Detect encoding or try multiple encodings |

### Debug Mode

Enable debug logging for troubleshooting:

```typescript
import { FileFactory } from '@cai-service/ingestion';

// Enable debug mode
process.env.FILE_PROCESSOR_DEBUG = 'true';

const factory = new FileFactory();
// Processing will now output debug information
```

## Related Documentation

- [Knowledge Ingestion Pipeline](./knowledge-ingestion.md)
- [Vector Embeddings](./vector-embeddings.md)
- [API Reference - File Upload Endpoint](./api-reference.md#file-upload)
- [Configuration Variables](./configuration.md)