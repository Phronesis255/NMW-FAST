import React, { useState } from 'react';
import axios from 'axios';
import SimpleEditorComponent from './SimpleEditorComponent';

const GenerateArticle = ({ onBack }) => {
    const [keyword, setKeyword] = useState('');
    const [title, setTitle] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [editorContent, setEditorContent] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setSuccess(null);

        try {
            const response = await axios.post('http://localhost:8000/api/generate-article', { keyword, title });
            setSuccess(response.data.message);
            setEditorContent(response.data.content);
        } catch (err) {
            setError(err.message || "An error occurred during article generation.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6">
            <h2 className="text-3xl font-bold mb-4">Generate a New Article</h2>
            {!editorContent ? (
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium">Keyword</label>
                        <input
                            type="text"
                            value={keyword}
                            onChange={(e) => setKeyword(e.target.value)}
                            className="input input-bordered w-full"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium">Title</label>
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            className="input input-bordered w-full"
                            required
                        />
                    </div>
                    <button type="submit" className="btn btn-primary" disabled={loading}>
                        {loading ? 'Generating...' : 'Submit'}
                    </button>
                    {error && <div className="text-red-500 mt-2">{error}</div>}
                    {success && <div className="text-green-500 mt-2">{success}</div>}
                </form>
            ) : (
                <SimpleEditorComponent initialContent={editorContent} />
            )}
            <button className="btn btn-secondary mt-4" onClick={onBack}>
                Back
            </button>
        </div>
    );
};

export default GenerateArticle;