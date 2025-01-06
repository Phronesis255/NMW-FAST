import React, { useEffect, useRef } from 'react';
import EditorJS from '@editorjs/editorjs';
import { markdownToEditorJsBlocks } from '../utils/markdownToEditorJsBlocks';

const SimpleEditorComponent = ({ initialContent }) => {
    const editorInstance = useRef(null);

    useEffect(() => {
        const blocks = markdownToEditorJsBlocks(initialContent);

        editorInstance.current = new EditorJS({
            holder: 'editorjs',
            data: {
                blocks: blocks.length ? blocks : [
                    {
                        type: 'paragraph',
                        data: {
                            text: 'Start writing your article here...'
                        }
                    }
                ]
            }
        });

        return () => {
            editorInstance.current.destroy();
        };
    }, [initialContent]);

    return <div id="editorjs" className="border p-4"></div>;
};

export default SimpleEditorComponent;