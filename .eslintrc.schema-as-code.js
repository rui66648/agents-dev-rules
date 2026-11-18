/**
 * Schema-As-Code ESLint 配置
 * 
 * 集成设计令牌语义校验规则
 */

const tokenLinter = require('./hooks/design-token-linter.js');

module.exports = {
  extends: ['eslint:recommended'],
  parser: '@babel/eslint-parser',
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true
    }
  },
  plugins: [
    'design-tokens'
  ],
  rules: {
    // 设计令牌语义校验
    'design-tokens/no-semantic-violation': ['error', {
      schemaPath: './schemas/design-tokens.yaml',
      severity: 'error'
    }],
    
    // 禁止硬编码颜色值
    'no-restricted-syntax': ['error', {
      selector: 'Literal[value/^#[0-9A-Fa-f]{6}$/]',
      message: '禁止硬编码颜色值，请使用设计令牌'
    }]
  },
  overrides: [
    {
      files: ['*.css', '*.scss', '*.less'],
      plugins: ['stylelint'],
      rules: {
        'stylelint/design-tokens/color-semantic-domain': ['error', {
          schemaPath: './schemas/design-tokens.yaml'
        }]
      }
    }
  ]
};
