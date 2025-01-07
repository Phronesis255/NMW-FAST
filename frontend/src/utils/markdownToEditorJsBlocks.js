import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkRehype from 'remark-rehype';

/**
 * Convert markdown content into Editor.js blocks without using rehype-react.
 */
export const markdownToEditorJsBlocks = (markdownContent) => {
  // Step 1: Parse the Markdown => remark AST
  const remarkAST = unified()
    .use(remarkParse)
    .parse(markdownContent);

  // Step 2: Convert remark AST => rehype AST
  const rehypeAST = unified()
    .use(remarkRehype)
    .runSync(remarkAST);

  // Step 3: Traverse the rehype AST to build an array of Editor.js blocks
  const blocks = [];

  function parseNode(node) {
    if (node.type === 'element') {
      const { tagName, children } = node;

      // HEADERS
      if (['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(tagName)) {
        const level = Number(tagName.replace('h', ''));
        const text = getTextContent(children);
        blocks.push({
          type: 'header',
          data: {
            text,
            level,
          },
        });
      }

      // PARAGRAPHS
      else if (tagName === 'p') {
        const text = getTextContent(children);
        blocks.push({
          type: 'paragraph',
          data: { text },
        });
      }

      // UNORDERED LISTS
      else if (tagName === 'ul') {
        const items = children
          ?.filter((item) => item.type === 'element' && item.tagName === 'li')
          .map((li) => getTextContent(li.children));
        blocks.push({
          type: 'list',
          data: {
            style: 'unordered',
            items,
          },
        });
      }

      // ORDERED LISTS
      else if (tagName === 'ol') {
        const items = children
          ?.filter((item) => item.type === 'element' && item.tagName === 'li')
          .map((li) => getTextContent(li.children));
        blocks.push({
          type: 'list',
          data: {
            style: 'ordered',
            items,
          },
        });
      }

      // RECURSE for nested tags
      else if (children && Array.isArray(children)) {
        children.forEach(parseNode);
      }
    }
    else if (node.type === 'text') {
      // Plain text nodes that are not wrapped in a paragraph or heading can be handled here.
      // Usually they'll appear inside paragraphs, headings, etc.
    }
  }

  // Traverse top-level nodes
  if (rehypeAST.children) {
    rehypeAST.children.forEach(parseNode);
  }

  return blocks;
};

// Helper function to get plain text from an array of rehype child nodes
function getTextContent(children = []) {
  return children
    .map((child) => {
      if (child.type === 'text') return child.value;
      if (child.type === 'element' && child.children) {
        return getTextContent(child.children);
      }
      return '';
    })
    .join('');
}
