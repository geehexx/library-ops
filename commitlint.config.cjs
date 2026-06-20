module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'body-max-line-length': [0],
    'type-enum': [
      2,
      'always',
      ['feat', 'fix', 'docs', 'style', 'refactor', 'perf', 'test', 'build', 'ci', 'chore', 'deps', 'revert']
    ],
    'scope-enum': [
      2,
      'always',
      ['project', 'prd', 'adr', 'agents', 'deploy', 'deps', 'codex', 'control-plane', 'speckit', 'taskmaster', 'catalog', 'closeout', 'circulation', 'search', 'seed', 'security', 'ci', 'release', 'render', 'docs', 'tooling', 'auth', 'ux', 'ui', 'visual', 'e2e', 'property', 'a11y']
    ],
    'subject-case': [0]
  }
};
