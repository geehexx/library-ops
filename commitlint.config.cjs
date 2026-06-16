module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      ['feat', 'fix', 'docs', 'style', 'refactor', 'perf', 'test', 'build', 'ci', 'chore', 'deps', 'revert']
    ],
    'scope-enum': [
      2,
      'always',
      ['project', 'prd', 'adr', 'agents', 'codex', 'control-plane', 'speckit', 'taskmaster', 'catalog', 'circulation', 'search', 'seed', 'security', 'ci', 'release', 'docs']
    ],
    'subject-case': [0]
  }
};
