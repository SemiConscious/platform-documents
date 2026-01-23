# Deployment Guide

## Overview

This guide provides comprehensive instructions for building and deploying the FreedomCTI client application across different environments. As a browser-based Computer Telephony Integration (CTI) client embedded within Salesforce as an iframe, the deployment process requires careful attention to environment-specific configurations, build optimizations, and integration testing.

The FreedomCTI platform supports multiple deployment environments including development, QA, staging, and production. Each environment has specific configuration requirements, API endpoints, and WebSocket connections that must be properly configured during the build process.

## Build Process

### Prerequisites

Before beginning the build process, ensure your development environment meets the following requirements:

```bash
# Verify Node.js installation (v16.x or higher recommended)
node --version

# Verify npm installation
npm --version

# Install global dependencies
npm install -g grunt-cli webpack webpack-cli

# Clone the repository and install dependencies
git clone <repository-url>
cd platform-cti-client
npm install
```

### Project Structure

Understanding the project structure is essential for successful builds:

```
platform-cti-client/
├── src/
│   ├── components/          # React components
│   ├── redux/
│   │   ├── actions/         # Redux actions
│   │   ├── reducers/        # Redux reducers
│   │   └── middleware/      # Custom middleware for WebSocket
│   ├── services/            # API and WebSocket services
│   └── utils/               # Utility functions
├── config/
│   ├── webpack.common.js    # Shared webpack configuration
│   ├── webpack.dev.js       # Development webpack config
│   ├── webpack.prod.js      # Production webpack config
│   └── environments/        # Environment-specific configs
├── Gruntfile.js             # Grunt task definitions
├── cypress/                 # E2E test suites
└── dist/                    # Build output directory
```

### Standard Build Commands

The build process follows a multi-stage approach to ensure code quality and optimal bundle sizes:

```bash
# Development build with hot reloading
npm run build:dev

# QA environment build
npm run build:qa

# Staging environment build
npm run build:stage

# Production build with optimizations
npm run build:prod

# Run all builds sequentially
npm run build:all
```

### Build Output

After a successful build, the `dist/` directory contains:

| File/Directory | Description |
|----------------|-------------|
| `index.html` | Main HTML entry point |
| `bundle.[hash].js` | Main JavaScript bundle |
| `vendor.[hash].js` | Third-party dependencies |
| `styles.[hash].css` | Compiled CSS styles |
| `assets/` | Static assets (images, fonts) |
| `manifest.json` | Build manifest for cache busting |

## Grunt Tasks

### Overview of Available Tasks

The Gruntfile.js defines automation tasks for building, testing, and deploying the application:

```javascript
// Gruntfile.js
module.exports = function(grunt) {
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    
    // Clean build directories
    clean: {
      dist: ['dist/*'],
      temp: ['.tmp/*'],
      coverage: ['coverage/*']
    },

    // Copy static assets
    copy: {
      assets: {
        expand: true,
        cwd: 'src/assets',
        src: ['**/*'],
        dest: 'dist/assets/'
      },
      config: {
        expand: true,
        cwd: 'config/environments',
        src: ['<%= env %>.config.js'],
        dest: 'dist/',
        rename: function() {
          return 'dist/environment.config.js';
        }
      }
    },

    // Environment variable injection
    replace: {
      environment: {
        options: {
          patterns: [
            {
              match: 'API_BASE_URL',
              replacement: '<%= apiBaseUrl %>'
            },
            {
              match: 'WEBSOCKET_URL',
              replacement: '<%= websocketUrl %>'
            },
            {
              match: 'SALESFORCE_ORIGIN',
              replacement: '<%= salesforceOrigin %>'
            }
          ]
        },
        files: [{
          expand: true,
          src: ['dist/environment.config.js']
        }]
      }
    },

    // Compress assets for production
    compress: {
      main: {
        options: {
          mode: 'gzip'
        },
        files: [{
          expand: true,
          cwd: 'dist/',
          src: ['**/*.js', '**/*.css'],
          dest: 'dist/',
          ext: function(ext) { return ext + '.gz'; }
        }]
      }
    }
  });

  // Load Grunt plugins
  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-replace');
  grunt.loadNpmTasks('grunt-contrib-compress');

  // Register custom tasks
  grunt.registerTask('build:dev', ['clean:dist', 'copy:assets', 'setEnv:dev', 'copy:config', 'replace:environment']);
  grunt.registerTask('build:qa', ['clean:dist', 'copy:assets', 'setEnv:qa', 'copy:config', 'replace:environment']);
  grunt.registerTask('build:stage', ['clean:dist', 'copy:assets', 'setEnv:stage', 'copy:config', 'replace:environment']);
  grunt.registerTask('build:prod', ['clean:dist', 'copy:assets', 'setEnv:prod', 'copy:config', 'replace:environment', 'compress']);
};
```

### Custom Grunt Tasks

#### Environment Configuration Task

```javascript
// Custom task for setting environment variables
grunt.registerTask('setEnv', 'Set environment configuration', function(env) {
  const envConfigs = {
    dev: {
      apiBaseUrl: 'https://api-dev.freedomcti.com',
      websocketUrl: 'wss://ws-dev.freedomcti.com',
      salesforceOrigin: 'https://dev-salesforce.lightning.force.com'
    },
    qa: {
      apiBaseUrl: 'https://api-qa.freedomcti.com',
      websocketUrl: 'wss://ws-qa.freedomcti.com',
      salesforceOrigin: 'https://qa-salesforce.lightning.force.com'
    },
    stage: {
      apiBaseUrl: 'https://api-stage.freedomcti.com',
      websocketUrl: 'wss://ws-stage.freedomcti.com',
      salesforceOrigin: 'https://stage-salesforce.lightning.force.com'
    },
    prod: {
      apiBaseUrl: 'https://api.freedomcti.com',
      websocketUrl: 'wss://ws.freedomcti.com',
      salesforceOrigin: 'https://salesforce.lightning.force.com'
    }
  };

  const config = envConfigs[env];
  if (!config) {
    grunt.fail.fatal('Invalid environment: ' + env);
  }

  grunt.config.set('env', env);
  grunt.config.set('apiBaseUrl', config.apiBaseUrl);
  grunt.config.set('websocketUrl', config.websocketUrl);
  grunt.config.set('salesforceOrigin', config.salesforceOrigin);
  
  grunt.log.writeln('Environment set to: ' + env);
});
```

#### Deployment Validation Task

```javascript
// Validate build artifacts before deployment
grunt.registerTask('validate', 'Validate build artifacts', function() {
  const done = this.async();
  const fs = require('fs');
  const path = require('path');

  const requiredFiles = [
    'dist/index.html',
    'dist/environment.config.js',
    'dist/assets'
  ];

  let valid = true;
  requiredFiles.forEach(file => {
    if (!fs.existsSync(file)) {
      grunt.log.error('Missing required file: ' + file);
      valid = false;
    }
  });

  // Validate bundle size
  const bundleStats = fs.statSync('dist/bundle.js');
  const maxBundleSize = 2 * 1024 * 1024; // 2MB limit
  if (bundleStats.size > maxBundleSize) {
    grunt.log.warn('Bundle size exceeds recommended limit: ' + 
      (bundleStats.size / 1024 / 1024).toFixed(2) + 'MB');
  }

  done(valid);
});
```

## Webpack Configuration

### Common Configuration

The shared webpack configuration establishes baseline settings used across all environments:

```javascript
// config/webpack.common.js
const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

module.exports = {
  entry: {
    main: './src/index.js',
    vendor: ['react', 'react-dom', 'redux', 'react-redux']
  },
  
  output: {
    path: path.resolve(__dirname, '../dist'),
    filename: '[name].[contenthash].js',
    publicPath: '/',
    clean: true
  },

  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env', '@babel/preset-react'],
            plugins: ['@babel/plugin-transform-runtime']
          }
        }
      },
      {
        test: /\.css$/,
        use: [MiniCssExtractPlugin.loader, 'css-loader', 'postcss-loader']
      },
      {
        test: /\.(png|jpg|gif|svg|woff|woff2|eot|ttf)$/,
        type: 'asset/resource',
        generator: {
          filename: 'assets/[name].[hash][ext]'
        }
      }
    ]
  },

  plugins: [
    new HtmlWebpackPlugin({
      template: './src/index.html',
      inject: true,
      meta: {
        'Content-Security-Policy': {
          'http-equiv': 'Content-Security-Policy',
          content: "frame-ancestors 'self' https://*.salesforce.com https://*.force.com"
        }
      }
    }),
    new MiniCssExtractPlugin({
      filename: 'styles.[contenthash].css'
    })
  ],

  resolve: {
    extensions: ['.js', '.jsx', '.json'],
    alias: {
      '@components': path.resolve(__dirname, '../src/components'),
      '@redux': path.resolve(__dirname, '../src/redux'),
      '@services': path.resolve(__dirname, '../src/services'),
      '@utils': path.resolve(__dirname, '../src/utils')
    }
  },

  optimization: {
    splitChunks: {
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendor',
          chunks: 'all'
        }
      }
    }
  }
};
```

### Development Configuration

```javascript
// config/webpack.dev.js
const { merge } = require('webpack-merge');
const common = require('./webpack.common.js');
const webpack = require('webpack');

module.exports = merge(common, {
  mode: 'development',
  devtool: 'inline-source-map',
  
  devServer: {
    static: './dist',
    hot: true,
    port: 3000,
    historyApiFallback: true,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'X-Frame-Options': 'ALLOW-FROM https://dev-salesforce.lightning.force.com'
    },
    proxy: {
      '/api': {
        target: 'https://api-dev.freedomcti.com',
        changeOrigin: true,
        secure: false
      }
    }
  },

  plugins: [
    new webpack.DefinePlugin({
      'process.env.NODE_ENV': JSON.stringify('development'),
      'process.env.API_BASE_URL': JSON.stringify('https://api-dev.freedomcti.com'),
      'process.env.WEBSOCKET_URL': JSON.stringify('wss://ws-dev.freedomcti.com'),
      'process.env.DEBUG_MODE': JSON.stringify(true)
    }),
    new webpack.HotModuleReplacementPlugin()
  ]
});
```

### Production Configuration

```javascript
// config/webpack.prod.js
const { merge } = require('webpack-merge');
const common = require('./webpack.common.js');
const webpack = require('webpack');
const TerserPlugin = require('terser-webpack-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
const CompressionPlugin = require('compression-webpack-plugin');

module.exports = merge(common, {
  mode: 'production',
  devtool: 'source-map',

  optimization: {
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: true,
            drop_debugger: true
          },
          mangle: true,
          output: {
            comments: false
          }
        },
        extractComments: false
      }),
      new CssMinimizerPlugin()
    ],
    splitChunks: {
      chunks: 'all',
      maxInitialRequests: 25,
      minSize: 20000,
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name(module) {
            const packageName = module.context.match(/[\\/]node_modules[\\/](.*?)([\\/]|$)/)[1];
            return `vendor.${packageName.replace('@', '')}`;
          }
        }
      }
    }
  },

  plugins: [
    new webpack.DefinePlugin({
      'process.env.NODE_ENV': JSON.stringify('production'),
      'process.env.API_BASE_URL': JSON.stringify('https://api.freedomcti.com'),
      'process.env.WEBSOCKET_URL': JSON.stringify('wss://ws.freedomcti.com'),
      'process.env.DEBUG_MODE': JSON.stringify(false)
    }),
    new CompressionPlugin({
      filename: '[path][base].gz',
      algorithm: 'gzip',
      test: /\.(js|css|html|svg)$/,
      threshold: 10240,
      minRatio: 0.8
    }),
    new BundleAnalyzerPlugin({
      analyzerMode: 'static',
      reportFilename: '../reports/bundle-analysis.html',
      openAnalyzer: false
    })
  ],

  performance: {
    hints: 'warning',
    maxEntrypointSize: 512000,
    maxAssetSize: 512000
  }
});
```

## Environment-Specific Builds

### Environment Configuration Files

Each environment requires specific configuration for API endpoints, WebSocket connections, and Salesforce integration:

```javascript
// config/environments/dev.config.js
export default {
  environment: 'development',
  api: {
    baseUrl: 'https://api-dev.freedomcti.com',
    timeout: 30000,
    retryAttempts: 3
  },
  websocket: {
    url: 'wss://ws-dev.freedomcti.com',
    reconnectInterval: 5000,
    maxReconnectAttempts: 10,
    heartbeatInterval: 30000
  },
  salesforce: {
    allowedOrigins: [
      'https://dev-salesforce.lightning.force.com',
      'https://*.sandbox.lightning.force.com'
    ],
    iframeTimeout: 10000
  },
  logging: {
    level: 'debug',
    enableConsole: true,
    enableRemote: false
  },
  features: {
    voicemailPlayback: true,
    callRecording: true,
    debugPanel: true
  }
};
```

```javascript
// config/environments/prod.config.js
export default {
  environment: 'production',
  api: {
    baseUrl: 'https://api.freedomcti.com',
    timeout: 15000,
    retryAttempts: 5
  },
  websocket: {
    url: 'wss://ws.freedomcti.com',
    reconnectInterval: 3000,
    maxReconnectAttempts: 20,
    heartbeatInterval: 25000
  },
  salesforce: {
    allowedOrigins: [
      'https://*.lightning.force.com',
      'https://*.salesforce.com'
    ],
    iframeTimeout: 5000
  },
  logging: {
    level: 'error',
    enableConsole: false,
    enableRemote: true,
    remoteEndpoint: 'https://logs.freedomcti.com/ingest'
  },
  features: {
    voicemailPlayback: true,
    callRecording: true,
    debugPanel: false
  }
};
```

### Building for Specific Environments

```bash
# Development build with source maps
NODE_ENV=development npm run build:dev

# QA build with testing instrumentation
NODE_ENV=qa CYPRESS_INSTRUMENT=true npm run build:qa

# Staging build (mirrors production)
NODE_ENV=staging npm run build:stage

# Production build with full optimizations
NODE_ENV=production npm run build:prod
```

### Environment Validation Script

```javascript
// scripts/validate-environment.js
const https = require('https');

async function validateEnvironment(env) {
  const configs = {
    dev: { api: 'api-dev.freedomcti.com', ws: 'ws-dev.freedomcti.com' },
    qa: { api: 'api-qa.freedomcti.com', ws: 'ws-qa.freedomcti.com' },
    stage: { api: 'api-stage.freedomcti.com', ws: 'ws-stage.freedomcti.com' },
    prod: { api: 'api.freedomcti.com', ws: 'ws.freedomcti.com' }
  };

  const config = configs[env];
  console.log(`Validating ${env} environment...`);

  // Test API endpoint
  try {
    const apiResponse = await testEndpoint(`https://${config.api}/health`);
    console.log(`✓ API endpoint healthy: ${apiResponse.status}`);
  } catch (error) {
    console.error(`✗ API endpoint unreachable: ${error.message}`);
    process.exit(1);
  }

  // Test WebSocket endpoint
  try {
    await testWebSocket(`wss://${config.ws}`);
    console.log(`✓ WebSocket endpoint accessible`);
  } catch (error) {
    console.error(`✗ WebSocket endpoint unreachable: ${error.message}`);
    process.exit(1);
  }

  console.log(`\n${env} environment validation passed!`);
}

const env = process.argv[2] || 'dev';
validateEnvironment(env);
```

## Deployment Checklist

### Pre-Deployment Checklist

Complete the following steps before initiating any deployment:

#### Code Quality Verification

- [ ] All unit tests pass: `npm run test:unit`
- [ ] All integration tests pass: `npm run test:integration`
- [ ] ESLint shows no errors: `npm run lint`
- [ ] TypeScript compilation succeeds (if applicable)
- [ ] Code coverage meets minimum threshold (80%)

#### Build Verification

- [ ] Clean build completes without errors
- [ ] Bundle size within acceptable limits (< 2MB)
- [ ] No console errors in browser
- [ ] Source maps generated correctly

#### Environment Configuration

- [ ] API endpoints configured correctly for target environment
- [ ] WebSocket URLs verified and accessible
- [ ] Salesforce origin whitelist updated
- [ ] Feature flags set appropriately
- [ ] Logging levels configured

### Deployment Steps

#### Step 1: Prepare the Build

```bash
# Clean previous builds
npm run clean

# Run full test suite
npm run test:all

# Generate production build
npm run build:prod

# Validate build artifacts
npm run validate
```

#### Step 2: Run E2E Tests

```bash
# Start the application in test mode
npm run serve:test

# Run Cypress tests against the build
npm run cypress:run

# Generate test report
npm run test:report
```

#### Step 3: Deploy to CDN/Hosting

```bash
# Deploy to AWS S3 (example)
aws s3 sync dist/ s3://freedomcti-prod-bucket/ \
  --delete \
  --cache-control "max-age=31536000" \
  --exclude "*.html" \
  --exclude "environment.config.js"

# Deploy HTML and config with shorter cache
aws s3 cp dist/index.html s3://freedomcti-prod-bucket/ \
  --cache-control "max-age=300"

aws s3 cp dist/environment.config.js s3://freedomcti-prod-bucket/ \
  --cache-control "max-age=300"

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id DISTRIBUTION_ID \
  --paths "/*"
```

#### Step 4: Verify Deployment

```bash
# Run smoke tests against production
npm run test:smoke:prod

# Verify WebSocket connectivity
npm run verify:websocket:prod

# Check Salesforce iframe integration
npm run verify:salesforce:prod
```

### Post-Deployment Checklist

- [ ] Application loads correctly in target environment
- [ ] WebSocket connection establishes successfully
- [ ] Call events received and displayed
- [ ] Voicemail playback functional
- [ ] Call logging creates records in Salesforce
- [ ] No JavaScript errors in browser console
- [ ] Performance metrics within acceptable range
- [ ] Monitoring alerts configured and active

### Rollback Procedure

If issues are detected post-deployment:

```bash
# Revert to previous version
aws s3 sync s3://freedomcti-backup-bucket/previous-version/ \
  s3://freedomcti-prod-bucket/ \
  --delete

# Invalidate CDN cache
aws cloudfront create-invalidation \
  --distribution-id DISTRIBUTION_ID \
  --paths "/*"

# Notify team of rollback
npm run notify:rollback
```

### Deployment Environments Summary

| Environment | Branch | Auto-Deploy | Approval Required |
|-------------|--------|-------------|-------------------|
| Development | `develop` | Yes | No |
| QA | `release/*` | Yes | No |
| Staging | `staging` | No | Tech Lead |
| Production | `main` | No | Release Manager |

## Troubleshooting Common Issues

### Build Failures

**Issue: Out of memory during build**
```bash
# Increase Node.js memory limit
NODE_OPTIONS="--max-old-space-size=4096" npm run build:prod
```

**Issue: Module not found errors**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Deployment Issues

**Issue: Iframe not loading in Salesforce**
- Verify Content-Security-Policy headers
- Check Salesforce Connected App configuration
- Ensure HTTPS is properly configured

**Issue: WebSocket connection failing**
- Verify WebSocket URL is correct for environment
- Check network firewall rules
- Validate SSL certificate

---

*Last updated: 2024*
*Document version: 1.0*