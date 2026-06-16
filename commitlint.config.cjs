module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      ['feat', 'fix', 'docs', 'style', 'refactor', 'perf', 'test', 'build', 'ci', 'chore', 'revert']
    ],
    'scope-enum': [
      2,
      'always',
      ['project', 'prd', 'adr', 'agents', 'codex', 'speckit', 'taskmaster', 'catalog', 'circulation', 'search', 'seed', 'security', 'ci', 'release', 'docs']
    ],
    'subject-case': [0]
  }
};
