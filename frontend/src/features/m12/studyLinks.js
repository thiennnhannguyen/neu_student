/**
 * D-324: link học W3Schools cho ô "Tự học ngoài chương trình". Khóa là đúng chuỗi trong cẩm nang
 * (careers.self_study). D-331: mục W3Schools không có bài thì dẫn sang tài liệu chính thức (OFFICIAL),
 * ghi nguồn trong chữ đọc màn hình. Chỉ gắn trang đã mở được ngày 2026-11-09; mục chung chung không
 * có tài liệu chính thức rõ (testing, RAG, IAM, storytelling…) để chữ thường.
 */
const W3 = 'https://www.w3schools.com/';

const PAGES = {
  html: 'html/',
  css: 'css/',
  responsive: 'css/css_rwd_intro.asp',
  js: 'js/',
  typescript: 'typescript/',
  react: 'react/',
  express: 'nodejs/nodejs_express.asp',
  django: 'django/',
  http: 'tags/ref_httpmethods.asp',
  postgresql: 'postgresql/',
  sql: 'sql/',
  git: 'git/',
  python: 'python/',
  numpy: 'python/numpy/',
  pandas: 'python/pandas/',
  matplotlib: 'python/matplotlib_intro.asp',
  ml: 'python/python_ml_getting_started.asp',
  genai: 'gen_ai/',
  excel: 'excel/',
  statistics: 'statistics/',
  accessibility: 'accessibility/',
  bash: 'bash/',
  aws: 'aws/',
  webSecurity: 'cybersecurity/cybersecurity_web_applications.php',
};

const BY_ITEM = {
  HTML5: 'html',
  CSS3: 'css',
  responsive: 'responsive',
  'JavaScript ES6+': 'js',
  TypeScript: 'typescript',
  React: 'react',
  'React + TypeScript': 'react',
  'Node.js/Express hoặc Python FastAPI/Flask': 'express',
  'Flask/FastAPI/Django hoặc Spring Boot': 'django',
  'HTTP/REST': 'http',
  'REST API': 'http',
  REST: 'http',
  PostgreSQL: 'postgresql',
  SQL: 'sql',
  'SQL cơ bản': 'sql',
  'SQL window functions': 'sql',
  SQLite: 'sql',
  Git: 'git',
  'Git/GitHub Actions': 'git',
  Python: 'python',
  NumPy: 'numpy',
  Pandas: 'pandas',
  'Python Pandas': 'pandas',
  Matplotlib: 'matplotlib',
  'trực quan hóa': 'matplotlib',
  'scikit-learn': 'ml',
  'mô hình Transformer/LLM': 'genai',
  Excel: 'excel',
  'Excel nâng cao': 'excel',
  'A/B testing cơ bản': 'statistics',
  accessibility: 'accessibility',
  'Linux CLI/Bash': 'bash',
  Linux: 'bash',
  'AWS/Azure/GCP': 'aws',
  'OWASP API Security': 'webSecurity',
  'OWASP Top 10 & WSTG': 'webSecurity',
};

const GITHUB_ACTIONS = {
  href: 'https://docs.github.com/en/actions',
  source: 'GitHub Actions Docs',
};
const FIGMA = { href: 'https://help.figma.com/hc/en-us', source: 'Figma Learn' };

/** D-331: tài liệu chính thức cho mục W3Schools không có bài. */
const OFFICIAL = {
  ORM: { href: 'https://docs.sqlalchemy.org/en/21/orm/quickstart.html', source: 'SQLAlchemy Docs' },
  Redis: { href: 'https://redis.io/docs/latest/get-started/', source: 'Redis Docs' },
  'OAuth/JWT': { href: 'https://datatracker.ietf.org/doc/html/rfc7519', source: 'RFC 7519' },
  Docker: { href: 'https://docs.docker.com/get-started/introduction/', source: 'Docker Docs' },
  'pytest/JUnit': {
    href: 'https://docs.pytest.org/en/stable/getting-started.html',
    source: 'pytest Docs',
  },
  'CI/CD': GITHUB_ACTIONS,
  CI: GITHUB_ACTIONS,
  'CI/CD mobile': GITHUB_ACTIONS,
  'Vite/Next.js': { href: 'https://vite.dev/guide/', source: 'Vite Docs' },
  'Figma cơ bản': FIGMA,
  Figma: FIGMA,
  authentication: {
    href: 'https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Authentication',
    source: 'MDN',
  },
  PyTorch: { href: 'https://docs.pytorch.org/tutorials/', source: 'PyTorch Tutorials' },
  FastAPI: { href: 'https://fastapi.tiangolo.com/tutorial/', source: 'FastAPI Docs' },
  'Power BI/Power Query/DAX': {
    href: 'https://learn.microsoft.com/en-us/power-bi/',
    source: 'Microsoft Learn',
  },
  'BPMN 2.0': { href: 'https://www.omg.org/spec/BPMN/2.0/', source: 'OMG' },
  UML: { href: 'https://www.omg.org/spec/UML/', source: 'OMG' },
  Jira: { href: 'https://support.atlassian.com/jira-software-cloud/', source: 'Atlassian Support' },
  Confluence: {
    href: 'https://support.atlassian.com/confluence-cloud/',
    source: 'Atlassian Support',
  },
  'Agile/Scrum': { href: 'https://scrumguides.org/scrum-guide.html', source: 'Scrum Guide' },
  'Kubernetes cơ bản': {
    href: 'https://kubernetes.io/docs/tutorials/kubernetes-basics/',
    source: 'Kubernetes Docs',
  },
  Terraform: {
    href: 'https://developer.hashicorp.com/terraform/tutorials',
    source: 'HashiCorp Developer',
  },
  Nginx: { href: 'https://nginx.org/en/docs/', source: 'nginx Docs' },
  'monitoring (Prometheus/Grafana)': {
    href: 'https://prometheus.io/docs/introduction/overview/',
    source: 'Prometheus Docs',
  },
  Wireshark: {
    href: 'https://www.wireshark.org/docs/wsug_html_chunked/',
    source: "Wireshark User's Guide",
  },
  Postman: { href: 'https://learning.postman.com/docs/', source: 'Postman Docs' },
  'Playwright/Cypress/Selenium': {
    href: 'https://playwright.dev/docs/intro',
    source: 'Playwright Docs',
  },
  'Flutter/Dart hoặc Kotlin Android hoặc Swift iOS': {
    href: 'https://docs.flutter.dev/',
    source: 'Flutter Docs',
  },
  Firebase: { href: 'https://firebase.google.com/docs', source: 'Firebase Docs' },
};

/** { href, source } hoặc null. W3Schools trước, không có thì tài liệu chính thức. */
export function studyLink(item) {
  const page = PAGES[BY_ITEM[item]];
  if (page) {
    return { href: W3 + page, source: 'W3Schools' };
  }
  return OFFICIAL[item] ?? null;
}
