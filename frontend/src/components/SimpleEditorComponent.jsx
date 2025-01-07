import React, { useEffect, useRef, useState } from 'react';
import EditorJS from '@editorjs/editorjs';
import Header from '@editorjs/header';
import Paragraph from '@editorjs/paragraph';
import List from '@editorjs/list';
import { markdownToEditorJsBlocks } from '../utils/markdownToEditorJsBlocks';

const SimpleEditorComponent = ({ initialContent, onChange }) => {
  const editorRef = useRef(null); // Will store the EditorJS instance
  const [editorContent, setEditorContent] = useState(initialContent || '');

  /**
   * 1) Initialize EditorJS once on component mount
   */
  useEffect(() => {
    // Convert Markdown -> Editor.js blocks on first load
    const blocks = markdownToEditorJsBlocks(initialContent || '');

    // If we already have an EditorJS instance, do nothing
    if (editorRef.current) return;

    // Create the EditorJS instance
    editorRef.current = new EditorJS({
      holder: 'editorjs', // Must match the div's ID below
      autofocus: true,
      placeholder: 'Start typing your content here...',
      tools: {
        header: {
          class: Header,
          inlineToolbar: ['bold', 'italic', 'link'],
          config: {
            placeholder: 'Enter a heading',
            levels: [1, 2, 3, 4],
            defaultLevel: 1,
          },
        },
        paragraph: {
          class: Paragraph,
          inlineToolbar: ['bold', 'italic', 'link'],
          config: {
            placeholder: 'Start typing here...',
          },
        },
        list: {
          class: List,
          inlineToolbar: ['bold', 'italic', 'link'],
          config: {
            defaultStyle: 'unordered',
          },
        },
      },
      data: {
        time: new Date().getTime(),
        blocks: blocks.length
          ? blocks
          : [
              {
                type: 'paragraph',
                data: { text: '' },
              },
            ],
      },
      onChange: async () => {
        try {
          const outputData = await editorRef.current.save();
          // Convert blocks array to a plain string for local state
          const textContent = outputData.blocks
            .map((block) => block.data.text || '')
            .join(' ');

          setEditorContent(textContent);
        } catch (error) {
          console.error('Error saving Editor.js data:', error);
        }
      },
    });

    // Cleanup on unmount
    return () => {
      if (editorRef.current && typeof editorRef.current.destroy === 'function') {
        editorRef.current.destroy();
        editorRef.current = null;
      }
    };
  }, [initialContent]);

  /**
   * 2) (Optional) Listen for changes in `initialContent`
   *    and re-render the editor data (Editor.js 2.26+).
   *    If you don’t need to “reload” blocks on each prop change,
   *    you can remove this effect.
   */
  useEffect(() => {
    if (!editorRef.current) return; // Editor not initialized yet

    // If Editor.js version is <2.26, .render() won't exist
    if (typeof editorRef.current.render === 'function') {
      const blocks = markdownToEditorJsBlocks(initialContent || '');
      editorRef.current.render({
        time: new Date().getTime(),
        blocks: blocks.length
          ? blocks
          : [
              {
                type: 'paragraph',
                data: { text: '' },
              },
            ],
      });
    }
  }, [initialContent]);

  /**
   * 3) Notify parent about text changes
   */
  useEffect(() => {
    if (onChange) {
      onChange(editorContent);
    }
  }, [editorContent, onChange]);

  return (
    <div className="w-full flex flex-col gap-6">
      {/* EditorJS container. Must have id="editorjs" for EditorJS holder */}
      <div
        id="editorjs"
        className="border rounded-lg p-4 bg-white shadow-md"
        style={{
          minHeight: '400px',
          maxHeight: '600px',
          overflowY: 'auto',
          width: '100%',
        }}
      >
        <style>
          {`
            .ce-block__content h1 {
              font-size: 1.5em;
              font-weight: bold;
              margin-bottom: 0.5em;
            }
            .ce-block__content h2 {
              font-size: 1.4em;
              font-weight: bold;
              margin-bottom: 0.5em;
            }
            .ce-block__content h3 {
              font-size: 1.3em;
              font-weight: bold;
              margin-bottom: 0.5em;
            }
            .ce-block__content h4 {
              font-size: 1.2em;
              font-weight: bold;
              margin-bottom: 0.5em;
            }
          `}
        </style>
      </div>
    </div>
  );
};

export default SimpleEditorComponent;
