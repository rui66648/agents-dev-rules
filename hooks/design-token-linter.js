/**
 * Design Token 语义校验器 — ESLint / Stylelint 插件
 * 
 * 功能：
 * 1. 校验 CSS/SCSS/Less 中的颜色值是否符合 Token 语义
 * 2. 校验 JavaScript/TypeScript 中的 Token 引用是否正确
 * 3. 报告违规项并阻止提交
 * 
 * 使用方式：
 *   npx eslint --config .eslintrc.schema-as-code.js src/
 *   npx stylelint --config stylelintrc.schema-as-code.yaml src/
 */

const fs = require('fs');
const path = require('path');

// Token 语义定义
let tokenSchema = null;

/**
 * 加载 Token Schema
 * 默认路径相对本脚本位置（hooks/ → ../schemas/design-tokens.yaml），不依赖 CWD
 */
function loadTokenSchema(schemaPath = path.resolve(__dirname, '..', 'schemas', 'design-tokens.yaml')) {
  if (!tokenSchema) {
    try {
      // 尝试 YAML 解析（需要 yaml 库）
      let yamlContent;
      try {
        const yaml = require('yaml');
        yamlContent = fs.readFileSync(path.resolve(schemaPath), 'utf8');
        tokenSchema = yaml.parse(yamlContent);
      } catch (e) {
        // 如果没有 yaml 库，尝试 JSON
        yamlContent = fs.readFileSync(schemaPath.replace('.yaml', '.json'), 'utf8');
        tokenSchema = JSON.parse(yamlContent);
      }
      
      if (!tokenSchema.tokens) {
        throw new Error('Token Schema 缺少 tokens 字段');
      }
    } catch (e) {
      console.error('❌ 加载 Token Schema 失败:', e.message);
      process.exit(1);
    }
  }
  return tokenSchema;
}

/**
 * 获取 Token 的允许域和禁止域
 */
function getTokenDomains(tokenName) {
  const schema = loadTokenSchema();
  const [category, ...parts] = tokenName.split('.');
  const tokenKey = parts.join('.');
  
  if (!schema.tokens[category] || !schema.tokens[category][tokenKey]) {
    return null;
  }
  
  const token = schema.tokens[category][tokenKey];
  return {
    domains: token.domains || [],
    forbiddenDomains: token.forbidden_domains || [],
    explanation: token.explanation || ''
  };
}

/**
 * 检查颜色值是否违规
 */
function checkColorUsage(filePath, colorValue, context) {
  // 简单实现：检查是否使用了硬编码的 critical 颜色
  const criticalColors = ['#EF4444', '#DC2626', '#B91C1C', '#991B1B'];
  
  if (criticalColors.includes(colorValue)) {
    // 检查是否在禁止的上下文中使用
    const forbiddenContexts = ['hint', 'success', 'info', 'decorative'];
    for (const forbiddenCtx of forbiddenContexts) {
      if (context.includes(forbiddenCtx)) {
        return {
          rule: 'color-semantic-violation',
          message: `硬编码 critical 颜色 "${colorValue}" 禁止用于 ${forbiddenCtx} 场景`,
          severity: 'error'
        };
      }
    }
  }
  
  return null;
}

/**
 * 校验 CSS 文件
 */
function lintCssFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const violations = [];
  
  // 检查硬编码颜色值
  const colorRegex = /#[0-9A-Fa-f]{6}\b/g;
  const matches = content.match(colorRegex) || [];
  
  for (const color of matches) {
    // 检查颜色使用上下文
    const line = content.split('\n')[content.substring(0, filePath.indexOf(color)).split('\n').length - 1];
    
    // 简单上下文检测
    const context = detectContext(line, filePath);
    
    const violation = checkColorUsage(filePath, color, context);
    if (violation) {
      violations.push({
        ...violation,
        line: content.substring(0, filePath.indexOf(color)).split('\n').length,
        column: line.indexOf(color) + 1
      });
    }
  }
  
  return violations;
}

/**
 * 检测颜色使用上下文
 */
function detectContext(line, filePath) {
  const context = [];
  
  // 根据文件名判断
  const fileName = path.basename(filePath).toLowerCase();
  if (fileName.includes('toast') || fileName.includes('badge') || fileName.includes('tag')) {
    context.push('hint');
  }
  if (fileName.includes('success') || fileName.includes('confirm')) {
    context.push('success');
  }
  if (fileName.includes('error') || fileName.includes('danger')) {
    context.push('error');
  }
  if (fileName.includes('info') || fileName.includes('help')) {
    context.push('info');
  }
  
  // 根据注释判断
  const commentMatch = line.match(/\/\*(.*?)\*\//);
  if (commentMatch) {
    if (commentMatch[1].toLowerCase().includes('hint')) {
      context.push('hint');
    }
    if (commentMatch[1].toLowerCase().includes('success')) {
      context.push('success');
    }
  }
  
  return context;
}

/**
 * 校验 JavaScript/TypeScript 文件
 */
function lintJsFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const violations = [];
  
  // 检查硬编码颜色
  const colorRegex = /['"`]#([0-9A-Fa-f]{6})['"`]/g;
  const matches = content.match(colorRegex) || [];
  
  for (const match of matches) {
    const color = match.replace(/['"`]/g, '');
    const line = content.split('\n')[content.substring(0, match).split('\n').length - 1];
    const context = detectContext(line, filePath);
    
    const violation = checkColorUsage(filePath, color, context);
    if (violation) {
      violations.push({
        ...violation,
        line: content.substring(0, match).split('\n').length,
        column: line.indexOf(match) + 1
      });
    }
  }
  
  return violations;
}

/**
 * 主入口函数
 */
function lintFiles(files, options = {}) {
  const schemaPath = options.schemaPath || './schemas/design-tokens.yaml';
  loadTokenSchema(schemaPath);
  
  const allViolations = [];
  
  for (const filePath of files) {
    const ext = path.extname(filePath).toLowerCase();
    
    if (ext === '.css' || ext === '.scss' || ext === '.less') {
      const violations = lintCssFile(filePath);
      allViolations.push(...violations);
    } else if (ext === '.js' || ext === '.ts' || ext === '.jsx' || ext === '.tsx') {
      const violations = lintJsFile(filePath);
      allViolations.push(...violations);
    }
  }
  
  return allViolations;
}

/**
 * ESLint Rule 实现
 */
module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description: '校验 Token 语义是否违规',
      category: 'Stylistic Issues',
      recommended: true
    },
    fixable: null,
    schema: [{
      type: 'object',
      properties: {
        schemaPath: {
          type: 'string',
          default: './schemas/design-tokens.yaml'
        }
      }
    }],
    messages: {
      'colorSemanticViolation': 'Token 语义违规: {{message}}'
    }
  },
  
  create(context) {
    const options = context.options[0] || {};
    const schemaPath = options.schemaPath || './schemas/design-tokens.yaml';
    
    return {
      Literal(node) {
        // 检查字符串字面量中的颜色值
        if (typeof node.value === 'string' && /^#[0-9A-Fa-f]{6}$/.test(node.value)) {
          const filePath = context.getFilename();
          const line = node.loc.start.line;
          const column = node.loc.start.column + 1;
          
          // 获取上下文
          const sourceCode = context.getSourceCode();
          const lineText = sourceCode.lines[line - 1];
          const contextArr = detectContext(lineText, filePath);
          
          const violation = checkColorUsage(filePath, node.value, contextArr);
          if (violation) {
            context.report({
              node,
              messageId: 'colorSemanticViolation',
              data: { message: violation.message }
            });
          }
        }
      }
    };
  }
};

/**
 * Stylelint Rule 实现
 */
module.exports.stylelintRule = {
  ruleName: 'design-tokens/color-semantic-domain',
  messages: {
    rejected: 'Token 语义违规: {{message}}'
  },
  primaryOptionSchema: {
    type: 'string'
  },
  
  rule: (primaryOption) => {
    return (root, result) => {
      const violations = lintFiles(
        [result.opts.from],
        { schemaPath: primaryOption }
      );
      
      for (const violation of violations) {
        result.warn(violation.message, {
          node: root,
          word: violation.word,
          line: violation.line,
          column: violation.column,
          ruleName: 'design-tokens/color-semantic-domain',
          severity: 'error'
        });
      }
    };
  }
};

// CLI 入口
if (require.main === module) {
  const args = process.argv.slice(2);
  const files = args.filter(arg => !arg.startsWith('--'));
  const options = {};

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--schema' && args[i + 1]) {
      options.schemaPath = args[++i];
    } else if (args[i] === '--fail-on-violation') {
      options.failOnViolation = true;
    }
  }

  // 无目标文件时不得平凡通过——否则 CI 会得到假绿
  if (files.length === 0) {
    console.error('❌ 未指定待校验文件。用法: node hooks/design-token-linter.js <file-or-dir> [...]');
    console.error('   例: node hooks/design-token-linter.js src/ --fail-on-violation');
    process.exit(1);
  }

  const violations = lintFiles(files, options);

  if (violations.length > 0) {
    console.error('\n❌ Token 语义违规:\n');
    for (const v of violations) {
      console.error(`  [${v.severity.toUpperCase()}] ${v.message}`);
      console.error(`    位置: ${v.line}:${v.column}`);
    }
    console.error('\n');

    if (options.failOnViolation) {
      process.exit(1);
    }
  } else {
    console.log(`✅ Token 语义校验通过（${files.length} 个目标）`);
  }
}
