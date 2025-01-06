import React, { useEffect, useRef } from 'react';
import EditorJS from '@editorjs/editorjs';

const SimpleEditorComponent = ({ initialContent }) => {
    const editorInstance = useRef(null);

    useEffect(() => {
        editorInstance.current = new EditorJS({
            holder: 'editorjs',
            data: {
                blocks: [
                    {
                        type: 'paragraph',
                        data: {
                            text: initialContent || 'Start writing your article here...'
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