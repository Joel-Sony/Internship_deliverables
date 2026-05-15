// 20 mock blog posts across 4 categories
const POSTS = [
  {
    id: 1, category: 'Technology',
    title: 'What is React and Why It Matters',
    excerpt: 'React is a JavaScript library for building user interfaces. It uses a component-based model and a virtual DOM to make UIs fast and predictable.',
    body: `React was created by Facebook in 2013 and has since become one of the most popular front-end libraries in the world.

At its core, React introduces two key ideas: components and the virtual DOM. Components let you break the UI into small, reusable pieces. The virtual DOM lets React figure out the minimal set of changes needed to update the real browser DOM, keeping things fast.

React's one-way data flow (props down, events up) makes it much easier to reason about state in a large application. Combined with hooks like useState and useEffect, you can manage complex logic inside function components without ever writing a class.

Today React powers huge sites like Facebook, Instagram, Airbnb, and countless others. Its ecosystem — React Router, Redux, React Query, Next.js — means there's a solution for almost any problem you encounter in web development.`,
    date: '2025-01-10', readTime: '5 min',
  },
  {
    id: 2, category: 'Technology',
    title: 'Understanding the Virtual DOM',
    excerpt: 'The virtual DOM is a lightweight in-memory representation of the real DOM. React uses it to batch and minimise updates to the browser.',
    body: `Every time state changes in a React app, React builds a new virtual DOM tree. It then diffs that tree against the previous snapshot using a process called reconciliation.

Only the elements that actually changed are updated in the real DOM. This batching of DOM writes is what makes React fast, because real DOM mutations are the most expensive operations in a browser.

Understanding the virtual DOM also helps you write better React code. Giving list items unique keys, avoiding unnecessary re-renders with memo, and splitting large components all help the reconciler do its job efficiently.

The virtual DOM concept has also influenced other frameworks — Vue.js and Inferno both use similar techniques.`,
    date: '2025-01-18', readTime: '4 min',
  },
  {
    id: 3, category: 'Technology',
    title: 'CSS Grid vs Flexbox: When to Use Which',
    excerpt: 'Both CSS Grid and Flexbox solve layout problems, but they shine in different situations. Here is a straightforward guide.',
    body: `Flexbox is a one-dimensional layout system. It works along a single axis — either a row or a column — and is perfect for aligning items inside a container: a nav bar, a button group, a card's content area.

CSS Grid is two-dimensional. It lets you control rows AND columns simultaneously, making it ideal for page-level layouts — a full site grid, an image gallery, a dashboard with multiple areas.

A practical rule of thumb: use Flexbox for components, use Grid for layouts. In most real projects you'll use both — Grid for the outer shell, Flexbox inside each cell.

Both are fully supported in all modern browsers, so you never need to choose based on compatibility anymore.`,
    date: '2025-02-03', readTime: '3 min',
  },
  {
    id: 4, category: 'Technology',
    title: 'TypeScript Basics Every Developer Should Know',
    excerpt: 'TypeScript adds static types to JavaScript, catching bugs at compile time and making large codebases much easier to navigate.',
    body: `TypeScript is a superset of JavaScript — every valid JS file is also valid TypeScript. You add types gradually, which makes migration from plain JS painless.

The most common features you'll use are: primitive types (string, number, boolean), interfaces and type aliases for object shapes, union types, generics, and utility types like Partial<T> and Required<T>.

The biggest benefit isn't just catching bugs — it's IDE autocomplete. With types in place, your editor knows exactly what properties and methods are available, reducing time spent reading documentation.

TypeScript is now the default in most serious React projects, and both Next.js and Vite have first-class TypeScript support.`,
    date: '2025-02-14', readTime: '6 min',
  },
  {
    id: 5, category: 'Technology',
    title: 'How Browsers Render Web Pages',
    excerpt: 'From HTML bytes to pixels on screen — a step-by-step look at the browser rendering pipeline.',
    body: `When you type a URL, quite a lot happens before you see anything. First the browser fetches the HTML, parses it into a DOM tree. Then it fetches and parses CSS, building the CSSOM. The two trees are combined into a render tree.

Layout (also called reflow) calculates the exact size and position of every element. Paint fills in the pixels. Compositing layers specific elements — like fixed headers or animated elements — onto the GPU for smooth scrolling and animation.

Understanding this pipeline explains why certain optimisations matter: why large CSS files block rendering, why re-layouts triggered by JavaScript are expensive, and why transform and opacity animations are cheaper than changing width or margin (they only trigger compositing, not layout or paint).`,
    date: '2025-03-01', readTime: '5 min',
  },

  {
    id: 6, category: 'Design',
    title: 'The 8-Point Grid System',
    excerpt: 'Using multiples of 8 for spacing and sizing keeps your designs consistent and makes developer hand-off much smoother.',
    body: `The 8-point grid means every spacing value in your design — margins, paddings, gaps — is a multiple of 8: 8, 16, 24, 32, 40, 48…

Why 8? Because most screen densities divide evenly by 8, so you avoid sub-pixel rendering issues. Also, having a finite set of spacing options forces consistency — you can't just add "a bit more padding" without snapping to a grid value.

In practice you can extend it with a 4-point mini-grid for tighter UI elements (icons, chips, badges). The rule: all major layout spacing uses 8-multiples; only fine-grained internal padding can use 4-multiples.

Both Material Design and Apple's Human Interface Guidelines are built around this principle.`,
    date: '2025-01-22', readTime: '3 min',
  },
  {
    id: 7, category: 'Design',
    title: 'Colour Theory for UI Designers',
    excerpt: 'Choosing colours is not just about taste. Understanding hue, saturation, and lightness helps you build accessible, coherent palettes.',
    body: `HSL (Hue, Saturation, Lightness) is the best model for UI colour work because it matches how humans think about colour. Hue is the colour family (0° = red, 120° = green, 240° = blue). Saturation is how vivid. Lightness is how bright.

A solid UI palette usually starts with a base hue, then creates a scale of 9–11 shades by varying lightness (10 % to 95 %) while keeping hue and saturation locked. This gives you consistent tints for backgrounds and strong shades for text.

Accessibility matters: text on backgrounds needs at least a 4.5:1 contrast ratio (WCAG AA). Use tools like Leonardo or Radix Colors which generate accessible scales automatically.`,
    date: '2025-02-08', readTime: '5 min',
  },
  {
    id: 8, category: 'Design',
    title: 'Typography Rules That Actually Matter',
    excerpt: 'Good typography is invisible. Bad typography is distracting. Here are the five rules that make the biggest difference.',
    body: `1. Limit typeface choices. One serif + one sans, or just one versatile sans. More than two fonts usually reads as chaotic.

2. Establish a clear type scale. Use a modular scale (1.25× or 1.333×) to generate sizes: 12, 14, 16, 20, 24, 32, 48… Assign roles: body, label, h3, h2, h1.

3. Line length (measure) should be 60–75 characters for body text. Too wide or too narrow hurts readability.

4. Line height (leading) for body text should be 1.5–1.7×. For headings, tighten it to 1.1–1.3×.

5. Never use pure black (#000) on pure white (#FFF). A dark grey like #111 on #FFF has the same readability with far less eye strain.`,
    date: '2025-02-25', readTime: '4 min',
  },
  {
    id: 9, category: 'Design',
    title: 'Micro-Animations and When to Use Them',
    excerpt: 'Small animations make interfaces feel alive. But overuse is worse than no animation at all.',
    body: `Micro-animations serve specific jobs: confirming actions, guiding attention, providing feedback, and adding delight. Each animation should have a clear purpose.

Rules for good micro-animations:
- Duration: 150–300 ms for most UI transitions. Anything over 500 ms feels sluggish.
- Easing: ease-out for elements entering the screen (fast start, gentle stop). ease-in for elements leaving.
- Only animate transform and opacity where possible — these properties don't trigger layout or paint.

Bad micro-animations: loading spinners on actions that take under 300 ms (they flash annoyingly), page transitions that slide every time (users want content, not a show), hover animations on mobile (there is no hover on touch).`,
    date: '2025-03-10', readTime: '4 min',
  },
  {
    id: 10, category: 'Design',
    title: 'Designing for Accessibility from Day One',
    excerpt: 'Accessibility is not a checklist to tick at the end. Baking it in from the start is faster and produces better designs.',
    body: `Start with semantic HTML. A <button> element is keyboard accessible and announced correctly by screen readers for free. A <div onClick> is not.

Colour contrast is non-negotiable. WCAG AA requires 4.5:1 for normal text. Use a contrast checker as part of your design tool (Figma has plugins; VS Code extensions exist for code).

Don't rely on colour alone to convey meaning. An error state needs text or an icon, not just a red border. Roughly 8 % of males have some form of colour vision deficiency.

Focus states are critical for keyboard users. Never do outline: none without providing a custom focus style. Test your app using only the keyboard — Tab, Shift+Tab, Enter, Space, Arrow keys.`,
    date: '2025-03-20', readTime: '5 min',
  },

  {
    id: 11, category: 'Career',
    title: 'Building a Portfolio That Gets You Hired',
    excerpt: 'Your portfolio is your best interview. Here is how to make one that stands out without being gimmicky.',
    body: `Three to five polished projects beat ten half-finished ones every time. Recruiters spend about 30 seconds on a portfolio — what you show must be immediately impressive.

Each project should have: a live demo link, a GitHub link, a short paragraph on the problem it solves, the tech stack, and one interesting challenge you solved. That last point is what interviewers follow up on.

Don't fill your portfolio with tutorial clones. A to-do app with your own twist, a personal dashboard for a real problem you have, or an open-source contribution all show more than a Udemy project.

The portfolio site itself should be clean and fast. A slow, over-animated portfolio signals you prioritise show over substance.`,
    date: '2025-01-15', readTime: '5 min',
  },
  {
    id: 12, category: 'Career',
    title: 'How to Prepare for a Technical Interview',
    excerpt: 'Coding interviews are a skill in themselves. Here is a structured approach to preparing without burning out.',
    body: `Phase 1 (weeks 1–2): Revise fundamentals. Arrays, strings, hash maps, and recursion cover about 70 % of interview questions. Solve 2–3 problems per day on LeetCode easy/medium.

Phase 2 (weeks 3–4): Learn key patterns. Sliding window, two pointers, BFS/DFS on graphs, binary search on answers, dynamic programming. You don't need every obscure algorithm — patterns matter more.

Phase 3 (1 week before): Mock interviews. Use Pramp or interviewing.io. Talking through your thinking out loud is a different skill from just solving the problem — practice it explicitly.

On the day: read the problem twice, clarify edge cases before coding, describe your approach first, then implement. It's fine to start with a brute force solution and optimise.`,
    date: '2025-02-01', readTime: '6 min',
  },
  {
    id: 13, category: 'Career',
    title: 'Remote Work: Staying Productive and Sane',
    excerpt: 'Remote work is great when you get it right. Boundaries, routines, and communication habits make or break the experience.',
    body: `The biggest remote work mistake is never leaving work mode. When your home is your office, work bleeds into evenings. A hard stop time, a dedicated workspace (even a specific chair), and a short end-of-day ritual all signal to your brain that the workday is over.

Communication overhead increases remotely. Write more, meet less. Document decisions in a shared doc immediately after a call. Async first means everyone's deep work isn't constantly interrupted.

Invest in your setup: a good chair, external monitor, and decent microphone make a measurable difference in productivity and how you're perceived in video calls.

Stay visible. Remote workers who are "out of sight, out of mind" miss promotions. Proactively share progress in stand-ups, Slack, or weekly updates.`,
    date: '2025-02-20', readTime: '5 min',
  },
  {
    id: 14, category: 'Career',
    title: 'The Art of Asking Good Questions',
    excerpt: 'Knowing when and how to ask for help is one of the most important — and underrated — skills in any software role.',
    body: `Asking too quickly makes you look lazy. Asking too late wastes hours you could have recovered in minutes. The sweet spot: try to solve the problem for 20–30 minutes, then ask.

A good question includes: what you're trying to do, what you've already tried, what result you expected, and what actually happened. Providing this context usually halves the time to an answer, and often you solve it yourself while writing it down (rubber duck debugging is real).

On platforms like Stack Overflow, a minimal reproducible example is required etiquette. Strip your code down to the smallest version that still shows the problem.

In a team context, choosing the right channel matters. A quick Slack message for a small question, a thread for a discussion, a meeting only when real-time back-and-forth is genuinely needed.`,
    date: '2025-03-05', readTime: '4 min',
  },
  {
    id: 15, category: 'Career',
    title: 'Understanding Your First Developer Job',
    excerpt: 'Your first six months on the job will teach you more than any course. Here is how to make the most of them.',
    body: `Onboarding is overwhelming for everyone. The codebase is large, the team dynamics are unclear, and everything feels unfamiliar. This is normal — give yourself three months before judging how you're doing.

Your job in the first 30 days is to listen, read, and ask questions. Understand what the team ships, why decisions were made the way they were (history matters), and who knows what.

Ship something small in the first two weeks, even if it's just a bug fix. Contributing early builds trust and gives you a real feel for the deployment process.

Find a mentor on the team — not necessarily your manager — someone willing to explain context without making you feel bad for not knowing it already.`,
    date: '2025-03-18', readTime: '5 min',
  },

  {
    id: 16, category: 'Tutorial',
    title: 'Build a Todo App with React Hooks',
    excerpt: 'A step-by-step guide to building a classic Todo app using useState and useEffect, with localStorage persistence.',
    body: `Step 1: Set up the project with Vite.\n\`\`\`\nnpx create-vite@latest todo-app --template react\n\`\`\`

Step 2: Create the state. We need a list of todos and an input value.
\`\`\`jsx\nconst [todos, setTodos] = useState([]);\nconst [input, setInput]  = useState('');\n\`\`\`

Step 3: Add, toggle, and delete functions. Each returns a new array — never mutate state directly.

Step 4: Persist to localStorage with useEffect.\n\`\`\`jsx\nuseEffect(() => {\n  localStorage.setItem('todos', JSON.stringify(todos));\n}, [todos]);\n\`\`\`

Step 5: Style with plain CSS. Keep it minimal — what matters here is the logic.

The finished app demonstrates all three core Hooks concepts: state, effects, and derived state (filtered lists).`,
    date: '2025-01-28', readTime: '8 min',
  },
  {
    id: 17, category: 'Tutorial',
    title: 'Fetching Data with useEffect and fetch()',
    excerpt: 'A guide to loading remote data in React: the fetch-in-useEffect pattern, loading states, error handling, and cleanup.',
    body: `The basic pattern looks like this:
\`\`\`jsx\nuseEffect(() => {\n  setLoading(true);\n  fetch('/api/posts')\n    .then(r => r.json())\n    .then(data => { setPosts(data); setLoading(false); })\n    .catch(err => { setError(err.message); setLoading(false); });\n}, []);\n\`\`\`

The empty dependency array means the effect runs once on mount — equivalent to componentDidMount in class components.

Cleanup matters when the component unmounts before the fetch completes. Use an AbortController:
\`\`\`jsx\nconst controller = new AbortController();\nfetch(url, { signal: controller.signal });\nreturn () => controller.abort();\n\`\`\`

For real projects, consider React Query or SWR which handle caching, deduplication, and background refetching for you.`,
    date: '2025-02-10', readTime: '7 min',
  },
  {
    id: 18, category: 'Tutorial',
    title: 'React Router v6 in 10 Minutes',
    excerpt: 'A fast, practical guide to React Router v6: BrowserRouter, Routes, Route, Link, useParams, and useNavigate.',
    body: `Install React Router:\n\`\`\`\nnpm install react-router-dom\n\`\`\`

Wrap your app in BrowserRouter (usually in main.jsx). Then define routes:
\`\`\`jsx\n<Routes>\n  <Route path="/" element={<Home />} />\n  <Route path="/posts/:id" element={<PostView />} />\n  <Route path="*" element={<NotFound />} />\n</Routes>\n\`\`\`

Read route params in a child component:
\`\`\`jsx\nconst { id } = useParams();\n\`\`\`

Navigate programmatically:
\`\`\`jsx\nconst navigate = useNavigate();\nnavigate('/posts/42');\n\`\`\`

Nested routes let you share layout. Wrap child routes under a parent and use <Outlet /> where you want the child to render.`,
    date: '2025-02-28', readTime: '6 min',
  },
  {
    id: 19, category: 'Tutorial',
    title: 'Building a REST API with Express',
    excerpt: 'Create a simple REST API with Node.js and Express: routing, middleware, JSON responses, and error handling.',
    body: `Install Express:\n\`\`\`\nnpm install express\n\`\`\`

A minimal server:
\`\`\`js\nconst express = require('express');\nconst app = express();\napp.use(express.json());\n\napp.get('/api/posts', (req, res) => {\n  res.json(posts);\n});\n\napp.listen(3000);\n\`\`\`

Route parameters: /api/posts/:id — accessed via req.params.id.
Query strings: /api/posts?page=2 — accessed via req.query.page.

Middleware runs before route handlers. Use it for logging, authentication, and parsing. Express has built-in JSON parsing (express.json()) and static file serving (express.static()).`,
    date: '2025-03-08', readTime: '7 min',
  },
  {
    id: 20, category: 'Tutorial',
    title: 'Git Workflow for Solo and Team Projects',
    excerpt: 'A practical Git workflow covering branches, commits, pull requests, and rebasing that works for both solo devs and teams.',
    body: `For solo projects, a simple two-branch setup works well: main (always deployable) and a feature or dev branch where work happens.

Commit messages should be short and imperative: "Add pagination to blog list", not "added some stuff to blog". The subject line should complete: "If applied, this commit will ___."

For teams, feature branches are standard. One branch per feature or bug fix. When ready, open a Pull Request. The PR is a review checkpoint — never merge directly to main without at least one review on a team.

Rebase vs merge: rebase keeps history linear and clean, merge preserves the exact sequence of events. On feature branches, rebase onto main frequently to minimize conflicts. Always merge (don't rebase) onto shared branches like main or develop.`,
    date: '2025-03-22', readTime: '6 min',
  },
];

export const CATEGORIES = ['All', ...new Set(POSTS.map(p => p.category))];
export const POSTS_PER_PAGE = 6;
export default POSTS;
