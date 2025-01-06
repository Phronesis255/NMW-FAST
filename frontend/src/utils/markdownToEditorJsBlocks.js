import markdownToJsx from 'markdown-to-jsx';

export const markdownToEditorJsBlocks = (markdown) => {
    const jsx = markdownToJsx(markdown);
    const blocks = [];

    const parseElement = (element) => {
        if (typeof element === 'string') {
            blocks.push({
                type: 'paragraph',
                data: {
                    text: element
                }
            });
        } else if (element.type === 'h1') {
            blocks.push({
                type: 'header',
                data: {
                    text: element.props.children,
                    level: 1
                }
            });
        } else if (element.type === 'h2') {
            blocks.push({
                type: 'header',
                data: {
                    text: element.props.children,
                    level: 2
                }
            });
        } else if (element.type === 'h3') {
            blocks.push({
                type: 'header',
                data: {
                    text: element.props.children,
                    level: 3
                }
            });
        } else if (Array.isArray(element.props.children)) {
            element.props.children.forEach(parseElement);
        } else {
            parseElement(element.props.children);
        }
    };

    parseElement(jsx);

    return blocks;
};